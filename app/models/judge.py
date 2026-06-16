from datetime import datetime
from app.extensions import db
from app.models.judgment import CourtLevel


class Judge(db.Model):
    __tablename__ = 'judges'
    __table_args__ = (
        db.Index('ix_judges_court_location', 'court_level', 'court_location'),
    )

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    title = db.Column(db.String(50), nullable=True)
    court_level = db.Column(db.Enum(CourtLevel), nullable=False, index=True)
    court_location = db.Column(db.String(120), nullable=False)
    date_appointed = db.Column(db.Date, nullable=True)
    date_retired = db.Column(db.Date, nullable=True)
    biography_text = db.Column(db.Text, nullable=True)
    bar_council_id = db.Column(db.String(50), nullable=True, unique=True)
    photo_url = db.Column(db.String(500), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    analytics = db.relationship('JudgeAnalytics', backref='judge', uselist=False, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Judge {self.full_name}>'

    @property
    def display_name(self):
        if self.title:
            return f'{self.title} {self.full_name}'
        return self.full_name


class JudgeAnalytics(db.Model):
    __tablename__ = 'judge_analytics'

    id = db.Column(db.Integer, primary_key=True)
    judge_id = db.Column(db.Integer, db.ForeignKey('judges.id'), nullable=False, unique=True, index=True)
    total_cases = db.Column(db.Integer, default=0, nullable=False)
    plaintiff_win_rate = db.Column(db.Float, nullable=True)
    defendant_win_rate = db.Column(db.Float, nullable=True)
    avg_days_to_judgment = db.Column(db.Float, nullable=True)
    subject_matter_breakdown = db.Column(db.JSON, default=dict, nullable=False)
    motion_grant_rates = db.Column(db.JSON, default=dict, nullable=False)
    cases_by_year = db.Column(db.JSON, default=dict, nullable=False)
    cases_by_court_level = db.Column(db.JSON, default=dict, nullable=False)
    most_cited_statutes = db.Column(db.JSON, default=list, nullable=False)
    landmark_judgments = db.Column(db.JSON, default=list, nullable=False)
    computed_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<JudgeAnalytics judge_id={self.judge_id}>'
