from flask import Blueprint, render_template, request, jsonify
from app.extensions import db
from app.models.lawyer import Lawyer, LawFirm, LawyerAnalytics

bp = Blueprint('lawyers', __name__, template_folder='templates')


@bp.route('/')
def index():
    """List all active lawyers."""
    page = request.args.get('page', 1, type=int)
    per_page = 20

    query = Lawyer.query.filter_by(is_active=True)

    # Filter by firm
    firm_id = request.args.get('firm_id', type=int)
    if firm_id:
        query = query.filter_by(firm_id=firm_id)

    paginated = query.order_by(Lawyer.full_name).paginate(page=page, per_page=per_page)

    firms = LawFirm.query.all()

    return render_template(
        'lawyers/list.html',
        lawyers=paginated.items,
        paginated=paginated,
        firms=firms
    )


@bp.route('/<int:lawyer_id>')
def profile(lawyer_id):
    """Lawyer profile with analytics."""
    lawyer = Lawyer.query.get_or_404(lawyer_id)
    analytics = LawyerAnalytics.query.filter_by(lawyer_id=lawyer_id).first()

    return render_template(
        'lawyers/profile.html',
        lawyer=lawyer,
        analytics=analytics
    )


@bp.route('/api/<int:lawyer_id>/analytics')
def api_get_analytics(lawyer_id):
    """API endpoint for lawyer analytics."""
    lawyer = Lawyer.query.get(lawyer_id)
    if not lawyer:
        return jsonify({'status': 'error', 'message': 'Lawyer not found'}), 404

    analytics = LawyerAnalytics.query.filter_by(lawyer_id=lawyer_id).first()

    if not analytics:
        return jsonify({'status': 'error', 'message': 'No analytics available'}), 404

    return jsonify({
        'status': 'success',
        'lawyer_id': lawyer_id,
        'full_name': lawyer.full_name,
        'bar_council_number': lawyer.bar_council_number,
        'total_appearances': analytics.total_appearances,
        'win_rate_plaintiff': analytics.win_rate_plaintiff,
        'win_rate_defendant': analytics.win_rate_defendant,
        'court_breakdown': analytics.court_breakdown,
        'computed_at': analytics.computed_at.isoformat() if analytics.computed_at else None,
    })
