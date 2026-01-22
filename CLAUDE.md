# Running Log

A Flask web app for tracking runs against a 50km ultra marathon training plan.

Live at: https://steeetown.pythonanywhere.com

## Commands

```bash
# Run locally (port 5001)
RUNNING_LOG_PASSWORD=yourpassword python -m webapp.app

# Run tests
pytest webapp/tests/

# Run specific test file
pytest webapp/tests/test_routes.py -v
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

## Deployment

Hosted on PythonAnywhere. Uses PostgreSQL in production, SQLite locally.
