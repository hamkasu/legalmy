from datetime import datetime
from enum import Enum
from app.extensions import db
from app.models.judgment import CourtLevel


class CaseStatus(Enum):
    ACTIVE = 'active'
    DECIDED = 'decided'
    STRUCK_OUT = 'struck_out'
    SETTLED = 'settled'


class PartyRole(Enum):
    PLAINTIFF = 'plaintiff'
    DEFENDANT = 'defendant'
    INTERVENER = 'intervener'
    APPELLANT = 'appellant'
    RESPONDENT = 'respondent'
    CLAIMANT = 'claimant'


class DocumentType(Enum):
    STATEMENT_OF_CLAIM = 'statement_of_claim'
    DEFENCE = 'defence'
    AFFIDAVIT = 'affidavit'
    WRITTEN_SUBMISSION = 'written_submission'
    ORDER = 'order'
    JUDGMENT = 'judgment'


class Case(db.Model):
    __tablename__ = 'cases'
    __table_args__ = (
        db.Index('ix_cases_case_number', 'case_number'),
        db.Index('ix_cases_court_filing', 'court_level', 'filing_date'),
    )

    id = db.Column(db.Integer, primary_key=True)
    case_number = db.Column(db.String(100), nullable=False, unique=True, index=True)
    court_level = db.Column(db.Enum(CourtLevel), nullable=False, index=True)
    court_location = db.Column(db.String(120), nullable=False)
    filing_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.Enum(CaseStatus), default=CaseStatus.ACTIVE, nullable=False)
    title = db.Column(db.String(500), nullable=False)
    judgment_id = db.Column(db.String(36), db.ForeignKey('judgments.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    parties = db.relationship('Party', backref='case', lazy='dynamic', cascade='all, delete-orphan')
    documents = db.relationship('CaseDocument', backref='case', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Case {self.case_number}>'

    @property
    def plaintiffs(self):
        return [p.name for p in self.parties.filter_by(role=PartyRole.PLAINTIFF).all()]

    @property
    def defendants(self):
        return [p.name for p in self.parties.filter_by(role=PartyRole.DEFENDANT).all()]


class Party(db.Model):
    __tablename__ = 'parties'
    __table_args__ = (
        db.Index('ix_parties_case_role', 'case_id', 'role'),
    )

    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('cases.id'), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(PartyRole), nullable=False)
    counsel_id = db.Column(db.Integer, db.ForeignKey('lawyers.id'), nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<Party {self.name} ({self.role.value})>'


class CaseDocument(db.Model):
    __tablename__ = 'case_documents'
    __table_args__ = (
        db.Index('ix_case_documents_case_type', 'case_id', 'doc_type'),
    )

    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('cases.id'), nullable=False, index=True)
    doc_type = db.Column(db.Enum(DocumentType), nullable=False)
    filed_date = db.Column(db.Date, nullable=True)
    file_url = db.Column(db.String(500), nullable=True)
    summary_ai = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<CaseDocument {self.case_id} - {self.doc_type.value}>'
