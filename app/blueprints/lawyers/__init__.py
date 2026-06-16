from flask import Blueprint

lawyers_bp = Blueprint('lawyers', __name__, template_folder='templates')

from app.blueprints.lawyers import routes
