from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models.alert import SavedSearch, Alert, AlertFrequency
from app.models.judgment import Judgment

bp = Blueprint('alerts', __name__, template_folder='templates')


@bp.route('/')
@login_required
def index():
    """Manage user's saved searches and alerts."""
    saved_searches = SavedSearch.query.filter_by(user_id=current_user.id).all()

    return render_template('alerts/index.html', saved_searches=saved_searches)


@bp.route('/create', methods=['POST'])
@login_required
def create_alert():
    """Create a new saved search alert."""
    data = request.get_json()
    name = data.get('name', '').strip()
    query_json = data.get('query_json', {})
    frequency = data.get('frequency', 'daily')

    if not name:
        return jsonify({'error': 'Name required'}), 400

    saved_search = SavedSearch(
        user_id=current_user.id,
        name=name,
        query_json=query_json
    )
    db.session.add(saved_search)
    db.session.flush()

    alert = Alert(
        saved_search_id=saved_search.id,
        frequency=AlertFrequency[frequency.upper()],
        is_active=True,
        delivery_email=current_user.email
    )
    db.session.add(alert)
    db.session.commit()

    return jsonify({'status': 'success', 'alert_id': alert.id})


@bp.route('/<int:alert_id>/toggle', methods=['POST'])
@login_required
def toggle_alert(alert_id):
    """Toggle alert active status."""
    alert = Alert.query.get_or_404(alert_id)

    # Verify ownership
    if alert.saved_search.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    alert.is_active = not alert.is_active
    db.session.commit()

    return jsonify({'status': 'success', 'is_active': alert.is_active})


@bp.route('/<int:alert_id>/delete', methods=['POST'])
@login_required
def delete_alert(alert_id):
    """Delete an alert."""
    alert = Alert.query.get_or_404(alert_id)

    # Verify ownership
    if alert.saved_search.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    saved_search_id = alert.saved_search_id
    db.session.delete(alert)

    # Delete saved search if no other alerts
    saved_search = SavedSearch.query.get(saved_search_id)
    if saved_search and not saved_search.alerts.count():
        db.session.delete(saved_search)

    db.session.commit()

    return jsonify({'status': 'success'})
