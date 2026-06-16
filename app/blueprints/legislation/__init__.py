from flask import Blueprint

legislation_bp = Blueprint('legislation', __name__, template_folder='templates')

from app.blueprints.legislation import routes
