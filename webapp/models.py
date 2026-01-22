"""SQLAlchemy models for the Running Log application."""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Run(db.Model):
    """Logged running sessions."""

    __tablename__ = 'runs'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    distance = db.Column(db.Numeric(5, 2), nullable=False)
    duration = db.Column(db.Integer, nullable=True)  # seconds
    pace = db.Column(db.Numeric(5, 2), nullable=True)  # min/km
    strava_activity_id = db.Column(db.BigInteger, nullable=True, unique=True)
    source = db.Column(db.String(20), default='manual')  # 'manual' or 'strava'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def pace_formatted(self):
        """Return pace as MM:SS string."""
        if self.pace is None:
            return None
        minutes = int(self.pace)
        seconds = int((float(self.pace) - minutes) * 60)
        return f"{minutes}:{seconds:02d}"

    @property
    def duration_formatted(self):
        """Return duration as HH:MM:SS or MM:SS string."""
        if self.duration is None:
            return None
        hours = self.duration // 3600
        minutes = (self.duration % 3600) // 60
        seconds = self.duration % 60
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"

    def __repr__(self):
        return f'<Run {self.date}: {self.distance}km>'


class StravaToken(db.Model):
    """Strava OAuth tokens."""

    __tablename__ = 'strava_tokens'

    id = db.Column(db.Integer, primary_key=True)
    athlete_id = db.Column(db.BigInteger, nullable=False, unique=True)
    access_token = db.Column(db.String(255), nullable=False)
    refresh_token = db.Column(db.String(255), nullable=False)
    expires_at = db.Column(db.Integer, nullable=False)  # Unix timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def is_expired(self):
        """Check if the access token is expired."""
        return datetime.utcnow().timestamp() >= self.expires_at

    def __repr__(self):
        return f'<StravaToken athlete_id={self.athlete_id}>'


class TrainingPlan(db.Model):
    """Training plan with target distances per day."""

    __tablename__ = 'training_plan'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, unique=True)
    target_distance = db.Column(db.Numeric(5, 2), nullable=False)

    def __repr__(self):
        return f'<TrainingPlan {self.date}: {self.target_distance}km>'
