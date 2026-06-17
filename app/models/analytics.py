from datetime import datetime
from app.extensions import db


class AIUsage(db.Model):
    __tablename__ = 'ai_usage'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    tool_name = db.Column(db.String(120), nullable=False)
    input_tokens = db.Column(db.Integer, default=0, nullable=False)
    output_tokens = db.Column(db.Integer, default=0, nullable=False)
    cost_usd = db.Column(db.Float, default=0.0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship('User', backref='ai_usages')

    def __repr__(self):
        return f'<AIUsage {self.user_id} - {self.tool_name}>'
