"""Script to import training plan from CSV into the database."""

import csv
import sys
from datetime import date
from pathlib import Path

# Add the project directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from webapp.app import create_app
from webapp.models import db, TrainingPlan


def import_training_plan(csv_path: str):
    """Import training plan from CSV file into the database."""
    app = create_app()

    with app.app_context():
        # Clear existing plan
        TrainingPlan.query.delete()
        db.session.commit()

        # First collect all entries, handling duplicates (keep last value)
        plan_entries = {}
        with open(csv_path, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    plan_date = date.fromisoformat(row['Date'])
                    target = float(row['Target_km'])
                    plan_entries[plan_date] = target
                except (KeyError, ValueError) as e:
                    print(f"Skipping row: {e}")
                    continue

        # Now insert unique entries
        for plan_date, target in sorted(plan_entries.items()):
            entry = TrainingPlan(date=plan_date, target_distance=target)
            db.session.add(entry)

        db.session.commit()
        print(f"Imported {len(plan_entries)} training plan entries")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        # Default to the serpent trail plan
        csv_path = Path(__file__).parent / 'serpent_trail_training_plan.csv'
    else:
        csv_path = sys.argv[1]

    import_training_plan(str(csv_path))
