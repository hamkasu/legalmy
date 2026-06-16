from flask import Blueprint

ai_bp = Blueprint('ai', __name__, template_folder='templates')

from app.blueprints.ai import routes
