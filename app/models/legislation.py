from datetime import datetime
from enum import Enum
from pgvector.sqlalchemy import Vector
from app.extensions import db


class SubLegislationType(Enum):
    PU_A = 'PU_A'
    PU_B = 'PU_B'


class Act(db.Model):
    __tablename__ = 'acts'
    __table_args__ = (
        db.Index('ix_acts_act_number', 'act_number'),
    )

    id = db.Column(db.Integer, primary_key=True)
    short_title = db.Column(db.String(255), nullable=False)
    long_title = db.Column(db.String(500), nullable=True)
    act_number = db.Column(db.String(50), nullable=False, unique=True, index=True)
    year = db.Column(db.Integer, nullable=False)
    current_in_force_from = db.Column(db.Date, nullable=True)
    repealed_on = db.Column(db.Date, nullable=True)
    category = db.Column(db.JSON, default=list, nullable=False)
    full_text_url = db.Column(db.String(500), nullable=True)
    full_text = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    sections = db.relationship('Section', backref='act', lazy='dynamic', cascade='all, delete-orphan')
    sub_legislations = db.relationship('SubLegislation', backref='parent_act', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Act {self.act_number}>'

    @property
    def is_current(self):
        return self.repealed_on is None


class Section(db.Model):
    __tablename__ = 'sections'
    __table_args__ = (
        db.Index('ix_sections_act_section', 'act_id', 'section_number'),
        db.Index('ix_sections_embedding', 'embedding', postgresql_using='ivfflat', postgresql_with={'opclasses': 'vector_cosine_ops'}),
    )

    id = db.Column(db.Integer, primary_key=True)
    act_id = db.Column(db.Integer, db.ForeignKey('acts.id'), nullable=False, index=True)
    section_number = db.Column(db.String(50), nullable=False)
    heading = db.Column(db.String(255), nullable=True)
    content = db.Column(db.Text, nullable=False)
    embedding = db.Column(Vector(1536), nullable=True)
    search_vector = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<Section {self.act.act_number} - Section {self.section_number}>'

    @property
    def full_citation(self):
        return f'{self.act.act_number}, Section {self.section_number}'


class SubLegislation(db.Model):
    __tablename__ = 'sub_legislations'
    __table_args__ = (
        db.Index('ix_sub_legislations_pu_number', 'pu_number'),
    )

    id = db.Column(db.Integer, primary_key=True)
    act_id = db.Column(db.Integer, db.ForeignKey('acts.id'), nullable=False, index=True)
    pu_number = db.Column(db.String(50), nullable=False, unique=True, index=True)
    type = db.Column(db.Enum(SubLegislationType), nullable=False)
    title = db.Column(db.String(500), nullable=False)
    gazetted_date = db.Column(db.Date, nullable=True)
    full_text = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<SubLegislation {self.pu_number}>'
