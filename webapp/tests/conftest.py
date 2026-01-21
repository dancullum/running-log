"""
Pytest configuration and fixtures for Running Log tests.

WHAT IS THIS FILE?
------------------
conftest.py is a special pytest file that provides "fixtures" - reusable
pieces of test setup that can be shared across all test files.

Think of fixtures as the "ingredients" your tests need:
- A test database
- A test client to make HTTP requests
- A logged-in user session
- Sample data

WHY FIXTURES?
-------------
Without fixtures, every test would need to repeat setup code:

    def test_something():
        app = create_app()
        app.config['TESTING'] = True
        client = app.test_client()
        # ... finally do the actual test

With fixtures, tests are clean:

    def test_something(client):
        # client is automatically provided!
        response = client.get('/dashboard')
"""

import pytest
from datetime import date, timedelta

from webapp.app import create_app
from webapp.models import db, Run, TrainingPlan


@pytest.fixture
def app():
    """
    Create a test application instance.

    This fixture:
    1. Creates a Flask app with test configuration
    2. Uses an in-memory SQLite database (fast, isolated)
    3. Creates all database tables
    4. Yields the app for tests to use
    5. Cleans up after the test

    The 'yield' keyword is important - code before yield runs BEFORE
    the test, code after yield runs AFTER the test (cleanup).
    """
    # Create app with test config
    test_app = create_app()
    test_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',  # In-memory DB
        'WTF_CSRF_ENABLED': False,  # Disable CSRF for testing forms
    })

    # Create tables in the test database
    with test_app.app_context():
        db.create_all()
        yield test_app  # This is where the test runs
        db.drop_all()   # Cleanup after test


@pytest.fixture
def client(app):
    """
    Create a test client for making HTTP requests.

    The test client lets you simulate browser requests without
    running a real server:

        response = client.get('/dashboard')
        response = client.post('/login', data={'password': 'xxx'})

    This fixture depends on the 'app' fixture - pytest automatically
    calls 'app' first and passes the result here.
    """
    return app.test_client()


@pytest.fixture
def authenticated_client(client):
    """
    Create a test client that's already logged in.

    Many tests need an authenticated user. Instead of repeating
    login code in every test, this fixture does it once.

    Usage in tests:
        def test_home_page(authenticated_client):
            response = authenticated_client.get('/')
            assert response.status_code == 200
    """
    # Log in with the default test password
    client.post('/login', data={'password': 'runninglog2026'})
    return client


@pytest.fixture
def sample_training_plan(app):
    """
    Create sample training plan data for testing.

    This fixture populates the database with a week of training data.
    Tests that need training plan data can use this fixture.

    Returns a dict with the created data for assertions.
    """
    with app.app_context():
        today = date.today()
        entries = []

        # Create 7 days of training plan
        for i in range(7):
            plan_date = today + timedelta(days=i)
            # Alternate between different distances
            target = 5.0 if i % 2 == 0 else 8.0

            entry = TrainingPlan(date=plan_date, target_distance=target)
            db.session.add(entry)
            entries.append({'date': plan_date, 'target': target})

        db.session.commit()

        return entries


@pytest.fixture
def sample_runs(app):
    """
    Create sample run data for testing.

    Returns a list of the created runs for use in assertions.
    """
    with app.app_context():
        today = date.today()
        runs = []

        # Create 3 past runs
        for i in range(1, 4):
            run_date = today - timedelta(days=i)
            distance = 5.0 + i  # 6, 7, 8 km

            run = Run(date=run_date, distance=distance)
            db.session.add(run)
            runs.append({'date': run_date, 'distance': distance})

        db.session.commit()

        return runs
