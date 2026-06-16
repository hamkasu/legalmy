import pytest
from app import create_app, db


@pytest.fixture(scope='session')
def app():
    """Create and configure a test Flask application."""
    app = create_app('testing')

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture(scope='function')
def runner(app):
    """A test runner for the app's CLI."""
    return app.test_cli_runner()


@pytest.fixture(autouse=True)
def reset_db(app):
    """Reset the database for each test."""
    with app.app_context():
        db.create_all()
        yield
        db.session.remove()
        db.drop_all()
