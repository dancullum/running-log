"""SQLAlchemy models for the Running Log application."""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Run(db.Model):
    """Logged running sessions."""

    __tablename__ = 'runs'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, unique=True)
    distance = db.Column(db.Numeric(5, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Run {self.date}: {self.distance}km>'


class TrainingPlan(db.Model):
    """Training plan with target distances per day."""

    __tablename__ = 'training_plan'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, unique=True)
    target_distance = db.Column(db.Numeric(5, 2), nullable=False)

    def __repr__(self):
        return f'<TrainingPlan {self.date}: {self.target_distance}km>'
