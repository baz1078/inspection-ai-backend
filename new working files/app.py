from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from models import db, InspectionReport, Conversation, Question, Contractor, Lead, Analytics
from utils import (
    extract_text_from_pdf,
    generate_summary_from_report,
    InspectionReportQA,
    save_uploaded_file,
    generate_punchlist,
    send_contractor_email
)
import os
from datetime import datetime
import re
from collections import OrderedDict

# Initialize Flask app
app = Flask(__name__)

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
        'electrical': ['electrical', 'outlet', 'wire', 'breaker', 'amperage', 'power', 'panel', 'gfci', 'wiring'],
        'roofing': ['roof', 'shingles', 'leak', 'gutter', 'chimney', 'flashing'],
        'plumbing': ['plumb', 'drain', 'water line', 'trap', 'pipe', 'faucet', 'leak', 'sewer'],
        'hvac': ['hvac', 'heating', 'cooling', 'furnace', 'ac', 'boiler', 'thermostat', 'duct'],
        'structural': ['foundation', 'crack', 'structural', 'settle', 'beam', 'wall', 'joist'],
        'siding': ['siding', 'exterior', 'cladding', 'fascia', 'trim', 'deck'],
        'mold': ['mold', 'mildew', 'moisture', 'fungal'],
        'radon': ['radon', 'gas', 'testing'],
        'pest': ['pest', 'termite', 'insect', 'rodent'],
        'general': ['contractor', 'repair', 'fix'],
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
        is_active=True
    ).order_by(Contractor.rating.desc()).limit(3).all()
    
    if zip_code and contractors:
        matching = []
        for c in contractors:
            if c.zip_codes and zip_code in c.zip_codes:
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
        extracted_text = extract_text_from_pdf(filepath)
        
        # Generate summary
        print("Generating AI summary...")
        summary = generate_summary_from_report(extracted_text)
        
        # Create database record
        report = InspectionReport(
            address=request.form.get('address', 'Unknown Address'),
            customer_name=request.form.get('customer_name', 'Unknown'),
            customer_email=request.form.get('customer_email', ''),
            customer_phone=request.form.get('customer_phone', ''),
            inspector_name=request.form.get('inspector_name', 'Inspector'),
            inspection_date=datetime.utcnow(),
            report_type=request.form.get('report_type', 'home_inspection'),
            original_filename=secure_filename(file.filename),
            file_path=filepath,
            file_size=os.path.getsize(filepath),
            extracted_text=extracted_text,
            summary=summary,
            is_shared=True
        )
        
        db.session.add(report)
        db.session.commit()
        
        # Cache the conversation
        qa_system = InspectionReportQA(extracted_text)
        REPORT_CACHE[report.id] = qa_system
        if len(REPORT_CACHE) > MAX_CACHE_SIZE:
            REPORT_CACHE.popitem(last=False)
        
        return jsonify({
            'success': True,
            'report_id': report.id,
            'share_token': report.share_token,
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
        
        # Get or create QA system from cache
        if report_id in REPORT_CACHE:
            qa_system = REPORT_CACHE[report_id]
        else:
            qa_system = InspectionReportQA(report.extracted_text)
            REPORT_CACHE[report_id] = qa_system
            if len(REPORT_CACHE) > MAX_CACHE_SIZE:
                REPORT_CACHE.popitem(last=False)
        
        # Get answer
        print(f"Processing question for report {report_id}...")
        answer = qa_system.answer_question(question)
        
        # Extract issue type
        issue_type = extract_issue_type(question)
        
        # Create question record
        db_question = Question(
            report_id=report.id,
            question=question,
            issue_type=issue_type,
            answer=answer
        )
        db.session.add(db_question)
        db.session.commit()
        
        # Get matching contractors
        zip_code = get_zip_from_address(report.address)
        contractors = get_matching_contractors(issue_type, zip_code)
        
        # Format contractor referrals
        referrals = []
        for contractor in contractors:
            referrals.append({
                'id': contractor.id,
                'name': contractor.name,
                'specialty': contractor.specialty,
                'rating': contractor.rating,
                'review_count': contractor.review_count,
                'is_licensed': contractor.is_licensed,
                'is_bonded': contractor.is_bonded,
                'is_insured': contractor.is_insured,
                'phone': contractor.phone,
                'email': contractor.email,
                'city': contractor.city,
                'state': contractor.state
            })
        
        return jsonify({
            'success': True,
            'conversation_id': db_question.id,
            'question': question,
            'answer': answer,
            'issue_type': issue_type,
            'referrals': referrals,
            'timestamp': db_question.created_at.isoformat()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/conversations/<report_id>', methods=['GET'])
def get_conversations(report_id):
    try:
        report = InspectionReport.query.get(report_id)
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        questions = Question.query.filter_by(report_id=report_id).order_by(Question.created_at.asc()).all()
        
        return jsonify({
            'report_id': report_id,
            'total_questions': len(questions),
            'conversations': [
                {
                    'id': q.id,
                    'question': q.question,
                    'answer': q.answer,
                    'issue_type': q.issue_type,
                    'timestamp': q.created_at.isoformat()
                }
                for q in questions
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/shared/<share_token>', methods=['GET'])
def get_shared_report(share_token):
    try:
        report = InspectionReport.query.filter_by(
            share_token=share_token,
            is_shared=True
        ).first()
        
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        return jsonify({
            'id': report.id,
            'address': report.address,
            'summary': report.summary,
            'report_type': report.report_type,
            'inspection_date': report.inspection_date.isoformat(),
            'share_token': share_token
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# CONTRACTOR MANAGEMENT
# ============================================================================

@app.route('/api/admin/contractors', methods=['GET'])
def list_contractors():
    try:
        contractors = Contractor.query.order_by(Contractor.created_at.desc()).all()
        
        return jsonify({
            'total_contractors': len(contractors),
            'contractors': [
                {
                    'id': c.id,
                    'name': c.name,
                    'specialty': c.specialty,
                    'city': c.city,
                    'state': c.state,
                    'rating': c.rating,
                    'phone': c.phone,
                    'email': c.email,
                    'is_active': c.is_active
                }
                for c in contractors
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/contractors', methods=['POST'])
def create_contractor():
    try:
        data = request.get_json()
        
        contractor = Contractor(
            name=data['name'],
            specialty=data['specialty'],
            phone=data['phone'],
            email=data['email'],
            zip_codes=data.get('zip_codes', ''),
            city=data.get('city', ''),
            state=data.get('state', ''),
            rating=float(data.get('rating', 0.0)),
            description=data.get('description', ''),
            is_licensed=data.get('is_licensed', True),
            is_bonded=data.get('is_bonded', True),
            is_insured=data.get('is_insured', True),
            cost_per_lead=float(data.get('cost_per_lead', 25.0))
        )
        
        db.session.add(contractor)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'contractor_id': contractor.id,
            'message': 'Contractor created'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/contractors/<contractor_id>', methods=['PUT'])
def update_contractor(contractor_id):
    try:
        contractor = Contractor.query.get(contractor_id)
        if not contractor:
            return jsonify({'error': 'Contractor not found'}), 404
        
        data = request.get_json()
        for key, value in data.items():
            if hasattr(contractor, key) and value is not None:
                setattr(contractor, key, value)
        
        db.session.commit()
        
        return jsonify({'success': True, 'contractor_id': contractor.id}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/contractors/<contractor_id>', methods=['DELETE'])
def delete_contractor(contractor_id):
    try:
        contractor = Contractor.query.get(contractor_id)
        if not contractor:
            return jsonify({'error': 'Contractor not found'}), 404
        
        db.session.delete(contractor)
        db.session.commit()
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ============================================================================
# LEADS & REFERRALS
# ============================================================================

@app.route('/api/admin/leads', methods=['GET'])
def list_leads():
    try:
        leads = Lead.query.order_by(Lead.created_at.desc()).all()
        
        return jsonify({
            'total_leads': len(leads),
            'leads': [
                {
                    'id': l.id,
                    'customer_name': l.customer_name or 'N/A',
                    'customer_email': l.customer_email or 'N/A',
                    'customer_phone': l.customer_phone or 'N/A',
                    'contractor_name': l.contractor.name,
                    'issue_type': l.question.issue_type,
                    'status': l.status,
                    'created_at': l.created_at.isoformat()
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
        report.customer_name = data.get('customer_name')
        report.customer_email = data.get('customer_email')
        report.customer_phone = data.get('customer_phone')
        
        # GENERATE PUNCHLIST: Create filtered issue list for this contractor specialty
        print(f"Generating punchlist for {question.issue_type}...")
        punchlist = generate_punchlist(
            report.extracted_text,
            question.issue_type,
            question.question
        )
        
        # CREATE LEAD with punchlist in notes
        lead = Lead(
            report_id=data['report_id'],
            question_id=data['question_id'],
            contractor_id=data['contractor_id'],
            customer_name=data.get('customer_name', ''),
            customer_email=data.get('customer_email', ''),
            customer_phone=data.get('customer_phone', ''),
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
                    issue_type=question.issue_type,
                    punchlist=punchlist
                )
                print(f"Email sent to contractor: {contractor.email}")
            except Exception as e:
                print(f"Warning: Failed to send email to contractor: {str(e)}")
                # Don't fail the request if email fails - lead is still created
        
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
            issue_type_count[q.issue_type] = issue_type_count.get(q.issue_type, 0) + 1
        
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
            issue_type_count[q.issue_type] = issue_type_count.get(q.issue_type, 0) + 1
        
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
