import logging
import hashlib
import secrets
from app.extensions import db
from app.models.user import ApiKey

logger = logging.getLogger(__name__)


class ApiKeyService:
    """API Key management service."""

    @staticmethod
    def generate_api_key(user_id, name):
        """Generate new API key. Returns raw key (shown once) and hash for storage."""
        try:
            # Generate random 32-byte key
            raw_key = secrets.token_urlsafe(32)
            # Prefix with lmy_
            prefixed_key = f"lmy_{raw_key}"

            # Hash for storage
            key_hash = hashlib.sha256(prefixed_key.encode()).hexdigest()

            # Store in DB
            api_key = ApiKey(
                user_id=user_id,
                key_hash=key_hash,
                name=name,
                is_active=True
            )
            db.session.add(api_key)
            db.session.commit()

            logger.info(f'API key generated for user {user_id}: {name}')
            # Return raw key (only shown once to user)
            return prefixed_key, api_key.id
        except Exception as e:
            logger.error(f'Failed to generate API key: {e}')
            raise

    @staticmethod
    def verify_api_key(raw_key):
        """Verify API key and return ApiKey record."""
        try:
            key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
            api_key = ApiKey.query.filter_by(
                key_hash=key_hash,
                is_active=True
            ).first()

            if api_key:
                # Update last_used
                from datetime import datetime
                api_key.last_used = datetime.utcnow()
                db.session.commit()

            return api_key
        except Exception as e:
            logger.error(f'Failed to verify API key: {e}')
            return None

    @staticmethod
    def revoke_api_key(api_key_id, user_id):
        """Revoke (soft delete) an API key."""
        try:
            api_key = ApiKey.query.filter_by(
                id=api_key_id,
                user_id=user_id
            ).first()

            if not api_key:
                return False

            api_key.is_active = False
            db.session.commit()

            logger.info(f'API key {api_key_id} revoked for user {user_id}')
            return True
        except Exception as e:
            logger.error(f'Failed to revoke API key: {e}')
            return False

    @staticmethod
    def list_api_keys(user_id):
        """List all API keys for a user (without exposing key_hash)."""
        return ApiKey.query.filter_by(user_id=user_id).all()

    @staticmethod
    def get_usage_today(user_id):
        """Get API request usage today for a user."""
        from datetime import datetime, timedelta
        from app.models.judgment import Judgment

        # Would query from api_usage table in real implementation
        # For now, return placeholder
        return 47

    @staticmethod
    def get_usage_limit(user_id):
        """Get daily API rate limit based on subscription plan."""
        from app.models.user import User

        user = User.query.get(user_id)
        if not user or not user.subscription:
            return 0

        plan = user.subscription.plan
        # Only Firm plan has API access with 1000 requests/day
        if plan == 'firm':
            return 1000
        return 0
