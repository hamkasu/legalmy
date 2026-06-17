from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, Response
from flask_login import current_user
from sqlalchemy import func, desc, text
from datetime import datetime, timedelta
import json
import os

from app.extensions import db
from app.decorators import role_required
from app.models.user import User, UserRole, Subscription, SubscriptionStatus, ApiKey
from app.models.judgment import Judgment, CourtLevel
from app.models.judge import Judge, JudgeAnalytics
from app.models.lawyer import Lawyer, LawFirm
from app.models.alert import SavedSearch, Alert
from app.models.analytics import AIUsage

bp = Blueprint('admin', __name__, template_folder='templates')


@bp.before_request
@role_required('admin')
def check_admin():
    """Verify user is admin on all admin routes."""
    pass


@bp.route('/')
def dashboard():
    """Admin dashboard with overview stats."""
    # Total judgments by court level
    judgments_by_court = db.session.query(
        CourtLevel,
        func.count(Judgment.id).label('count')
    ).group_by(CourtLevel).all()

    # Ingestion activity (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    daily_ingestion = db.session.query(
        func.date(Judgment.created_at).label('date'),
        func.count(Judgment.id).label('count')
    ).filter(Judgment.created_at >= thirty_days_ago).group_by(
        func.date(Judgment.created_at)
    ).order_by('date').all()

    # User stats
    total_users = User.query.count()
    free_users = User.query.filter_by(role=UserRole.FREE).count()
    paid_users = Subscription.query.filter_by(
        status=SubscriptionStatus.ACTIVE
    ).count()
    
    # MRR calculation
    from app.config import PLANS
    mrr = 0
    for sub in Subscription.query.filter_by(status=SubscriptionStatus.ACTIVE).all():
        if sub.plan in PLANS:
            monthly_price = PLANS[sub.plan].get('price_myr', 0)
            mrr += monthly_price

    # AI usage this month
    from app.models.analytics import AIUsage
    month_start = datetime.utcnow().replace(day=1)
    total_ai_queries = AIUsage.query.filter(
        AIUsage.created_at >= month_start
    ).count()
    total_ai_cost = db.session.query(
        func.sum(AIUsage.cost_usd)
    ).filter(AIUsage.created_at >= month_start).scalar() or 0

    ai_by_tool = db.session.query(
        AIUsage.tool_name,
        func.count(AIUsage.id).label('count'),
        func.sum(AIUsage.cost_usd).label('cost')
    ).filter(AIUsage.created_at >= month_start).group_by(
        AIUsage.tool_name
    ).all()

    # Pending items
    unverified_lawyers = User.query.filter_by(
        is_verified=False, role=UserRole.SUBSCRIBER
    ).count()

    return render_template('admin/dashboard.html',
        judgments_by_court=judgments_by_court,
        daily_ingestion=daily_ingestion,
        total_users=total_users,
        free_users=free_users,
        paid_users=paid_users,
        mrr=round(mrr, 2),
        total_ai_queries=total_ai_queries,
        total_ai_cost=round(total_ai_cost, 2),
        ai_by_tool=ai_by_tool,
        unverified_lawyers=unverified_lawyers
    )


@bp.route('/judgments')
def judgments_manage():
    """Judgment management page."""
    page = request.args.get('page', 1, type=int)
    is_published = request.args.get('is_published', 'all')
    source = request.args.get('source', '')
    court_level = request.args.get('court_level', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')

    query = Judgment.query

    # Filters
    if is_published == 'true':
        query = query.filter_by(is_published=True)
    elif is_published == 'false':
        query = query.filter_by(is_published=False)

    if source:
        query = query.filter_by(source_url=source)

    if court_level:
        query = query.filter_by(court_level=court_level)

    if date_from:
        try:
            date_from_dt = datetime.fromisoformat(date_from)
            query = query.filter(Judgment.date_decided >= date_from_dt)
        except ValueError:
            pass

    if date_to:
        try:
            date_to_dt = datetime.fromisoformat(date_to)
            query = query.filter(Judgment.date_decided <= date_to_dt)
        except ValueError:
            pass

    paginated = query.order_by(desc(Judgment.created_at)).paginate(
        page=page, per_page=50
    )

    return render_template('admin/judgments.html',
        judgments=paginated.items,
        paginated=paginated,
        court_levels=[cl.value for cl in CourtLevel]
    )


@bp.route('/judgments/<int:judgment_id>/toggle-publish', methods=['POST'])
def toggle_judgment_publish(judgment_id):
    """Toggle judgment published status."""
    judgment = Judgment.query.get_or_404(judgment_id)
    judgment.is_published = not judgment.is_published
    db.session.commit()
    flash(f'Judgment updated.', 'success')
    return redirect(url_for('admin.judgments_manage'))


@bp.route('/judgments/export-csv')
def export_judgments_csv():
    """Export all judgments as CSV."""
    import csv
    from io import StringIO

    query = request.args.get('query', '')
    
    judgments = Judgment.query.all()
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Citation', 'Title', 'Court Level', 'Date Decided', 
                     'Published', 'Source', 'Created At'])
    
    for j in judgments:
        writer.writerow([
            j.id,
            j.neutral_citation or '',
            j.title,
            j.court_level.value if j.court_level else '',
            j.date_decided.isoformat() if j.date_decided else '',
            j.is_published,
            j.source_url or '',
            j.created_at.isoformat() if j.created_at else ''
        ])
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=judgments.csv'}
    )


@bp.route('/ingest')
def ingest_control():
    """Ingestion control page."""
    from app.services.ingest_pipeline import AVAILABLE_SOURCES
    return render_template('admin/ingest.html',
        sources=AVAILABLE_SOURCES or ['kehakiman', 'industrial_court']
    )


