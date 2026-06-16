from flask import Blueprint

judges_bp = Blueprint('judges', __name__, template_folder='templates')

from app.blueprints.judges import routes
