"""
Database Model Tests for Running Log.

WHY TEST MODELS?
----------------
Models are the foundation of your app. Testing them ensures:

1. Data is stored correctly
2. Constraints work (unique dates, required fields)
3. Relationships work if you have them
4. Your assumptions about the database are correct

MODEL TESTS vs ROUTE TESTS
--------------------------
- Model tests: Test database operations directly
- Route tests: Test the full HTTP request/response cycle

Model tests are faster and more focused. Use them to test
database logic in isolation.

TESTING DATABASE CONSTRAINTS
---------------------------
SQLAlchemy will raise exceptions when constraints are violated:
- IntegrityError: Unique constraint, foreign key, not null
- DataError: Value doesn't fit column type

We test that these constraints work as expected.
"""

import pytest
from datetime import date, timedelta
from sqlalchemy.exc import IntegrityError

from webapp.models import db, Run, TrainingPlan


class TestRunModel:
    """
    Tests for the Run model.
    """

    def test_create_run(self, app):
        """
        Test basic run creation.
        """
        with app.app_context():
            run = Run(date=date.today(), distance=5.5)
            db.session.add(run)
            db.session.commit()

            # Verify it was saved
            assert run.id is not None
            saved_run = db.session.get(Run, run.id)
            assert saved_run.date == date.today()
            assert float(saved_run.distance) == 5.5

    def test_run_has_created_at_timestamp(self, app):
        """
        Test that runs automatically get a created_at timestamp.
        """
        with app.app_context():
            run = Run(date=date.today(), distance=5.0)
            db.session.add(run)
            db.session.commit()

            assert run.created_at is not None

    def test_multiple_runs_per_day_allowed(self, app):
        """
        Test that multiple runs can be logged for the same date.

        This supports Strava integration where multiple activities
        can occur on the same day.
        """
        with app.app_context():
            # Create first run
            run1 = Run(date=date.today(), distance=5.0)
            db.session.add(run1)
            db.session.commit()

            # Create second run for same date - should succeed
            run2 = Run(date=date.today(), distance=8.0)
            db.session.add(run2)
            db.session.commit()

            # Both runs should exist
            runs_today = Run.query.filter_by(date=date.today()).all()
            assert len(runs_today) == 2

    def test_run_distance_required(self, app):
        """
        Test that distance is required (not nullable).
        """
        with app.app_context():
            # Try to create run without distance
            run = Run(date=date.today())
            db.session.add(run)

            with pytest.raises(IntegrityError):
                db.session.commit()

            db.session.rollback()

    def test_run_date_required(self, app):
        """
        Test that date is required (not nullable).
        """
        with app.app_context():
            run = Run(distance=5.0)
            db.session.add(run)

            with pytest.raises(IntegrityError):
                db.session.commit()

            db.session.rollback()

    def test_run_repr(self, app):
        """
        Test the string representation of a Run.

        __repr__ is useful for debugging - it shows in logs and errors.
        """
        with app.app_context():
            run = Run(date=date(2026, 1, 15), distance=7.5)
            representation = repr(run)

            assert '2026-01-15' in representation
            assert '7.5' in representation

    def test_query_runs_by_date_range(self, app):
        """
        Test querying runs within a date range.

        This tests a common query pattern used in weekly summaries.
        """
        with app.app_context():
            # Create runs across multiple days
            today = date.today()
            for i in range(5):
                run = Run(date=today - timedelta(days=i), distance=5.0 + i)
                db.session.add(run)
            db.session.commit()

            # Query for last 3 days
            three_days_ago = today - timedelta(days=2)
            runs = Run.query.filter(
                Run.date >= three_days_ago,
                Run.date <= today
            ).all()

            assert len(runs) == 3

    def test_query_runs_ordered_by_date(self, app):
        """
        Test that runs can be ordered by date.
        """
        with app.app_context():
            # Create runs out of order
            dates = [date.today(), date.today() - timedelta(days=2), date.today() - timedelta(days=1)]
            for d in dates:
                run = Run(date=d, distance=5.0)
                db.session.add(run)
            db.session.commit()

            # Query in descending order (most recent first)
            runs = Run.query.order_by(Run.date.desc()).all()

            assert runs[0].date == date.today()
            assert runs[-1].date == date.today() - timedelta(days=2)


class TestTrainingPlanModel:
    """
    Tests for the TrainingPlan model.
    """

    def test_create_training_plan_entry(self, app):
        """
        Test basic training plan entry creation.
        """
        with app.app_context():
            entry = TrainingPlan(date=date.today(), target_distance=8.0)
            db.session.add(entry)
            db.session.commit()

            assert entry.id is not None
            assert float(entry.target_distance) == 8.0

    def test_training_plan_date_must_be_unique(self, app):
        """
        Test that each date can only have one training plan entry.
        """
        with app.app_context():
            entry1 = TrainingPlan(date=date.today(), target_distance=5.0)
            db.session.add(entry1)
            db.session.commit()

            entry2 = TrainingPlan(date=date.today(), target_distance=8.0)
            db.session.add(entry2)

            with pytest.raises(IntegrityError):
                db.session.commit()

            db.session.rollback()

    def test_query_future_plan_entries(self, app):
        """
        Test querying future training plan entries.

        Used for the "Plan" page to show upcoming workouts.
        """
        with app.app_context():
            today = date.today()

            # Create past and future entries
            for i in range(-2, 5):
                entry = TrainingPlan(
                    date=today + timedelta(days=i),
                    target_distance=5.0
                )
                db.session.add(entry)
            db.session.commit()

            # Query future entries only
            future = TrainingPlan.query.filter(
                TrainingPlan.date >= today
            ).all()

            assert len(future) == 5  # Today + 4 future days

    def test_sum_total_planned_distance(self, app):
        """
        Test calculating total planned distance.

        Used for "Total remaining until race day" calculation.
        """
        with app.app_context():
            today = date.today()

            # Create entries with known distances
            distances = [5.0, 8.0, 3.0, 10.0]
            for i, dist in enumerate(distances):
                entry = TrainingPlan(
                    date=today + timedelta(days=i),
                    target_distance=dist
                )
                db.session.add(entry)
            db.session.commit()

            # Calculate sum using SQLAlchemy
            from sqlalchemy import func
            total = db.session.query(
                func.sum(TrainingPlan.target_distance)
            ).scalar()

            assert float(total) == sum(distances)


class TestModelInteractions:
    """
    Tests for interactions between models.

    Even though Run and TrainingPlan don't have a formal foreign key
    relationship, they're related by date. These tests verify
    common query patterns that join them logically.
    """

    def test_find_runs_with_matching_targets(self, app):
        """
        Test finding runs and their corresponding targets.

        This is the pattern used to calculate "actual vs target".
        """
        with app.app_context():
            today = date.today()

            # Create training plan
            plan = TrainingPlan(date=today, target_distance=8.0)
            db.session.add(plan)

            # Create run
            run = Run(date=today, distance=7.5)
            db.session.add(run)
            db.session.commit()

            # Query pattern: get run and find matching plan
            saved_run = Run.query.filter_by(date=today).first()
            matching_plan = TrainingPlan.query.filter_by(date=saved_run.date).first()

            assert saved_run is not None
            assert matching_plan is not None
            assert matching_plan.date == saved_run.date

            # Calculate difference
            diff = float(saved_run.distance) - float(matching_plan.target_distance)
            assert diff == -0.5  # Ran 0.5km less than target
