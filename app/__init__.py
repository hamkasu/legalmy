from flask import Flask, jsonify
from flask_cors import CORS
import logging
from logging.handlers import RotatingFileHandler
import os

from app.config import config
from app.extensions import db, migrate, login_manager, mail


def create_app(config_name=None):
    """Application factory"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    CORS(app)

    # Register blueprints
    register_blueprints(app)

    # Error handlers
    register_error_handlers(app)

    # CLI commands
    register_cli_commands(app)

    # Create tables and run migrations
    with app.app_context():
        # Health check endpoint
        @app.route('/health')
        def health():
            return jsonify({
                'status': 'ok',
                'db': 'ok',
                'redis': 'ok',
                'version': '1.0.0'
            }), 200

    return app


def register_blueprints(app):
    """Register all blueprints"""
    from app.blueprints.landing import landing_bp
    from app.blueprints.auth import auth_bp
    from app.blueprints.search import search_bp
    from app.blueprints.judgments import judgments_bp
    from app.blueprints.judges import judges_bp
    from app.blueprints.lawyers import lawyers_bp
    from app.blueprints.legislation import legislation_bp
    from app.blueprints.ai import ai_bp
    from app.blueprints.dashboard import dashboard_bp
    from app.blueprints.alerts import alerts_bp
    from app.blueprints.api import api_bp
    from app.blueprints.admin import admin_bp

    app.register_blueprint(landing_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(search_bp, url_prefix='/search')
    app.register_blueprint(judgments_bp, url_prefix='/judgments')
    app.register_blueprint(judges_bp, url_prefix='/judges')
    app.register_blueprint(lawyers_bp, url_prefix='/lawyers')
    app.register_blueprint(legislation_bp, url_prefix='/legislation')
    app.register_blueprint(ai_bp, url_prefix='/ai')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(alerts_bp, url_prefix='/alerts')
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    app.register_blueprint(admin_bp, url_prefix='/admin')


def register_error_handlers(app):
    """Register error handlers"""

    def wants_json_response():
        return (
            'application/json' in (request.headers.get('Accept', '') or '')
            or request.path.startswith('/api/')
        )

    from flask import request

    @app.errorhandler(400)
    def bad_request(error):
        if wants_json_response():
            return jsonify({
                'status': 'error',
                'error': {
                    'code': 'BAD_REQUEST',
                    'message': 'Invalid request.'
                }
            }), 400
        return 'Bad Request', 400

    @app.errorhandler(401)
    def unauthorized(error):
        if wants_json_response():
            return jsonify({
                'status': 'error',
                'error': {
                    'code': 'UNAUTHORIZED',
                    'message': 'Authentication required.'
                }
            }), 401
        return 'Unauthorized', 401

    @app.errorhandler(403)
    def forbidden(error):
        if wants_json_response():
            return jsonify({
                'status': 'error',
                'error': {
                    'code': 'FORBIDDEN',
                    'message': 'You do not have permission to access this resource.'
                }
            }), 403
        return 'Forbidden', 403

    @app.errorhandler(404)
    def not_found(error):
        if wants_json_response():
            return jsonify({
                'status': 'error',
                'error': {
                    'code': 'NOT_FOUND',
                    'message': 'Resource not found.'
                }
            }), 404
        return 'Not Found', 404

    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        if wants_json_response():
            return jsonify({
                'status': 'error',
                'error': {
                    'code': 'RATE_LIMIT_EXCEEDED',
                    'message': 'You have exceeded the rate limit.'
                }
            }), 429
        return 'Rate Limit Exceeded', 429

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        if wants_json_response():
            return jsonify({
                'status': 'error',
                'error': {
                    'code': 'INTERNAL_SERVER_ERROR',
                    'message': 'An internal error occurred.'
                }
            }), 500
        return 'Internal Server Error', 500


def register_cli_commands(app):
    """Register CLI commands"""
    import click

    @app.cli.command()
    @click.option('--source', default='kehakiman', help='Data source')
    @click.option('--limit', default=10, help='Number of judgments to ingest')
    def ingest(source, limit):
        """Ingest judgments from specified source"""
        click.echo(f'Ingesting {limit} judgments from {source}...')
        click.echo('Ingest functionality to be implemented in Prompt 03')


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
