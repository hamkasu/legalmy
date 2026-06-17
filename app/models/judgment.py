from datetime import datetime
from enum import Enum
import uuid
from pgvector.sqlalchemy import Vector
from app.extensions import db


class CourtLevel(Enum):
    FEDERAL = 'FEDERAL'
    APPEAL = 'APPEAL'
    HIGH = 'HIGH'
    SESSIONS = 'SESSIONS'
    MAGISTRATE = 'MAGISTRATE'
    INDUSTRIAL = 'INDUSTRIAL'
    SYARIAH_HIGH = 'SYARIAH_HIGH'
    SYARIAH_APPEAL = 'SYARIAH_APPEAL'


class OutcomeType(Enum):
    ALLOWED = 'allowed'
    DISMISSED = 'dismissed'
    PARTLY_ALLOWED = 'partly_allowed'
    STRUCK_OUT = 'struck_out'


class CitationRelationship(Enum):
    FOLLOWED = 'followed'
    DISTINGUISHED = 'distinguished'
    OVERRULED = 'overruled'
    CONSIDERED = 'considered'
    REFERRED = 'referred'
    APPROVED = 'approved'


class Judgment(db.Model):
    __tablename__ = 'judgments'
    __table_args__ = (
        db.Index('ix_judgments_court_date', 'court_level', 'date_decided'),
        db.Index('ix_judgments_citation', 'citation'),
        db.Index('ix_judgments_embedding', 'embedding', postgresql_using='ivfflat', postgresql_with={'opclasses': 'vector_cosine_ops'}),
    )

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    citation = db.Column(db.String(255), nullable=False, unique=True, index=True)
    title = db.Column(db.String(500), nullable=False)
    court_level = db.Column(db.Enum(CourtLevel), nullable=False, index=True)
    court_location = db.Column(db.String(120), nullable=False)
    coram = db.Column(db.JSON, default=list, nullable=False)
    parties_plaintiff = db.Column(db.ARRAY(db.String), default=list, nullable=False)
    parties_defendant = db.Column(db.ARRAY(db.String), default=list, nullable=False)
    date_decided = db.Column(db.Date, nullable=True, index=True)
    date_delivered = db.Column(db.Date, nullable=True)
    subject_matter = db.Column(db.ARRAY(db.String), default=list, nullable=False)
    full_text = db.Column(db.Text, nullable=False)
    summary_ai = db.Column(db.Text, nullable=True)
    summary_ai_bm = db.Column(db.Text, nullable=True)
    outcome = db.Column(db.Enum(OutcomeType), nullable=True)
    neutral_citation = db.Column(db.String(255), nullable=True)
    mlj_citation = db.Column(db.String(255), nullable=True)
    clj_citation = db.Column(db.String(255), nullable=True)
    amr_citation = db.Column(db.String(255), nullable=True)
    mlra_citation = db.Column(db.String(255), nullable=True)
    law_report_refs = db.Column(db.JSON, default=dict, nullable=False)
    embedding = db.Column(Vector(1536), nullable=True)
    search_vector = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    source_url = db.Column(db.String(500), nullable=True)
    is_published = db.Column(db.Boolean, default=True, nullable=False)
    language = db.Column(db.String(2), default='en', nullable=False)

    citations_made = db.relationship(
        'Citation',
        foreign_keys='Citation.citing_judgment_id',
        backref='citing_judgment',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    citations_received = db.relationship(
        'Citation',
        foreign_keys='Citation.cited_judgment_id',
        backref='cited_judgment',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    linked_case = db.relationship('Case', backref='judgment', uselist=False, foreign_keys='Case.judgment_id')

    def __repr__(self):
        return f'<Judgment {self.citation}>'

    @property
    def citation_count(self):
        return self.citations_received.count()


class Citation(db.Model):
    __tablename__ = 'citations'
    __table_args__ = (
        db.Index('ix_citations_citing', 'citing_judgment_id'),
        db.Index('ix_citations_cited', 'cited_judgment_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    citing_judgment_id = db.Column(db.String(36), db.ForeignKey('judgments.id'), nullable=False, index=True)
    cited_judgment_id = db.Column(db.String(36), db.ForeignKey('judgments.id'), nullable=False, index=True)
    relationship = db.Column(db.Enum(CitationRelationship), nullable=False)
    paragraph_ref = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<Citation {self.citing_judgment_id} → {self.cited_judgment_id}>'
