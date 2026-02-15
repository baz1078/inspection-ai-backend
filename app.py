from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from models import db, InspectionReport, Conversation, Question, Contractor, Lead, Analytics, WarrantyDocument, ReportWarranty, WarrantyQuery
from utils import (
    extract_text_from_pdf,
    generate_summary_from_report,
    InspectionReportQA,
    save_uploaded_file,
    generate_punchlist,
    send_contractor_email
)
from warranty_utils import (
    extract_warranty_text,
    parse_warranty_coverage,
    WarrantyCoverageQA
)
import uuid
import os
from datetime import datetime
import re
import json
from collections import OrderedDict

# Initialize Flask app
#app = Flask(__name__)
app = Flask(__name__, static_folder='.', static_url_path='')

@app.route('/')
def index():
    with open('index.html', 'r', encoding='utf-8') as f:
        return f.read()
# Database config
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///inspection_reports.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 5,
    'pool_recycle': 300,
    'pool_pre_ping': True,
}

# Email config
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@assureinspections.com')

# Initialize database
db.init_app(app)
CORS(app)

# Create upload folder
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# In-memory cache for conversations (10 reports max)
REPORT_CACHE = OrderedDict()
MAX_CACHE_SIZE = 10

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def extract_issue_type(question: str) -> str:
    """Extract issue type from question"""
    keywords = {
        'electrical': ['electrical', 'electric', 'outlet', 'wire', 'breaker', 'amperage', 'power', 'panel', 'gfci', 'wiring', 'light', 'switch', 'socket'],
        'roofing': ['roof', 'shingles', 'shingle', 'leak', 'gutter', 'chimney', 'flashing', 'slope', 'top layer'],
        'plumbing': ['plumb', 'drain', 'water', 'pipe', 'faucet', 'leak', 'sewer', 'toilet', 'sink', 'shower', 'bath', 'tub', 'trap', 'line'],
        'hvac': ['hvac', 'heating', 'cooling', 'furnace', 'ac', 'boiler', 'thermostat', 'duct', 'heat', 'cool', 'air', 'heater', 'conditioner'],
        'structural': ['foundation', 'crack', 'structural', 'settle', 'beam', 'wall', 'joist', 'support', 'basement', 'floor', 'post'],
        'siding': ['siding', 'exterior', 'cladding', 'fascia', 'trim', 'deck', 'clapboard', 'vinyl', 'metal'],
        'mold': ['mold', 'mildew', 'moisture', 'fungal', 'wet', 'damp', 'water damage'],
        'radon': ['radon', 'gas', 'testing', 'test'],
        'pest': ['pest', 'termite', 'insect', 'rodent', 'bug', 'ant', 'mouse', 'rat', 'infestation'],
        'general': ['contractor', 'repair', 'fix', 'issue', 'problem'],
    }
    
    q_lower = question.lower()
    for issue_type, keywords_list in keywords.items():
        if any(kw in q_lower for kw in keywords_list):
            return issue_type
    return 'general'

def get_zip_from_address(address: str) -> str:
    """Extract zip code from address"""
    match = re.search(r'\b\d{5}\b', address)
    return match.group(0) if match else None

def get_matching_contractors(issue_type: str, zip_code: str = None):
    """Get contractors matching issue type and optionally zip code"""
    contractors = Contractor.query.filter_by(
        specialty=issue_type,
        isActive=True
    ).order_by(Contractor.rating.desc()).limit(3).all()
    
    if zip_code and contractors:
        matching = []
        for c in contractors:
            if c.zipCodes and zip_code in c.zipCodes:
                matching.append(c)
        return matching if matching else contractors[:3]
    
    return contractors

