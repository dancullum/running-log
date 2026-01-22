"""Authentication routes for Running Log."""

from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash

from ..config import PASSWORD_HASH

auth_bp = Blueprint('auth', __name__)


def login_required(f):
    """Decorator to require authentication for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def is_authenticated():
    """Check if user is currently authenticated."""
    return session.get('authenticated', False)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle login."""
    if request.method == 'POST':
        password = request.form.get('password', '')
        if check_password_hash(PASSWORD_HASH, password):
            session['authenticated'] = True

            # Auto-sync from Strava if connected
            _auto_sync_strava()

            next_url = request.args.get('next')
            if next_url:
                return redirect(next_url)
            return redirect(url_for('main.home'))
        flash('Incorrect password', 'error')
    return render_template('login.html')


def _auto_sync_strava():
    """Sync runs from Strava on login if connected."""
    try:
        from webapp.services import strava as strava_service
        if strava_service.is_strava_connected():
            result, error = strava_service.sync_from_strava(days=30)
            if result:
                synced, _ = result
                if synced > 0:
                    flash(f'Synced {synced} new runs from Strava.', 'success')
    except Exception:
        # Don't block login if sync fails
        pass


@auth_bp.route('/logout')
def logout():
    """Handle logout."""
    session.pop('authenticated', None)
    flash('Logged out', 'success')
    return redirect(url_for('dashboard.dashboard'))
