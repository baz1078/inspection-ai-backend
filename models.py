from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()

class InspectionReport(db.Model):
    __tablename__ = 'InspectionReport'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    address = db.Column(db.String(255), nullable=False)
    customerName = db.Column(db.String(255))
    customerEmail = db.Column(db.String(255))
    customerPhone = db.Column(db.String(20))
    inspectorName = db.Column(db.String(255))
    inspectionDate = db.Column(db.DateTime, default=datetime.utcnow)
    reportType = db.Column(db.String(50))
    originalFilename = db.Column(db.String(255))
    filePath = db.Column(db.String(500))
    fileSize = db.Column(db.Integer)
    extractedText = db.Column(db.Text)
    summary = db.Column(db.Text)
    shareToken = db.Column(db.String(100), unique=True, default=lambda: str(uuid.uuid4()))
    isShared = db.Column(db.Boolean, default=True)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    conversations = db.relationship('Conversation', backref='report', lazy=True, cascade='all, delete-orphan')
    questions = db.relationship('Question', backref='report', lazy=True, cascade='all, delete-orphan')
    leads = db.relationship('Lead', backref='report', lazy=True, cascade='all, delete-orphan')
    reportWarranties = db.relationship('ReportWarranty', backref='report', lazy=True, cascade='all, delete-orphan')
    warrantyQueries = db.relationship('WarrantyQuery', backref='report', lazy=True, cascade='all, delete-orphan')

class Conversation(db.Model):
    __tablename__ = 'Conversation'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    reportId = db.Column(db.String(36), db.ForeignKey('InspectionReport.id'), nullable=False)
    customerQuestion = db.Column(db.Text)
    aiResponse = db.Column(db.Text)
    questionNumber = db.Column(db.Integer)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)

class Question(db.Model):
    __tablename__ = 'Question'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    reportId = db.Column(db.String(36), db.ForeignKey('InspectionReport.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    issueType = db.Column(db.String(50))
    answer = db.Column(db.Text)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)

class Contractor(db.Model):
    __tablename__ = 'Contractor'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(255), nullable=False)
    specialty = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(255))
    zipCodes = db.Column(db.Text)
    city = db.Column(db.String(100))
    state = db.Column(db.String(2))
    rating = db.Column(db.Float, default=0.0)
    reviewCount = db.Column(db.Integer, default=0)
    description = db.Column(db.Text)
    imageUrl = db.Column(db.String(500))
    website = db.Column(db.String(500))
    isLicensed = db.Column(db.Boolean, default=True)
    isBonded = db.Column(db.Boolean, default=True)
    isInsured = db.Column(db.Boolean, default=True)
    costPerLead = db.Column(db.Float, default=25.0)
    isActive = db.Column(db.Boolean, default=True)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    leads = db.relationship('Lead', backref='contractor', lazy=True, cascade='all, delete-orphan')

class Lead(db.Model):
    __tablename__ = 'Lead'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    reportId = db.Column(db.String(36), db.ForeignKey('InspectionReport.id'), nullable=False)
    questionId = db.Column(db.String(36), db.ForeignKey('Question.id'), nullable=False)
    contractorId = db.Column(db.String(36), db.ForeignKey('Contractor.id'), nullable=False)
    customerName = db.Column(db.String(255), nullable=True)
    customerEmail = db.Column(db.String(255), nullable=True)
    customerPhone = db.Column(db.String(20), nullable=True)
    status = db.Column(db.String(50), default='pending')
    notes = db.Column(db.Text)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    question = db.relationship('Question', backref='leads')

class Analytics(db.Model):
    __tablename__ = 'Analytics'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    reportId = db.Column(db.String(36))
    issueType = db.Column(db.String(50))
    questionCount = db.Column(db.Integer, default=0)
    leadCount = db.Column(db.Integer, default=0)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)

class WarrantyDocument(db.Model):
    __tablename__ = 'WarrantyDocument'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    builderName = db.Column(db.String(255), nullable=False)
    warrantyType = db.Column(db.String(100), nullable=False)
    jurisdiction = db.Column(db.String(50))
    filePath = db.Column(db.String(500))
    originalFilename = db.Column(db.String(255))
    fileSize = db.Column(db.Integer)
    extractedText = db.Column(db.Text)
    coverageRules = db.Column(db.Text)
    isActive = db.Column(db.Boolean, default=True)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    reportWarranties = db.relationship('ReportWarranty', backref='warranty', lazy=True, cascade='all, delete-orphan')
    warrantyQueries = db.relationship('WarrantyQuery', backref='warrantyDoc', lazy=True, cascade='all, delete-orphan')

class ReportWarranty(db.Model):
    __tablename__ = 'ReportWarranty'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    reportId = db.Column(db.String(36), db.ForeignKey('InspectionReport.id'), nullable=False)
    warrantyId = db.Column(db.String(36), db.ForeignKey('WarrantyDocument.id'), nullable=False)
    certificateNumber = db.Column(db.String(255))
    warrantyStartDate = db.Column(db.DateTime)
    warrantyEndDate = db.Column(db.DateTime)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class WarrantyQuery(db.Model):
    __tablename__ = 'WarrantyQuery'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    reportId = db.Column(db.String(36), db.ForeignKey('InspectionReport.id'), nullable=False)
    warrantyId = db.Column(db.String(36), db.ForeignKey('WarrantyDocument.id'), nullable=False)
    customerQuestion = db.Column(db.Text)
    inspectionFinding = db.Column(db.Text)
    claimability = db.Column(db.String(50))
    claimReason = db.Column(db.Text)
    warrantySection = db.Column(db.String(255))
    aiAnalysis = db.Column(db.Text)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)

class DamageAssessmentReport(db.Model):
    __tablename__ = 'DamageAssessmentReport'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    reportId = db.Column(db.String(20), unique=True, nullable=False)
    customerName = db.Column(db.String(255), nullable=False)
    customerEmail = db.Column(db.String(255))
    customerPhone = db.Column(db.String(20))
    damageLocation = db.Column(db.String(50), nullable=False)
    waterSource = db.Column(db.String(255))
    damageDescription = db.Column(db.Text)
    photoPath = db.Column(db.String(500), nullable=False)
    pdfPath = db.Column(db.String(500), nullable=False)
    moldRisk = db.Column(db.Integer)
    claimApproval = db.Column(db.Integer)
    damageSeverity = db.Column(db.String(50))
    estimatedSquareFootage = db.Column(db.Integer)
    moistureSaturation = db.Column(db.String(50))
    affectedMaterials = db.Column(db.Text)
    visibleIssues = db.Column(db.Text)
    hiddenDamageRisk = db.Column(db.Text)
    recommendedAction = db.Column(db.Text)
    structuralRisk = db.Column(db.String(50))
    analysisData = db.Column(db.Text)
    shareToken = db.Column(db.String(100), unique=True)
    isShared = db.Column(db.Boolean, default=True)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<DamageAssessmentReport {self.reportId}>'