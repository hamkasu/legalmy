from flask import Blueprint, render_template, request, jsonify
from app.models.judge import Judge, JudgeAnalytics
from app.models.judgment import Judgment, CourtLevel
from app.services.analytics_service import AnalyticsService
from app.extensions import db

bp = Blueprint('judges', __name__, template_folder='templates')
analytics_service = AnalyticsService()


@bp.route('/', methods=['GET'])
def index():
    """List all judges with search and filter."""
    page = request.args.get('page', 1, type=int)
    per_page = 20

    query = Judge.query.filter_by(is_active=True)

    # Filter by court level
    court_level = request.args.get('court_level')
    if court_level:
        try:
            query = query.filter_by(court_level=CourtLevel[court_level])
        except KeyError:
            pass

    # Filter by location
    location = request.args.get('location')
    if location:
        query = query.filter_by(court_location=location)

    # Sort by total cases (via analytics)
    judges = query.all()

    # Get analytics for sorting
    judge_data = []
    for judge in judges:
        analytics = JudgeAnalytics.query.filter_by(judge_id=judge.id).first()
        judge_data.append({
            'judge': judge,
            'analytics': analytics,
            'total_cases': analytics.total_cases if analytics else 0
        })

    # Sort by total cases
    judge_data.sort(key=lambda x: x['total_cases'], reverse=True)

    # Paginate
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated = judge_data[start_idx:end_idx]
    total = len(judge_data)
    pages = (total + per_page - 1) // per_page

    return render_template(
        'judges/list.html',
        judges=paginated,
        page=page,
        pages=pages,
        total=total,
        court_levels=[cl.value for cl in CourtLevel],
    )


@bp.route('/<int:judge_id>', methods=['GET'])
def profile(judge_id):
    """Judge profile with analytics and judgment history."""
    judge = Judge.query.get_or_404(judge_id)
    analytics = JudgeAnalytics.query.filter_by(judge_id=judge_id).first()

    # Get recent judgments
    recent_judgments = db.session.query(Judgment).filter(
        Judgment.coram.contains([{'name': judge.full_name}])
    ).order_by(Judgment.date_decided.desc()).limit(10).all()

    # Compute analytics if not yet done
    if not analytics:
        analytics = analytics_service.compute_judge_analytics(judge_id)

    # Generate AI insight
    insight = None
    if analytics:
        insight = analytics_service.generate_judge_insight(judge_id)

    return render_template(
        'judges/profile.html',
        judge=judge,
        analytics=analytics,
        recent_judgments=recent_judgments,
        insight=insight,
    )


@bp.route('/api/<int:judge_id>/analytics', methods=['GET'])
def api_get_analytics(judge_id):
    """API endpoint returning judge analytics as JSON."""
    judge = Judge.query.get(judge_id)
    if not judge:
        return jsonify({'status': 'error', 'message': 'Judge not found'}), 404

    analytics = JudgeAnalytics.query.filter_by(judge_id=judge_id).first()

    if not analytics:
        # Compute on-demand
        analytics = analytics_service.compute_judge_analytics(judge_id)

    if not analytics:
        return jsonify({'status': 'error', 'message': 'No analytics available'}), 404

    return jsonify({
        'status': 'success',
        'judge_id': judge_id,
        'full_name': judge.full_name,
        'court_level': judge.court_level.value,
        'court_location': judge.court_location,
        'total_cases': analytics.total_cases,
        'plaintiff_win_rate': analytics.plaintiff_win_rate,
        'defendant_win_rate': analytics.defendant_win_rate,
        'avg_days_to_judgment': analytics.avg_days_to_judgment,
        'subject_matter_breakdown': analytics.subject_matter_breakdown,
        'cases_by_year': analytics.cases_by_year,
        'cases_by_court_level': analytics.cases_by_court_level,
        'most_cited_statutes': analytics.most_cited_statutes,
        'landmark_judgments': analytics.landmark_judgments,
        'computed_at': analytics.computed_at.isoformat(),
    })
