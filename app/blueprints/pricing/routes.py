from flask import Blueprint, render_template

bp = Blueprint('pricing', __name__)


@bp.route('/pricing')
def index():
    """Pricing page with plan comparison."""
    return render_template('pricing.html')
