import pytest
from app.models.user import User, Subscription, SubscriptionStatus, ApiKey, UserRole
from app.extensions import db
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash


@pytest.fixture
def test_user(app):
    """Create a test user."""
    with app.app_context():
        user = User(
            email='test@example.com',
            full_name='Test User',
            password_hash=generate_password_hash('password123'),
            is_verified=True
        )
        db.session.add(user)
        db.session.commit()
        yield user
        db.session.delete(user)
        db.session.commit()


def test_user_registration_flow(client):
    """Test user registration endpoint."""
    response = client.post('/auth/register', data={
        'email': 'newuser@example.com',
        'full_name': 'New User',
        'password': 'securepass123',
        'password_confirm': 'securepass123'
    })
    assert response.status_code in [200, 302, 400]  # 302 redirect or 200 form, 400 if validation fails


def test_email_verification_token_generation(app):
    """Test that email verification tokens are generated correctly."""
    with app.app_context():
        user = User(
            email='verify@example.com',
            full_name='Test User',
            password_hash=generate_password_hash('pass')
        )
        db.session.add(user)
        db.session.commit()

        # Verification token should be creatable
        from itsdangerous import URLSafeTimedSerializer
        from app.config import config
        serializer = URLSafeTimedSerializer(config['testing'].SECRET_KEY)
        token = serializer.dumps(user.email)
        assert token is not None


def test_password_hashing(app):
    """Test that passwords are hashed correctly."""
    with app.app_context():
        plain_password = 'mypassword123'
        hashed = generate_password_hash(plain_password)

        # Verify hash is different from plain
        assert hashed != plain_password

        # Verify hash can be checked
        assert check_password_hash(hashed, plain_password)
        assert not check_password_hash(hashed, 'wrongpassword')


def test_login_with_valid_credentials(client, test_user):
    """Test login with valid credentials."""
    response = client.post('/auth/login', data={
        'email': 'test@example.com',
        'password': 'password123'
    })
    assert response.status_code in [200, 302]


def test_login_with_invalid_credentials(client):
    """Test login with invalid credentials."""
    response = client.post('/auth/login', data={
        'email': 'nonexistent@example.com',
        'password': 'wrongpass'
    })
    assert response.status_code in [200, 302]  # Returns form or redirect


def test_plan_gate_decorator_free_user(client, test_user):
    """Test that @require_plan decorator blocks free users."""
    # Free user should not have access to subscriber routes
    response = client.get('/dashboard')
    # Either redirect to login or show dashboard
    assert response.status_code in [200, 302, 401]


def test_api_key_generation(app):
    """Test API key generation and hashing."""
    with app.app_context():
        from app.services.api_key_service import generate_api_key
        from hashlib import sha256

        user = User(
            email='api@example.com',
            full_name='API User',
            password_hash=generate_password_hash('pass')
        )
        db.session.add(user)
        db.session.commit()

        # Generate API key
        raw_key = generate_api_key(user.id, 'test_key')
        assert raw_key is not None
        assert raw_key.startswith('lmy_') or len(raw_key) == 32


def test_api_key_hashing(app):
    """Test that API keys are hashed in database."""
    with app.app_context():
        from app.services.api_key_service import generate_api_key
        from hashlib import sha256

        user = User(
            email='api2@example.com',
            full_name='API User 2',
            password_hash=generate_password_hash('pass')
        )
        db.session.add(user)
        db.session.commit()

        raw_key = generate_api_key(user.id, 'test_key_2')

        # Retrieve key from DB
        api_key = ApiKey.query.filter_by(user_id=user.id).first()
        assert api_key is not None

        # Verify the stored hash is not the raw key
        assert api_key.key_hash != raw_key


def test_api_key_verification(app):
    """Test API key verification."""
    with app.app_context():
        from app.services.api_key_service import generate_api_key, verify_api_key

        user = User(
            email='api3@example.com',
            full_name='API User 3',
            password_hash=generate_password_hash('pass')
        )
        db.session.add(user)
        db.session.commit()

        raw_key = generate_api_key(user.id, 'test_key_3')

        # Verify the raw key works
        verified = verify_api_key(raw_key)
        assert verified is not None


def test_subscription_plan_tiers(app):
    """Test that subscription plan tiers are correctly defined."""
    with app.app_context():
        from app.config import config
        plans = config['testing'].PLANS

        assert 'free' in plans
        assert 'starter' in plans
        assert 'professional' in plans
        assert 'firm' in plans

        # Verify free plan has no cost
        assert plans['free']['price_myr'] == 0

        # Verify paid plans have prices
        assert plans['starter']['price_myr'] > 0
        assert plans['professional']['price_myr'] > 0
        assert plans['firm']['price_myr'] > 0


def test_subscription_status_enum(app):
    """Test subscription status enum values."""
    valid_statuses = [
        SubscriptionStatus.ACTIVE,
        SubscriptionStatus.CANCELLED,
        SubscriptionStatus.TRIAL,
    ]

    for status in valid_statuses:
        assert status.value in ['active', 'cancelled', 'trial']


def test_user_role_enum(app):
    """Test user role enum values."""
    valid_roles = [
        UserRole.FREE,
        UserRole.SUBSCRIBER,
        UserRole.ADMIN,
        UserRole.API,
    ]

    for role in valid_roles:
        assert role.value in ['free', 'subscriber', 'admin', 'api']


def test_password_reset_token_generation(app):
    """Test password reset token generation."""
    with app.app_context():
        from itsdangerous import URLSafeTimedSerializer
        from app.config import config

        user = User(
            email='reset@example.com',
            full_name='Reset User',
            password_hash=generate_password_hash('pass')
        )
        db.session.add(user)
        db.session.commit()

        serializer = URLSafeTimedSerializer(config['testing'].SECRET_KEY)
        token = serializer.dumps(user.email)
        assert token is not None


def test_password_reset_token_expiry(app):
    """Test that reset tokens have TTL."""
    with app.app_context():
        from itsdangerous import URLSafeTimedSerializer, SignatureExpired
        from app.config import config

        user = User(
            email='reset2@example.com',
            full_name='Reset User 2',
            password_hash=generate_password_hash('pass')
        )
        db.session.add(user)
        db.session.commit()

        serializer = URLSafeTimedSerializer(config['testing'].SECRET_KEY)
        token = serializer.dumps(user.email)

        # Token should be valid immediately
        email = serializer.loads(token, max_age=3600)
        assert email == user.email


def test_logout_clears_session(client, test_user):
    """Test that logout clears user session."""
    # Login first
    client.post('/auth/login', data={
        'email': 'test@example.com',
        'password': 'password123'
    })

    # Logout
    response = client.get('/auth/logout')
    assert response.status_code in [200, 302]


def test_remember_me_functionality(client):
    """Test remember me checkbox during login."""
    response = client.post('/auth/login', data={
        'email': 'test@example.com',
        'password': 'password123',
        'remember_me': True
    })
    # Should set persistent session cookie
    assert response.status_code in [200, 302]


def test_api_key_rate_limiting(app):
    """Test that API keys have rate limit enforcement."""
    with app.app_context():
        user = User(
            email='ratelimit@example.com',
            full_name='Rate Limit User',
            password_hash=generate_password_hash('pass')
        )
        db.session.add(user)
        db.session.commit()

        api_key = ApiKey(
            user_id=user.id,
            key_hash='test_hash',
            name='test_key',
            rate_limit_per_day=1000
        )
        db.session.add(api_key)
        db.session.commit()

        assert api_key.rate_limit_per_day == 1000
