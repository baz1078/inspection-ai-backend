from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()

class InspectionReport(db.Model):
    __tablename__ = 'inspection_reports'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    address = db.Column(db.String(255), nullable=False)
    customer_name = db.Column(db.String(255))
    customer_email = db.Column(db.String(255))
    customer_phone = db.Column(db.String(20))
    inspector_name = db.Column(db.String(255))
    inspection_date = db.Column(db.DateTime, default=datetime.utcnow)
    report_type = db.Column(db.String(50))
    original_filename = db.Column(db.String(255))
    file_path = db.Column(db.String(500))
    file_size = db.Column(db.Integer)
    extracted_text = db.Column(db.Text)
    summary = db.Column(db.Text)
    share_token = db.Column(db.String(100), unique=True, default=lambda: str(uuid.uuid4()))
    is_shared = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    conversations = db.relationship('Conversation', backref='report', lazy=True, cascade='all, delete-orphan')
    questions = db.relationship('Question', backref='report', lazy=True, cascade='all, delete-orphan')
    leads = db.relationship('Lead', backref='report', lazy=True, cascade='all, delete-orphan')
    report_warranties = db.relationship('ReportWarranty', backref='report', lazy=True, cascade='all, delete-orphan')
    warranty_queries = db.relationship('WarrantyQuery', backref='report', lazy=True, cascade='all, delete-orphan')

class Conversation(db.Model):
    __tablename__ = 'conversations'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id = db.Column(db.String(36), db.ForeignKey('inspection_reports.id'), nullable=False)
    customer_question = db.Column(db.Text)
    ai_response = db.Column(db.Text)
    question_number = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Question(db.Model):
    __tablename__ = 'questions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id = db.Column(db.String(36), db.ForeignKey('inspection_reports.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    issue_type = db.Column(db.String(50))
    answer = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Contractor(db.Model):
    __tablename__ = 'contractors'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(255), nullable=False)
    specialty = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(255))
    zip_codes = db.Column(db.Text)
    city = db.Column(db.String(100))
    state = db.Column(db.String(2))
    rating = db.Column(db.Float, default=0.0)
    review_count = db.Column(db.Integer, default=0)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(500))
    website = db.Column(db.String(500))
    is_licensed = db.Column(db.Boolean, default=True)
    is_bonded = db.Column(db.Boolean, default=True)
    is_insured = db.Column(db.Boolean, default=True)
    cost_per_lead = db.Column(db.Float, default=25.0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    leads = db.relationship('Lead', backref='contractor', lazy=True, cascade='all, delete-orphan')

class Lead(db.Model):
    __tablename__ = 'leads'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id = db.Column(db.String(36), db.ForeignKey('inspection_reports.id'), nullable=False)
    question_id = db.Column(db.String(36), db.ForeignKey('questions.id'), nullable=False)
    contractor_id = db.Column(db.String(36), db.ForeignKey('contractors.id'), nullable=False)
    customer_name = db.Column(db.String(255), nullable=True)
    customer_email = db.Column(db.String(255), nullable=True)
    customer_phone = db.Column(db.String(20), nullable=True)
    status = db.Column(db.String(50), default='pending')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    question = db.relationship('Question', backref='leads')

class Analytics(db.Model):
    __tablename__ = 'analytics'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id = db.Column(db.String(36))
    issue_type = db.Column(db.String(50))
    question_count = db.Column(db.Integer, default=0)
    lead_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ============================================================================
# WARRANTY MODELS - NEW ADDITIONS
# ============================================================================

class WarrantyDocument(db.Model):
    __tablename__ = 'warranty_documents'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Warranty identification
    builder_name = db.Column(db.String(255), nullable=False)
    warranty_type = db.Column(db.String(100), nullable=False)
    jurisdiction = db.Column(db.String(50))
    
    # Document storage
    file_path = db.Column(db.String(500))
    original_filename = db.Column(db.String(255))
    file_size = db.Column(db.Integer)
    extracted_text = db.Column(db.Text)
    
    # Parsed warranty rules (JSON structure)
    coverage_rules = db.Column(db.Text)
    
    # Metadata
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    report_warranties = db.relationship('ReportWarranty', backref='warranty', lazy=True, cascade='all, delete-orphan')
    warranty_queries = db.relationship('WarrantyQuery', backref='warranty_doc', lazy=True, cascade='all, delete-orphan')

class ReportWarranty(db.Model):
    __tablename__ = 'report_warranties'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Links inspection to warranty document
    report_id = db.Column(db.String(36), db.ForeignKey('inspection_reports.id'), nullable=False)
    warranty_id = db.Column(db.String(36), db.ForeignKey('warranty_documents.id'), nullable=False)
    
    # Warranty certificate info (extracted from PDF)
    certificate_number = db.Column(db.String(255))
    warranty_start_date = db.Column(db.DateTime)
    warranty_end_date = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class WarrantyQuery(db.Model):
    __tablename__ = 'warranty_queries'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Links question to warranty analysis
    report_id = db.Column(db.String(36), db.ForeignKey('inspection_reports.id'), nullable=False)
    warranty_id = db.Column(db.String(36), db.ForeignKey('warranty_documents.id'), nullable=False)
    
    # The question and analysis
    customer_question = db.Column(db.Text)
    inspection_finding = db.Column(db.Text)
    
    # AI Analysis result
    claimability = db.Column(db.String(50))
    claim_reason = db.Column(db.Text)
    warranty_section = db.Column(db.String(255))
    ai_analysis = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
