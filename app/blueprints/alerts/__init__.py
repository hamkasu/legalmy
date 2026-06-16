from flask import Blueprint

alerts_bp = Blueprint('alerts', __name__, template_folder='templates')

from app.blueprints.alerts import routes
