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
# Set RUNNING_LOG_PASSWORD environment variable, or use default for dev
_password = os.environ.get('RUNNING_LOG_PASSWORD', 'run')
PASSWORD_HASH = generate_password_hash(_password)
