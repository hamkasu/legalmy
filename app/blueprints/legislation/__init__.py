from flask import Blueprint

legislation_bp = Blueprint('legislation', __name__)

from app.blueprints.legislation import routes
