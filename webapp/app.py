"""Flask application factory for Running Log."""

from datetime import date, timedelta
from flask import Flask

from .config import DATABASE_URL, SECRET_KEY
from .models import db


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Configuration
    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    from .routes.auth import auth_bp
    from .routes.main import main_bp
    from .routes.runs import runs_bp
    from .routes.dashboard import dashboard_bp
    from .routes.strava import strava_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(runs_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(strava_bp)

    # Template filters
    @app.template_filter('format_date')
    def format_date(d):
        """Format date for display."""
        if d == date.today():
            return 'Today'
        elif d == date.today() - timedelta(days=1):
            return 'Yesterday'
        return d.strftime('%a, %b %d')

    @app.template_filter('format_date_short')
    def format_date_short(d):
        """Format date shortly."""
        return d.strftime('%a %d')

    @app.template_filter('format_distance')
    def format_distance(km):
        """Format distance for display with thousands separator."""
        if km is None:
            return '-'
        km = float(km)
        if km == int(km):
            return f'{int(km):,}'
        return f'{km:,.1f}'

    # Context processor to inject strava_connected into all templates
    @app.context_processor
    def inject_strava_status():
        from .services.strava import is_strava_connected
        return {'strava_connected': is_strava_connected()}

    # Create tables
    with app.app_context():
        db.create_all()

    return app


# Development server entry point
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5001)
