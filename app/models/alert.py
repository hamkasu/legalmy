from datetime import datetime
from enum import Enum
from app.extensions import db


class AlertFrequency(Enum):
    DAILY = 'daily'
    WEEKLY = 'weekly'


class SavedSearch(db.Model):
    __tablename__ = 'saved_searches'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    query_json = db.Column(db.JSON, default=dict, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    alerts = db.relationship('Alert', backref='saved_search', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<SavedSearch {self.name}>'


class Alert(db.Model):
    __tablename__ = 'alerts'

    id = db.Column(db.Integer, primary_key=True)
    saved_search_id = db.Column(db.Integer, db.ForeignKey('saved_searches.id'), nullable=False, index=True)
    frequency = db.Column(db.Enum(AlertFrequency), default=AlertFrequency.DAILY, nullable=False)
    last_sent = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    delivery_email = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<Alert {self.saved_search.name}>'
