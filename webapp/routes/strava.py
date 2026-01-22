"""Strava OAuth and sync routes."""

from flask import Blueprint, redirect, url_for, flash, session

from webapp import config
from webapp.models import db, StravaToken
from webapp.routes.auth import login_required
from webapp.services import strava as strava_service

strava_bp = Blueprint('strava', __name__, url_prefix='/strava')


@strava_bp.route('/connect')
@login_required
def connect():
    """Redirect to Strava OAuth authorization."""
    if not config.STRAVA_CLIENT_ID or not config.STRAVA_CLIENT_SECRET:
        flash('Strava API credentials not configured.', 'error')
        return redirect(url_for('main.home'))

    auth_url = strava_service.get_authorization_url()
    return redirect(auth_url)


@strava_bp.route('/callback')
def callback():
    """Handle Strava OAuth callback."""
    from flask import request

    error = request.args.get('error')
    if error:
        flash(f'Strava authorization failed: {error}', 'error')
        return redirect(url_for('main.home'))

    code = request.args.get('code')
    if not code:
        flash('No authorization code received from Strava.', 'error')
        return redirect(url_for('main.home'))

    try:
        token_data = strava_service.exchange_code_for_token(code)

        # Store or update token
        athlete_id = token_data['athlete']['id']
        existing = StravaToken.query.filter_by(athlete_id=athlete_id).first()

        if existing:
            existing.access_token = token_data['access_token']
            existing.refresh_token = token_data['refresh_token']
            existing.expires_at = token_data['expires_at']
        else:
            new_token = StravaToken(
                athlete_id=athlete_id,
                access_token=token_data['access_token'],
                refresh_token=token_data['refresh_token'],
                expires_at=token_data['expires_at'],
            )
            db.session.add(new_token)

        db.session.commit()

        # Sync recent activities
        result, error = strava_service.sync_from_strava(days=30)
        if result:
            synced, skipped = result
            flash(f'Strava connected! Synced {synced} new runs.', 'success')
        else:
            flash(f'Strava connected, but sync failed: {error}', 'warning')

    except Exception as e:
        flash(f'Failed to connect Strava: {str(e)}', 'error')

    return redirect(url_for('main.home'))


@strava_bp.route('/disconnect', methods=['POST'])
@login_required
def disconnect():
    """Disconnect Strava integration."""
    strava_service.disconnect_strava()
    flash('Strava disconnected.', 'success')
    return redirect(url_for('main.home'))


@strava_bp.route('/sync', methods=['POST'])
@login_required
def sync():
    """Manually trigger a Strava sync."""
    result, error = strava_service.sync_from_strava(days=30)

    if result:
        synced, skipped = result
        if synced > 0:
            flash(f'Synced {synced} new runs from Strava.', 'success')
        else:
            flash('No new runs to sync.', 'info')
    else:
        flash(f'Sync failed: {error}', 'error')

    return redirect(url_for('main.home'))
