from flask import Blueprint

judgments_bp = Blueprint('judgments', __name__, template_folder='templates')

from app.blueprints.judgments import routes
