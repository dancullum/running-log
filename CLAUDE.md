# Running Log

A Flask web app for tracking runs against a 50km ultra marathon training plan.

Live at: https://steeetown.pythonanywhere.com

## Commands

```bash
# Run locally (port 5001)
RUNNING_LOG_PASSWORD=yourpassword python -m webapp.app

# Run tests
RUNNING_LOG_PASSWORD=runninglog2026 pytest webapp/tests/

# Run specific test file
pytest webapp/tests/test_routes.py -v

# Database migrations (after changing models)
RUNNING_LOG_PASSWORD=test FLASK_APP=webapp.app flask db migrate -m "Description of change"
RUNNING_LOG_PASSWORD=test FLASK_APP=webapp.app flask db upgrade
```

## Environment Variables

Required:
- `RUNNING_LOG_PASSWORD` - Password for web authentication

Optional:
- `DATABASE_URL` - Database connection string (default: SQLite)
- `SECRET_KEY` - Flask session key (default: dev key)
- `STRAVA_CLIENT_ID` - Strava API client ID
- `STRAVA_CLIENT_SECRET` - Strava API secret
- `STRAVA_REDIRECT_URI` - OAuth callback URL

## Project Structure

```
webapp/
├── app.py              # Flask factory, template filters
├── config.py           # Environment-based configuration
├── models.py           # SQLAlchemy models (Run, StravaToken, TrainingPlan)
├── routes/
│   ├── auth.py         # Login/logout
│   ├── main.py         # Home, weekly view
│   ├── runs.py         # CRUD for runs
│   ├── dashboard.py    # Stats and charts
│   └── strava.py       # Strava OAuth and sync
├── services/
│   └── strava.py       # Strava API client
├── templates/          # Jinja2 templates
└── tests/              # Pytest tests

migrations/             # Flask-Migrate database migrations
wsgi.py                 # PythonAnywhere entry point
instance/               # Local SQLite database
```

## Models

- **Run** - date, distance, duration, pace, strava_activity_id, source
- **TrainingPlan** - date, target_distance
- **StravaToken** - OAuth tokens for Strava integration

## Key Patterns

- Flask app factory pattern in `create_app()`
- Blueprints for route organization
- Template filters: `format_date`, `format_date_short`, `format_distance`
- Context processor injects `strava_connected` into all templates
- Password authentication (single user, no registration)

## Strava Integration

### What's Implemented
- **OAuth flow**: Connect/disconnect via `/strava/connect` and `/strava/disconnect`
- **Token management**: Stores tokens in `StravaToken` model, auto-refreshes expired tokens
- **Activity sync**: Fetches runs from Strava API, imports to database with duplicate detection
- **Manual sync**: Button in header triggers `/strava/sync` (syncs last 30 days)
- **UI indicators**: Strava icon on synced runs, connect/sync buttons in header

### Routes (`webapp/routes/strava.py`)
- `GET /strava/connect` - Redirects to Strava OAuth (requires login)
- `GET /strava/callback` - Handles OAuth callback, stores token, triggers initial sync
- `POST /strava/disconnect` - Removes Strava connection
- `POST /strava/sync` - Manual sync trigger

### Service (`webapp/services/strava.py`)
- `get_authorization_url()` - Builds OAuth URL
- `exchange_code_for_token(code)` - Exchanges auth code for tokens
- `refresh_access_token(token)` - Refreshes expired token
- `fetch_recent_activities(token, days)` - Fetches runs from Strava API
- `sync_activities_to_db(activities)` - Imports to DB, skips duplicates
- `sync_from_strava(days)` - Full sync orchestration

### Potential Enhancements
- Webhook support for automatic sync when activities added on Strava
- Settings page to manage Strava connection
- Periodic/scheduled sync (currently manual only)

## Database Migrations

Uses Flask-Migrate (Alembic) to track schema changes.

**Workflow for schema changes:**
1. Modify models in `webapp/models.py`
2. Generate migration: `flask db migrate -m "Description"`
3. Review the generated file in `migrations/versions/`
4. Apply locally: `flask db upgrade`
5. Commit migration file to git
6. On PythonAnywhere after pull: `flask db upgrade`

**Common commands:**
- `flask db migrate` - Auto-generate migration from model changes
- `flask db upgrade` - Apply pending migrations
- `flask db downgrade` - Revert last migration
- `flask db current` - Show current revision

## Deployment

Hosted on PythonAnywhere. Uses SQLite in both local and production.

**After pulling changes to PythonAnywhere:**
```bash
cd ~/running-log
source venv/bin/activate
pip install -r webapp/requirements.txt  # If dependencies changed
RUNNING_LOG_PASSWORD=xxx FLASK_APP=webapp.app flask db upgrade  # If migrations exist
```
Then reload the web app.
