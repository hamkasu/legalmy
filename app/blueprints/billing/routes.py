import logging
import stripe
from flask import Blueprint, request, jsonify, url_for, redirect, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.services.stripe_service import StripeService

bp = Blueprint('billing', __name__, url_prefix='/billing')
logger = logging.getLogger(__name__)
stripe_service = StripeService()


@bp.route('/checkout/success')
@login_required
def checkout_success():
    """Handle successful Stripe checkout."""
    session_id = request.args.get('session_id')
    if not session_id:
        flash('Invalid checkout session', 'danger')
        return redirect(url_for('auth.profile'))

    try:
        session = stripe.checkout.Session.retrieve(session_id)
        stripe_service.handle_checkout_completed(session)
        flash('Subscription upgraded successfully! You can now access all premium features.', 'success')
        return redirect(url_for('auth.profile'))
    except Exception as e:
        logger.error(f'Checkout success error: {e}')
        flash('Unable to confirm subscription. Please contact support.', 'danger')
        return redirect(url_for('auth.profile'))


@bp.route('/webhook', methods=['POST'])
def webhook():
    """Handle Stripe webhooks."""
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            stripe_service.webhook_secret
        )
    except ValueError as e:
        logger.error(f'Invalid webhook payload: {e}')
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError as e:
        logger.error(f'Invalid webhook signature: {e}')
        return jsonify({'error': 'Invalid signature'}), 400

    # Handle events
    if event['type'] == 'checkout.session.completed':
        stripe_service.handle_checkout_completed(event['data']['object'])
    elif event['type'] == 'customer.subscription.updated':
        stripe_service.handle_subscription_updated(event['data']['object'])
    elif event['type'] == 'customer.subscription.deleted':
        stripe_service.handle_subscription_deleted(event['data']['object'])

    return jsonify({'status': 'success'}), 200