@bp.route('/api/ingest/trigger', methods=['POST'])
def trigger_ingest():
    """Trigger ingestion task."""
    data = request.get_json()
    source = data.get('source')
    limit = data.get('limit', 100)
    dry_run = data.get('dry_run', False)

    from celery_worker import celery
    task = celery.send_task('ingest.judgment', args=[source, limit, dry_run])
    
    return jsonify({
        'status': 'ok',
        'task_id': task.id
    })


@bp.route('/users')
def users_manage():
    """User management page."""
    page = request.args.get('page', 1, type=int)
    role_filter = request.args.get('role', '')
    plan_filter = request.args.get('plan', '')

    query = User.query

    if role_filter:
        try:
            role = UserRole[role_filter.upper()]
            query = query.filter_by(role=role)
        except KeyError:
            pass

    if plan_filter:
        query = query.join(Subscription).filter(Subscription.plan == plan_filter)

    paginated = query.order_by(desc(User.created_at)).paginate(
        page=page, per_page=50
    )

    return render_template('admin/users.html',
        users=paginated.items,
        paginated=paginated,
        roles=[r.name for r in UserRole],
        plans=['starter', 'professional', 'firm']
    )


@bp.route('/users/<int:user_id>/verify', methods=['POST'])
def verify_user(user_id):
    """Mark user as verified lawyer."""
    user = User.query.get_or_404(user_id)
    user.is_verified = True
    db.session.commit()
    flash(f'{user.email} marked as verified.', 'success')
    return redirect(url_for('admin.users_manage'))


@bp.route('/users/<int:user_id>/ban', methods=['POST'])
def ban_user(user_id):
    """Ban a user."""
    user = User.query.get_or_404(user_id)
    user.is_active = False
    db.session.commit()
    flash(f'{user.email} has been banned.', 'success')
    return redirect(url_for('admin.users_manage'))


@bp.route('/judges')
def judges_manage():
    """Judge management page."""
    page = request.args.get('page', 1, type=int)
    court_level = request.args.get('court_level', '')

    query = Judge.query

    if court_level:
        query = query.filter_by(court_level=court_level)

    paginated = query.order_by(Judge.full_name).paginate(
        page=page, per_page=50
    )

    return render_template('admin/judges.html',
        judges=paginated.items,
        paginated=paginated,
        court_levels=[cl.value for cl in CourtLevel]
    )


@bp.route('/judges/<int:judge_id>/recompute', methods=['POST'])
def recompute_judge_analytics(judge_id):
    """Trigger judge analytics recomputation."""
    judge = Judge.query.get_or_404(judge_id)
    
    from app.services.analytics_service import compute_judge_analytics
    from celery_worker import celery
    
    task = celery.send_task('analytics.compute_judge', args=[judge_id])
    
    flash(f'Analytics computation queued for {judge.full_name}.', 'success')
    return redirect(url_for('admin.judges_manage'))


@bp.route('/lawyers')
def lawyers_manage():
    """Lawyer management page."""
    page = request.args.get('page', 1, type=int)
    firm_id = request.args.get('firm_id', '')

    query = Lawyer.query

    if firm_id:
        query = query.filter_by(firm_id=firm_id)

    paginated = query.order_by(Lawyer.full_name).paginate(
        page=page, per_page=50
    )

    firms = LawFirm.query.all()

    return render_template('admin/lawyers.html',
        lawyers=paginated.items,
        paginated=paginated,
        firms=firms
    )


@bp.route('/health')
def system_health():
    """System health check page."""
    health_status = {
        'db': 'checking',
        'redis': 'checking',
        'celery': 'checking',
        'disk_usage': 'checking'
    }

    # DB check
    try:
        db.session.execute(text('SELECT 1'))
        health_status['db'] = 'ok'
    except Exception as e:
        health_status['db'] = f'error: {str(e)}'

    # Redis check
    try:
        from app.extensions import limiter
        if limiter and limiter.storage_uri:
            health_status['redis'] = 'ok'
        else:
            health_status['redis'] = 'not configured'
    except Exception as e:
        health_status['redis'] = f'error: {str(e)}'

    # Celery check (basic)
    try:
        from celery_worker import celery
        stats = celery.control.inspect().active()
        if stats:
            total_active = sum(len(v) for v in stats.values())
            health_status['celery'] = f'{total_active} tasks active'
        else:
            health_status['celery'] = 'no workers connected'
    except Exception as e:
        health_status['celery'] = f'error: {str(e)}'

    # Disk usage check
    try:
        raw_data_dir = '/data/raw'
        if os.path.exists(raw_data_dir):
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(raw_data_dir):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    total_size += os.path.getsize(fp)
            size_mb = total_size / (1024 * 1024)
            health_status['disk_usage'] = f'{size_mb:.2f} MB'
        else:
            health_status['disk_usage'] = 'data directory not found'
    except Exception as e:
        health_status['disk_usage'] = f'error: {str(e)}'

    # API key usage
    from app.models.user import ApiKey
    active_keys = ApiKey.query.filter_by(is_active=True).count()

    # Deployment info
    env_info = {
        'FLASK_ENV': os.environ.get('FLASK_ENV', 'development'),
        'RAILWAY_ENV': os.environ.get('RAILWAY_ENV', 'not set'),
        'DATABASE_URL': '***' if os.environ.get('DATABASE_URL') else 'not set'
    }

    return render_template('admin/health.html',
        health_status=health_status,
        active_api_keys=active_keys,
        env_info=env_info
    )
