from flask import Blueprint

pricing_bp = Blueprint('pricing', __name__)

from app.blueprints.pricing import routes
