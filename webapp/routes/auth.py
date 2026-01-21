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
            next_url = request.args.get('next')
            if next_url:
                return redirect(next_url)
            return redirect(url_for('main.home'))
        flash('Incorrect password', 'error')
    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    """Handle logout."""
    session.pop('authenticated', None)
    flash('Logged out', 'success')
    return redirect(url_for('dashboard.dashboard'))
