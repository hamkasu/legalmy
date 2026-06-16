from datetime import datetime
from enum import Enum
from app.extensions import db


class HeadcountTier(Enum):
    SOLO = 'solo'
    SMALL = 'small'
    MEDIUM = 'medium'
    LARGE = 'large'


class LawFirm(db.Model):
    __tablename__ = 'law_firms'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.String(500), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    website = db.Column(db.String(255), nullable=True)
    established_year = db.Column(db.Integer, nullable=True)
    headcount_tier = db.Column(db.Enum(HeadcountTier), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    lawyers = db.relationship('Lawyer', backref='firm', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<LawFirm {self.name}>'


class Lawyer(db.Model):
    __tablename__ = 'lawyers'
    __table_args__ = (
        db.Index('ix_lawyers_bar_council', 'bar_council_number'),
    )

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    bar_council_number = db.Column(db.String(50), nullable=False, unique=True, index=True)
    firm_id = db.Column(db.Integer, db.ForeignKey('law_firms.id'), nullable=True, index=True)
    call_year = db.Column(db.Integer, nullable=True)
    specialisations = db.Column(db.ARRAY(db.String), default=list, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    analytics = db.relationship('LawyerAnalytics', backref='lawyer', uselist=False, cascade='all, delete-orphan')
    counsel_appearances = db.relationship('Party', backref='counsel', lazy='dynamic', foreign_keys='Party.counsel_id')

    def __repr__(self):
        return f'<Lawyer {self.full_name}>'

    @property
    def years_of_experience(self):
        if self.call_year:
            from datetime import datetime
            return datetime.utcnow().year - self.call_year
        return None


class LawyerAnalytics(db.Model):
    __tablename__ = 'lawyer_analytics'

    id = db.Column(db.Integer, primary_key=True)
    lawyer_id = db.Column(db.Integer, db.ForeignKey('lawyers.id'), nullable=False, unique=True, index=True)
    total_appearances = db.Column(db.Integer, default=0, nullable=False)
    win_rate_plaintiff = db.Column(db.Float, nullable=True)
    win_rate_defendant = db.Column(db.Float, nullable=True)
    court_breakdown = db.Column(db.JSON, default=dict, nullable=False)
    subject_matter_breakdown = db.Column(db.JSON, default=dict, nullable=False)
    computed_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<LawyerAnalytics lawyer_id={self.lawyer_id}>'
