"""Configuration for the Running Log web application."""

import os
from werkzeug.security import generate_password_hash

# Database URL - use environment variable or default to SQLite for local dev
DATABASE_URL = os.environ.get(
    'DATABASE_URL',
    'sqlite:///running_log.db'
)

# For PostgreSQL on PythonAnywhere, set DATABASE_URL to:
# postgresql://username:password@username-123.postgres.pythonanywhere-services.com/dbname

# Secret key for session management
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Password hash for authentication
# REQUIRED: Set RUNNING_LOG_PASSWORD environment variable
_password = os.environ.get('RUNNING_LOG_PASSWORD')
if not _password:
    raise ValueError('RUNNING_LOG_PASSWORD environment variable must be set')
PASSWORD_HASH = generate_password_hash(_password)

# Strava API configuration
# Get these from https://www.strava.com/settings/api
STRAVA_CLIENT_ID = os.environ.get('STRAVA_CLIENT_ID')
STRAVA_CLIENT_SECRET = os.environ.get('STRAVA_CLIENT_SECRET')
STRAVA_REDIRECT_URI = os.environ.get(
    'STRAVA_REDIRECT_URI',
    'http://localhost:5001/strava/callback'
)
