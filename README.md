# Running Log

A Flask web app to track daily runs against a 50km ultra marathon training plan.

**Live:** https://steeetown.pythonanywhere.com

## Features

- Log runs with distance, duration, and pace
- Training plan with daily targets
- Dashboard with stats and progress charts
- Strava integration for automatic sync
- Public dashboard view

## Local Development

```bash
cd /Users/dancullum/running-log
pip install -r webapp/requirements.txt

# Run the app (port 5001)
RUNNING_LOG_PASSWORD=yourpassword python -m webapp.app
```

## Environment Variables

- `RUNNING_LOG_PASSWORD` (required) - Authentication password
- `DATABASE_URL` - Database connection (default: SQLite)
- `SECRET_KEY` - Flask session secret
- `STRAVA_CLIENT_ID` - Strava API credentials
- `STRAVA_CLIENT_SECRET`
- `STRAVA_REDIRECT_URI`

## Deployment

Hosted on PythonAnywhere with PostgreSQL database.