# ============================================================================
# CORE ENDPOINTS
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'Assure Inspections AI',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@app.route('/api/upload', methods=['POST'])
def upload_report():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Save file
        filepath = save_uploaded_file(file, app.config['UPLOAD_FOLDER'])
        
        # Extract text
        print("Extracting text from PDF...")
        extractedText = extract_text_from_pdf(filepath)
        
        # Generate summary
        print("Generating AI summary...")
        summary = generate_summary_from_report(extractedText)
        
        # Create database record
        report = InspectionReport(
            address=request.form.get('address', 'Unknown Address'),
            customerName=request.form.get('customer_name', 'Unknown'),
            customerEmail=request.form.get('customer_email', ''),
            customerPhone=request.form.get('customer_phone', ''),
            inspectorName=request.form.get('inspector_name', 'Inspector'),
            inspectionDate=datetime.utcnow(),
            reportType=request.form.get('report_type', 'home_inspection'),
            originalFilename=secure_filename(file.filename),
            filePath=filepath,
            fileSize=os.path.getsize(filepath),
            extractedText=extractedText,
            summary=summary,
            isShared=True,
            shareToken=str(uuid.uuid4())[:8] 
        )
        
        db.session.add(report)
        db.session.commit()
        
        # Cache the conversation
        qa_system = InspectionReportQA(extractedText)
        REPORT_CACHE[report.id] = qa_system
        if len(REPORT_CACHE) > MAX_CACHE_SIZE:
            REPORT_CACHE.popitem(last=False)
        
        return jsonify({
            'success': True,
            'report_id': report.id,
            'shareToken': report.shareToken,
            'summary': summary,
            'address': report.address,
            'message': 'Report uploaded successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/ask/<report_id>', methods=['POST'])
def ask_question(report_id):
    try:
        data = request.get_json()
        if not data or 'question' not in data:
            return jsonify({'error': 'No question provided'}), 400
        
        question = data['question'].strip()
        if not question:
            return jsonify({'error': 'Question cannot be empty'}), 400
        
        # Get report
        report = InspectionReport.query.get(report_id)
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        # Check if warranty is linked to this report
        warranty_id = data.get('warranty_id')
        warranty_context = ""
        
        if warranty_id:
            warranty = WarrantyDocument.query.get(warranty_id)
            if warranty:
                warranty_context = f"\n\nWARRANTY COVERAGE INFORMATION:\n{warranty.coverageRules}"
        
        # Get or create QA system from cache
        if report_id in REPORT_CACHE:
            qa_system = REPORT_CACHE[report_id]
        else:
            qa_system = InspectionReportQA(report.extractedText)
            REPORT_CACHE[report_id] = qa_system
            if len(REPORT_CACHE) > MAX_CACHE_SIZE:
                REPORT_CACHE.popitem(last=False)
        
        # Get answer - pass warranty context as part of question if present
        print(f"Processing question for report {report_id}...")
        if warranty_context:
            # Prepend warranty context to the question for Claude
            question_with_context = f"{warranty_context}\n\nCustomer question: {question}"
            answer = qa_system.answer_question(question_with_context)
        else:
            answer = qa_system.answer_question(question)
        
        # Extract issue type
        issue_type = extract_issue_type(question)
        
        # Create question record
        db_question = Question(
            reportId=report.id,
            question=question,
            issueType=issue_type,
            answer=answer
        )
        db.session.add(db_question)
        db.session.commit()
        
        # Get matching contractors (only if not a warranty question)
        referrals = []
        is_warranty_question = any(word in question.lower() for word in ['warranty', 'covered', 'coverage', 'claim'])
        
        if not is_warranty_question:
            zip_code = get_zip_from_address(report.address)
            contractors = get_matching_contractors(issue_type, zip_code)
            
            # Format contractor referrals
            for c in contractors:
                referrals.append({
                    'id': c.id,
                    'name': c.name,
                    'specialty': c.specialty,
                    'phone': c.phone,
                    'email': c.email,
                    'rating': c.rating,
                    'review_count': c.reviewCount,
                    'description': c.description,
                    'website': c.website
                })
        
        return jsonify({
            'success': True,
            'conversation_id': db_question.id,
            'answer': answer,
            'issue_type': issue_type,
            'referrals': referrals
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/contractors', methods=['GET'])
def get_contractors():
    try:
        contractors = Contractor.query.filter_by(isActive=True).all()
        
        return jsonify({
            'total': len(contractors),
            'contractors': [
                {
                    'id': c.id,
                    'name': c.name,
                    'specialty': c.specialty,
                    'phone': c.phone,
                    'email': c.email,
                    'city': c.city,
                    'state': c.state,
                    'rating': c.rating,
                    'review_count': c.reviewCount,
                    'is_licensed': c.isLicensed,
                    'is_bonded': c.isBonded,
                    'is_insured': c.isInsured
                }
                for c in contractors
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/leads', methods=['GET'])
def get_leads():
    try:
        leads = Lead.query.all()
        
        return jsonify({
            'total': len(leads),
            'leads': [
                {
                    'id': l.id,
                    'report_id': l.reportId,
                    'contractorName': l.contractor.name,
                    'issue_type': l.question.issueType,
                    'status': l.status,
                    'created_at': l.createdAt.isoformat()
                }
                for l in leads
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/leads/<lead_id>', methods=['PUT'])
def update_lead(lead_id):
    try:
        lead = Lead.query.get(lead_id)
        if not lead:
            return jsonify({'error': 'Lead not found'}), 404
        
        data = request.get_json()
        if 'status' in data:
            lead.status = data['status']
        if 'notes' in data:
            lead.notes = data['notes']
        
        db.session.commit()
        
        return jsonify({'success': True, 'lead_id': lead.id}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/referral-request', methods=['POST'])
def create_referral_request():
    """Customer requests quote from contractor - generates punchlist and sends email"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required = ['report_id', 'question_id', 'contractor_id', 'customer_name', 'customer_email', 'customer_phone']
        if not all(k in data for k in required):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Get report and question for context
        report = InspectionReport.query.get(data['report_id'])
        question = Question.query.get(data['question_id'])
        contractor = Contractor.query.get(data['contractor_id'])
        
        if not (report and question and contractor):
            return jsonify({'error': 'Report, question, or contractor not found'}), 404
        
        # UPDATE report with customer info if provided
        report.customerName = data.get('customer_name')
        report.customerEmail = data.get('customer_email')
        report.customerPhone = data.get('customer_phone')
        
        # GENERATE PUNCHLIST
        print(f"Generating punchlist for {question.issueType}...")
        punchlist = generate_punchlist(
            question.answer,
            question.issueType,
            question.question
        )
        
        # CREATE LEAD with punchlist in notes
        lead = Lead(
            reportId=data['report_id'],
            questionId=data['question_id'],
            contractorId=data['contractor_id'],
            status='pending',
            notes=punchlist
        )
        
        db.session.add(lead)
        db.session.commit()
        
        # SEND EMAIL to contractor with punchlist
        if contractor.email:
            try:
                send_contractor_email(
                    contractor_email=contractor.email,
                    contractor_name=contractor.name,
                    customer_name=data.get('customer_name'),
                    customer_email=data.get('customer_email'),
                    customer_phone=data.get('customer_phone'),
                    property_address=report.address,
                    issue_type=question.issueType,
                    punchlist=punchlist
                )
                print(f"Email sent to contractor: {contractor.email}")
            except Exception as e:
                print(f"Warning: Failed to send email to contractor: {str(e)}")
        
        return jsonify({
            'success': True,
            'lead_id': lead.id,
            'message': 'Quote request sent to contractor'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Error creating referral request: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# ANALYTICS & DASHBOARD
# ============================================================================

@app.route('/api/admin/analytics/questions', methods=['GET'])
def get_question_analytics():
    try:
        questions = Question.query.all()
        
        issue_type_count = {}
        for q in questions:
            issue_type_count[q.issueType] = issue_type_count.get(q.issueType, 0) + 1
        
        return jsonify({
            'total_questions': len(questions),
            'by_issue_type': issue_type_count
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/analytics/contractors', methods=['GET'])
def get_contractor_analytics():
    try:
        contractors = Contractor.query.all()
        
        contractor_stats = []
        for c in contractors:
            lead_count = len(c.leads)
            converted = len([l for l in c.leads if l.status == "converted"])
            
            contractor_stats.append({
                'id': c.id,
                'name': c.name,
                'specialty': c.specialty,
                'total_leads': lead_count,
                'converted_leads': converted,
                'conversion_rate': (converted / lead_count * 100) if lead_count > 0 else 0,
                'rating': c.rating
            })
        
        return jsonify({'contractors': contractor_stats}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    try:
        total_reports = InspectionReport.query.count()
        total_questions = Question.query.count()
        total_leads = Lead.query.count()
        total_contractors = Contractor.query.count()
        
        questions = Question.query.all()
        leads = Lead.query.all()
        
        issue_type_count = {}
        for q in questions:
            issue_type_count[q.issueType] = issue_type_count.get(q.issueType, 0) + 1
        
        by_status = {}
        for l in leads:
            by_status[l.status] = by_status.get(l.status, 0) + 1
        
        return jsonify({
            'total_reports': total_reports,
            'total_questions': total_questions,
            'total_leads': total_leads,
            'total_contractors': total_contractors,
            'questions_by_issue_type': issue_type_count,
            'leads_by_status': by_status
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# WARRANTY ENDPOINTS
# ============================================================================

@app.route('/api/upload-warranty/<report_id>', methods=['POST'])
def upload_warranty(report_id):
    """Upload warranty document for an inspection report"""
    try:
        report = InspectionReport.query.get(report_id)
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        builder_name = request.form.get('builder_name', 'Unknown Builder')
        warranty_type = request.form.get('warranty_type', 'Standard')
        jurisdiction = request.form.get('jurisdiction', 'USA')
        
        # Save file
        print(f"[WARRANTY] Saving warranty file...")
        filepath = save_uploaded_file(file, app.config['UPLOAD_FOLDER'])
        
        # Extract warranty text
        print(f"[WARRANTY] Extracting text from PDF...")
        warranty_text = extract_warranty_text(filepath)
        print(f"[WARRANTY] Extracted {len(warranty_text)} characters")
        
        # Parse warranty coverage (returns plain text summary, not JSON)
        print(f"[WARRANTY] Parsing warranty coverage summary...")
        coverage_summary = parse_warranty_coverage(warranty_text, builder_name, warranty_type)
        print(f"[WARRANTY] Coverage summary created: {len(coverage_summary)} characters")
        
        # Create WarrantyDocument record
        warranty_doc = WarrantyDocument(
            builderName=builder_name,
            warrantyType=warranty_type,
            jurisdiction=jurisdiction,
            filePath=filepath,
            originalFilename=secure_filename(file.filename),
            fileSize=os.path.getsize(filepath),
            extractedText=warranty_text[:5000],  # Store first 5000 chars
            coverageRules=coverage_summary,  # Plain text summary, not JSON
            isActive=True
        )
        
        db.session.add(warranty_doc)
        db.session.commit()
        
        # Link warranty to report
        report_warranty = ReportWarranty(
            reportId=report_id,
            warrantyId=warranty_doc.id,
            warrantyStartDate=datetime.utcnow()
        )
        
        db.session.add(report_warranty)
        db.session.commit()
        
        print(f"[WARRANTY] Successfully saved warranty for {builder_name}")
        return jsonify({
            'success': True,
            'warranty_id': warranty_doc.id,
            'builder_name': builder_name,
            'warranty_type': warranty_type,
            'message': f'{builder_name} warranty uploaded successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"[WARRANTY] Error uploading warranty: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Warranty endpoints removed - functionality moved to unified /api/ask endpoint

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request'}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500

# ============================================================================
# INITIALIZATION
# ============================================================================

with app.app_context():
    db.create_all()
    print("Database tables verified/created")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)