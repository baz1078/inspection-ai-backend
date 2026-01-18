from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from config import config
from models import db, InspectionReport, Conversation
from utils import (
    extract_text_from_pdf,
    generate_summary_from_report,
    InspectionReportQA,
    save_uploaded_file
)
import os
from datetime import datetime
from collections import OrderedDict

# Initialize Flask app
app = Flask(__name__)

# Load config
config_name = os.getenv('FLASK_ENV', 'development')
app.config.from_object(config[config_name])

# Initialize database
db.init_app(app)

# Enable CORS
CORS(app)

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# In-memory cache for report conversations (limit to 10)
REPORT_CACHE = OrderedDict()
MAX_CACHE_SIZE = 10

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request', 'message': str(error)}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error', 'message': str(error)}), 500


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Inspection AI Backend',
        'timestamp': datetime.utcnow().isoformat(),
        'cache_size': len(REPORT_CACHE)
    }), 200


@app.route('/api/upload', methods=['POST'])
def upload_report():
    """
    Upload a PDF inspection report
    
    Expected multipart form data:
    - file: PDF file
    - address: property address (optional)
    - inspector_name: inspector name (optional)
    - inspection_date: date of inspection (optional)
    - report_type: type of report (home_inspection, mold, radon, sewer, etc.)
    """
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Save file
        filepath = save_uploaded_file(file, app.config['UPLOAD_FOLDER'])
        
        # Extract text from PDF
        print(f"Extracting text from {filepath}...")
        extracted_text = extract_text_from_pdf(filepath)
        
        # Generate AI summary
        print("Generating AI summary...")
        summary = generate_summary_from_report(extracted_text)
        
        # Create database record
        report = InspectionReport(
            address=request.form.get('address', 'Unknown Address'),
            inspector_name=request.form.get('inspector_name', 'Unknown'),
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
        
        # Cache the conversation object immediately after upload
        print(f"Caching report {report.id}")
        qa_system = InspectionReportQA(extracted_text)
        REPORT_CACHE[report.id] = qa_system
        
        # Limit cache to MAX_CACHE_SIZE
        if len(REPORT_CACHE) > MAX_CACHE_SIZE:
            oldest_report_id = REPORT_CACHE.popitem(last=False)[0]
            print(f"Cache full ({MAX_CACHE_SIZE}). Removed {oldest_report_id}")
        
        return jsonify({
            'success': True,
            'report_id': report.id,
            'share_token': report.share_token,
            'summary': summary,
            'address': report.address,
            'message': 'Report uploaded and processed successfully. Ready for questions!'
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error processing report', 'details': str(e)}), 500


@app.route('/api/report/<report_id>', methods=['GET'])
def get_report(report_id):
    """
    Get report details (for authenticated access)
    """
    try:
        report = InspectionReport.query.get(report_id)
        
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        return jsonify({
            'id': report.id,
            'address': report.address,
            'inspector_name': report.inspector_name,
            'inspection_date': report.inspection_date.isoformat(),
            'report_type': report.report_type,
            'summary': report.summary,
            'created_at': report.created_at.isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/shared/<share_token>', methods=['GET'])
def get_shared_report(share_token):
    """
    Get report via share token (for customer portal)
    Returns summary and basic info - no full extracted text
    """
    try:
        report = InspectionReport.query.filter_by(
            share_token=share_token,
            is_shared=True
        ).first()
        
        if not report:
            return jsonify({'error': 'Report not found or not shared'}), 404
        
        return jsonify({
            'id': report.id,
            'address': report.address,
            'summary': report.summary,
            'report_type': report.report_type,
            'inspection_date': report.inspection_date.isoformat() if report.inspection_date else None,
            'share_token': share_token
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/ask/<report_id>', methods=['POST'])
def ask_question(report_id):
    """
    Ask a question about an inspection report
    Uses in-memory cache for fast responses on follow-up questions
    
    Expected JSON:
    {
        "question": "Is the roof a big problem?"
    }
    """
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
        
        # Check if conversation is already cached
        if report_id in REPORT_CACHE:
            print(f"Using cached conversation for {report_id}")
            qa_system = REPORT_CACHE[report_id]
        else:
            # Initialize Q&A system and cache it
            print(f"Creating new conversation for {report_id}")
            qa_system = InspectionReportQA(report.extracted_text)
            
            # Add to cache
            REPORT_CACHE[report_id] = qa_system
            
            # Limit cache to MAX_CACHE_SIZE
            if len(REPORT_CACHE) > MAX_CACHE_SIZE:
                oldest_report_id = REPORT_CACHE.popitem(last=False)[0]
                print(f"Cache full ({MAX_CACHE_SIZE}). Removed {oldest_report_id}")
        
        # Get answer
        print(f"Processing question for report {report_id}...")
        answer = qa_system.answer_question(question)
        
        # Store conversation in database
        conversation = Conversation(
            report_id=report.id,
            customer_question=question,
            ai_response=answer,
            question_number=len(report.conversations) + 1
        )
        
        db.session.add(conversation)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'conversation_id': conversation.id,
            'question': question,
            'answer': answer,
            'timestamp': conversation.created_at.isoformat()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error processing question', 'details': str(e)}), 500


@app.route('/api/conversations/<report_id>', methods=['GET'])
def get_conversations(report_id):
    """
    Get all Q&A conversations for a report
    """
    try:
        report = InspectionReport.query.get(report_id)
        
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        conversations = Conversation.query.filter_by(report_id=report_id).order_by(
            Conversation.question_number.asc()
        ).all()
        
        return jsonify({
            'report_id': report_id,
            'total_questions': len(conversations),
            'conversations': [
                {
                    'id': c.id,
                    'question': c.customer_question,
                    'answer': c.ai_response,
                    'timestamp': c.created_at.isoformat()
                }
                for c in conversations
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/reports', methods=['GET'])
def list_reports():
    """
    List all uploaded reports (for dashboard/admin)
    """
    try:
        reports = InspectionReport.query.order_by(
            InspectionReport.created_at.desc()
        ).all()
        
        return jsonify({
            'total_reports': len(reports),
            'cached_reports': len(REPORT_CACHE),
            'cache_max_size': MAX_CACHE_SIZE,
            'reports': [
                {
                    'id': r.id,
                    'address': r.address,
                    'report_type': r.report_type,
                    'created_at': r.created_at.isoformat(),
                    'share_token': r.share_token,
                    'total_questions': len(r.conversations),
                    'cached': r.id in REPORT_CACHE
                }
                for r in reports
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/cache-status', methods=['GET'])
def cache_status():
    """
    Get current cache status
    """
    return jsonify({
        'cached_reports': len(REPORT_CACHE),
        'max_cache_size': MAX_CACHE_SIZE,
        'report_ids_in_cache': list(REPORT_CACHE.keys())
    }), 200


# ============================================================================
# INITIALIZATION
# ============================================================================

@app.before_request
def before_request():
    """Initialize database before first request"""
    pass


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Database initialized")
    
    # Development server
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=app.config['DEBUG']
    )