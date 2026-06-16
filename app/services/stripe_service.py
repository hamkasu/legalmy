import logging
import stripe
from flask import current_app, url_for
from app.extensions import db
from app.models.user import Subscription, SubscriptionStatus
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class StripeService:
    """Stripe payment integration for LegalMY subscriptions."""

    def __init__(self):
        stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY')
        self.webhook_secret = current_app.config.get('STRIPE_WEBHOOK_SECRET')

    @staticmethod
    def get_plan_price_id(plan):
        """Get Stripe price ID for plan."""
        price_ids = {
            'starter': current_app.config.get('STRIPE_PRICE_STARTER'),
            'professional': current_app.config.get('STRIPE_PRICE_PROFESSIONAL'),
            'firm': current_app.config.get('STRIPE_PRICE_FIRM'),
        }
        return price_ids.get(plan)

    def create_checkout_session(self, user_id, plan):
        """Create Stripe Checkout session for subscription upgrade."""
        from app.models.user import User

        user = User.query.get(user_id)
        if not user:
            raise ValueError(f'User {user_id} not found')

        price_id = self.get_plan_price_id(plan)
        if not price_id:
            raise ValueError(f'Invalid plan: {plan}')

        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price': price_id,
                        'quantity': 1,
                    }
                ],
                mode='subscription',
                success_url=url_for('billing.checkout_success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=url_for('pricing.index', _external=True),
                customer_email=user.email,
                metadata={
                    'user_id': str(user.id),
                    'plan': plan,
                },
            )
            logger.info(f'Stripe checkout session created for user {user_id}, plan {plan}')
            return session.url
        except Exception as e:
            logger.error(f'Stripe checkout error: {e}')
            raise

    def handle_checkout_completed(self, session):
        """Handle checkout.session.completed webhook."""
        user_id = int(session['metadata'].get('user_id'))
        plan = session['metadata'].get('plan')
        stripe_subscription_id = session.get('subscription')

        try:
            from app.models.user import User

            user = User.query.get(user_id)
            if not user:
                logger.error(f'User {user_id} not found in checkout webhook')
                return False

            # Update subscription
            subscription = user.subscription
            if not subscription:
                subscription = Subscription(user=user)

            subscription.plan = plan
            subscription.status = SubscriptionStatus.ACTIVE
            subscription.stripe_subscription_id = stripe_subscription_id
            subscription.started_at = datetime.utcnow()

            # Set period end based on plan
            if plan == 'firm':
                subscription.current_period_end = datetime.utcnow() + timedelta(days=365)
            else:
                subscription.current_period_end = datetime.utcnow() + timedelta(days=30)

            db.session.add(subscription)
            db.session.commit()

            logger.info(f'Subscription activated for user {user_id}, plan {plan}')
            return True
        except Exception as e:
            logger.error(f'Error handling checkout completion: {e}')
            return False

    def handle_subscription_updated(self, stripe_subscription):
        """Handle customer.subscription.updated webhook."""
        try:
            stripe_subscription_id = stripe_subscription['id']
            subscription = Subscription.query.filter_by(
                stripe_subscription_id=stripe_subscription_id
            ).first()

            if not subscription:
                logger.warning(f'Subscription {stripe_subscription_id} not found')
                return False

            if stripe_subscription['status'] == 'active':
                subscription.status = SubscriptionStatus.ACTIVE
            elif stripe_subscription['status'] in ['past_due', 'unpaid']:
                subscription.status = SubscriptionStatus.PAST_DUE
            else:
                subscription.status = SubscriptionStatus.CANCELLED

            db.session.commit()
            logger.info(f'Subscription {stripe_subscription_id} updated')
            return True
        except Exception as e:
            logger.error(f'Error handling subscription update: {e}')
            return False

    def handle_subscription_deleted(self, stripe_subscription):
        """Handle customer.subscription.deleted webhook."""
        try:
            stripe_subscription_id = stripe_subscription['id']
            subscription = Subscription.query.filter_by(
                stripe_subscription_id=stripe_subscription_id
            ).first()

            if not subscription:
                logger.warning(f'Subscription {stripe_subscription_id} not found')
                return False

            subscription.status = SubscriptionStatus.CANCELLED
            subscription.current_period_end = datetime.utcnow()

            # Downgrade to free
            subscription.plan = 'free'

            db.session.commit()
            logger.info(f'Subscription {stripe_subscription_id} cancelled, downgraded to free')
            return True
        except Exception as e:
            logger.error(f'Error handling subscription deletion: {e}')
            return False
