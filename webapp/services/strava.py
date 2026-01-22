"""Strava API client and sync service."""

import time
from datetime import datetime, timedelta
from decimal import Decimal

import requests

from webapp import config
from webapp.models import db, Run, StravaToken

STRAVA_AUTH_URL = 'https://www.strava.com/oauth/authorize'
STRAVA_TOKEN_URL = 'https://www.strava.com/oauth/token'
STRAVA_API_URL = 'https://www.strava.com/api/v3'


def get_authorization_url():
    """Generate the Strava OAuth authorization URL."""
    params = {
        'client_id': config.STRAVA_CLIENT_ID,
        'redirect_uri': config.STRAVA_REDIRECT_URI,
        'response_type': 'code',
        'scope': 'activity:read_all',
    }
    query = '&'.join(f'{k}={v}' for k, v in params.items())
    return f'{STRAVA_AUTH_URL}?{query}'


def exchange_code_for_token(code):
    """Exchange authorization code for access and refresh tokens."""
    response = requests.post(STRAVA_TOKEN_URL, data={
        'client_id': config.STRAVA_CLIENT_ID,
        'client_secret': config.STRAVA_CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code',
    })
    response.raise_for_status()
    return response.json()


def refresh_access_token(strava_token):
    """Refresh an expired access token."""
    response = requests.post(STRAVA_TOKEN_URL, data={
        'client_id': config.STRAVA_CLIENT_ID,
        'client_secret': config.STRAVA_CLIENT_SECRET,
        'refresh_token': strava_token.refresh_token,
        'grant_type': 'refresh_token',
    })
    response.raise_for_status()
    data = response.json()

    strava_token.access_token = data['access_token']
    strava_token.refresh_token = data['refresh_token']
    strava_token.expires_at = data['expires_at']
    db.session.commit()

    return strava_token


def get_valid_token():
    """Get a valid access token, refreshing if necessary."""
    token = StravaToken.query.first()
    if token is None:
        return None

    if token.is_expired():
        token = refresh_access_token(token)

    return token


def fetch_recent_activities(token, days=30):
    """Fetch running activities from the last N days."""
    after = int((datetime.utcnow() - timedelta(days=days)).timestamp())

    headers = {'Authorization': f'Bearer {token.access_token}'}
    activities = []
    page = 1
    per_page = 50

    while True:
        response = requests.get(
            f'{STRAVA_API_URL}/athlete/activities',
            headers=headers,
            params={
                'after': after,
                'page': page,
                'per_page': per_page,
            }
        )
        response.raise_for_status()
        data = response.json()

        if not data:
            break

        # Filter to only running activities
        runs = [a for a in data if a['type'] == 'Run']
        activities.extend(runs)

        if len(data) < per_page:
            break
        page += 1

    return activities


def sync_activities_to_db(activities):
    """Import Strava activities to the database, skipping duplicates."""
    synced = 0
    skipped = 0

    for activity in activities:
        strava_id = activity['id']

        # Check if already synced
        existing = Run.query.filter_by(strava_activity_id=strava_id).first()
        if existing:
            skipped += 1
            continue

        # Parse activity data
        distance_km = Decimal(str(activity['distance'] / 1000)).quantize(Decimal('0.01'))
        duration_seconds = activity['moving_time']

        # Calculate pace (min/km)
        if distance_km > 0:
            pace_decimal = Decimal(str(duration_seconds / 60 / float(distance_km))).quantize(Decimal('0.01'))
        else:
            pace_decimal = None

        # Parse date from start_date_local
        activity_date = datetime.fromisoformat(
            activity['start_date_local'].replace('Z', '+00:00')
        ).date()

        run = Run(
            date=activity_date,
            distance=distance_km,
            duration=duration_seconds,
            pace=pace_decimal,
            strava_activity_id=strava_id,
            source='strava',
        )
        db.session.add(run)
        synced += 1

    db.session.commit()
    return synced, skipped


def sync_from_strava(days=30):
    """Full sync: get token, fetch activities, import to DB."""
    token = get_valid_token()
    if token is None:
        return None, 'Strava not connected'

    try:
        activities = fetch_recent_activities(token, days=days)
        synced, skipped = sync_activities_to_db(activities)
        return (synced, skipped), None
    except requests.RequestException as e:
        return None, f'Strava API error: {str(e)}'


def is_strava_connected():
    """Check if Strava is connected."""
    return StravaToken.query.first() is not None


def disconnect_strava():
    """Remove Strava connection by deleting tokens."""
    StravaToken.query.delete()
    db.session.commit()
