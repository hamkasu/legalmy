import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.alert import SavedSearch, Alert
from app.models.judgment import Judgment
from app.config import PLANS
from datetime import datetime, timedelta
import json

bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')
logger = logging.getLogger(__name__)


@bp.route('/')
@login_required
def index():
    """Main subscriber dashboard."""
    try:
        subscription = current_user.subscriptions.first()
        plan_info = PLANS.get(subscription.plan, {}) if subscription else PLANS['free']

        # Recent searches (last 5 SavedSearch records)
        recent_searches = SavedSearch.query.filter_by(user_id=current_user.id).order_by(
            SavedSearch.created_at.desc()
        ).limit(5).all()

        # Active alerts
        active_alerts = Alert.query.join(SavedSearch).filter(
            SavedSearch.user_id == current_user.id,
            Alert.is_active == True
        ).order_by(Alert.last_sent.desc()).limit(10).all()

        # AI usage this month (placeholder - would aggregate from ai_usage table)
        ai_usage = {
            'case_analyser': 12,
            'summariser': 8,
            'argument_generator': 5,
            'counsel_research': 3,
            'timeline_builder': 2,
            'explain_law': 4
        }
        total_ai_usage = sum(ai_usage.values())
        monthly_ai_limit = plan_info.get('ai_queries_per_month', 0)

        # Preferences for personalization
        preferences = current_user.preferences if hasattr(current_user, 'preferences') else {}

        return render_template(
            'dashboard/index.html',
            subscription=subscription,
            plan_info=plan_info,
            recent_searches=recent_searches,
            active_alerts=active_alerts,
            ai_usage=ai_usage,
            total_ai_usage=total_ai_usage,
            monthly_ai_limit=monthly_ai_limit,
            preferences=preferences
        )
    except Exception as e:
        import traceback
        logger.error(f'Dashboard error: {e}')
        logger.error(traceback.format_exc())
        flash('Failed to load dashboard', 'danger')
        return redirect(url_for('landing.index'))


@bp.route('/alerts')
@login_required
def alerts_list():
    """Manage saved searches and alerts."""
    try:
        page = request.args.get('page', 1, type=int)

        # Get saved searches with their alerts
        saved_searches = SavedSearch.query.filter_by(user_id=current_user.id).order_by(
            SavedSearch.created_at.desc()
        ).paginate(page=page, per_page=20)

        return render_template(
            'dashboard/alerts.html',
            saved_searches=saved_searches.items,
            total=saved_searches.total,
            page=page,
            pages=saved_searches.pages
        )
    except Exception as e:
        logger.error(f'Alerts list error: {e}')
        flash('Failed to load alerts', 'danger')
        return redirect(url_for('dashboard.index'))


@bp.route('/alerts/create', methods=['POST'])
@login_required
def create_alert():
    """Create new saved search and alert from current search params."""
    try:
        data = request.get_json() if request.is_json else request.form.to_dict()

        name = data.get('name', '').strip()
        query = data.get('query', '').strip()
        filters = data.get('filters', {})
        frequency = data.get('frequency', 'daily')

        if not name or not query:
            return jsonify({'error': 'Name and query required'}), 400

        # Create SavedSearch
        saved_search = SavedSearch(
            user_id=current_user.id,
            name=name,
            query_json={
                'query': query,
                'filters': filters
            }
        )
        db.session.add(saved_search)
        db.session.flush()

        # Create Alert
        alert = Alert(
            saved_search_id=saved_search.id,
            frequency=frequency,
            is_active=True,
            last_sent=datetime.utcnow()
        )
        db.session.add(alert)
        db.session.commit()

        logger.info(f'Alert created for user {current_user.id}: {name}')
        return jsonify({'status': 'success', 'alert_id': alert.id}), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f'Create alert error: {e}')
        return jsonify({'error': str(e)}), 500


@bp.route('/alerts/<int:alert_id>/pause', methods=['PUT'])
@login_required
def pause_alert(alert_id):
    """Toggle alert active status."""
    try:
        alert = Alert.query.join(SavedSearch).filter(
            Alert.id == alert_id,
            SavedSearch.user_id == current_user.id
        ).first_or_404()

        alert.is_active = not alert.is_active
        db.session.commit()

        status = 'paused' if not alert.is_active else 'resumed'
        logger.info(f'Alert {alert_id} {status} for user {current_user.id}')

        return jsonify({'status': 'success', 'is_active': alert.is_active}), 200
    except Exception as e:
        logger.error(f'Pause alert error: {e}')
        return jsonify({'error': str(e)}), 500


@bp.route('/alerts/<int:alert_id>', methods=['DELETE'])
@login_required
def delete_alert(alert_id):
    """Delete saved search and its alert."""
    try:
        alert = Alert.query.join(SavedSearch).filter(
            Alert.id == alert_id,
            SavedSearch.user_id == current_user.id
        ).first_or_404()

        saved_search = alert.saved_search
        db.session.delete(alert)
        db.session.delete(saved_search)
        db.session.commit()

        logger.info(f'Alert {alert_id} deleted for user {current_user.id}')
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f'Delete alert error: {e}')
        return jsonify({'error': str(e)}), 500


@bp.route('/saved-cases')
@login_required
def saved_cases():
    """View bookmarked judgments."""
    try:
        page = request.args.get('page', 1, type=int)
        sort = request.args.get('sort', 'date', type=str)

        # Query bookmarked judgments (placeholder - would use relationship)
        bookmarked = Judgment.query.limit(20).paginate(page=page, per_page=20)

        return render_template(
            'dashboard/saved_cases.html',
            bookmarked=bookmarked.items,
            total=bookmarked.total,
            page=page,
            pages=bookmarked.pages,
            sort=sort
        )
    except Exception as e:
        logger.error(f'Saved cases error: {e}')
        flash('Failed to load saved cases', 'danger')
        return redirect(url_for('dashboard.index'))


@bp.route('/saved-cases/export')
@login_required
def export_saved_cases():
    """Export bookmarked judgments as CSV."""
    try:
        # Check subscription plan
        if current_user.subscription.plan == 'free':
            return jsonify({'error': 'Upgrade required for CSV export'}), 402

        # Would generate CSV file
        return jsonify({'status': 'success', 'message': 'Export feature coming soon'}), 200
    except Exception as e:
        logger.error(f'Export error: {e}')
        return jsonify({'error': str(e)}), 500

