import os
from datetime import timedelta

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True

    # Flask-Login
    REMEMBER_COOKIE_DURATION = timedelta(days=30)
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'

    # Flask-Mail
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.brevo.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', True)
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@legalmy.com.my')

    # Anthropic API
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
    ANTHROPIC_MODEL = 'claude-sonnet-4-6'

    # Stripe
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')

    # Redis
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

    # Celery
    CELERY_BROKER_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    CELERY_ENABLE_UTC = True

    # Subscription Plans
    PLANS = {
        'free': {
            'name': 'Free',
            'price_myr': 0,
            'searches_per_day': 10,
            'ai_queries_per_month': 0,
            'judgment_exports': 0,
            'alerts': 1,
            'judge_analytics': False,
            'lawyer_analytics': False,
        },
        'starter': {
            'name': 'Starter',
            'price_myr': 99,
            'stripe_price_id': 'price_starter_myr',
            'searches_per_day': -1,
            'ai_queries_per_month': 50,
            'judgment_exports': 50,
            'alerts': 5,
            'judge_analytics': True,
            'lawyer_analytics': False,
        },
        'professional': {
            'name': 'Professional',
            'price_myr': 299,
            'stripe_price_id': 'price_professional_myr',
            'searches_per_day': -1,
            'ai_queries_per_month': 500,
            'judgment_exports': -1,
            'alerts': 25,
            'judge_analytics': True,
            'lawyer_analytics': True,
        },
        'firm': {
            'name': 'Firm',
            'price_myr': 999,
            'stripe_price_id': 'price_firm_myr',
            'searches_per_day': -1,
            'ai_queries_per_month': -1,
            'judgment_exports': -1,
            'alerts': -1,
            'judge_analytics': True,
            'lawyer_analytics': True,
            'seats': 10,
            'api_access': True,
        },
    }


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'postgresql://postgres:postgres@localhost:5432/legalmy_dev'
    )
    SQLALCHEMY_ECHO = True
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False


class StagingConfig(Config):
    """Staging configuration"""
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SESSION_COOKIE_SECURE = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    PROPAGATE_EXCEPTIONS = True
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'staging': StagingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}
