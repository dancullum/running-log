"""Training plan loader and query functions."""

import csv
from datetime import date
from pathlib import Path
from typing import Optional

import yaml


def get_plan_path() -> Path:
    """Get the training plan file path."""
    # First check user config directory
    user_plan = Path.home() / ".running-log" / "plan.yaml"
    if user_plan.exists():
        return user_plan
    # Fall back to project config directory
    return Path(__file__).parent.parent / "config" / "plan.yaml"


def load_plan() -> dict[date, float]:
    """Load training plan from YAML file."""
    plan_path = get_plan_path()
    if not plan_path.exists():
        return {}

    with open(plan_path) as f:
        data = yaml.safe_load(f)

    if not data or "schedule" not in data:
        return {}

    schedule = {}
    for date_key, distance in data["schedule"].items():
        if isinstance(date_key, date):
            schedule[date_key] = float(distance)
        else:
            schedule[date.fromisoformat(str(date_key))] = float(distance)

    return schedule


def get_target(target_date: date) -> Optional[float]:
    """Get target distance for a specific date."""
    plan = load_plan()
    return plan.get(target_date)


def get_targets_in_range(start_date: date, end_date: date) -> dict[date, float]:
    """Get all targets within a date range (inclusive)."""
    plan = load_plan()
    return {
        d: dist for d, dist in plan.items()
        if start_date <= d <= end_date
    }


def get_total_planned() -> float:
    """Get total planned distance across entire training plan."""
    plan = load_plan()
    return sum(plan.values())


def get_planned_days() -> int:
    """Get number of days with planned runs (non-zero targets)."""
    plan = load_plan()
    return sum(1 for dist in plan.values() if dist > 0)


def import_from_csv(csv_path: str) -> int:
    """Import training plan from CSV file.

    Expected columns: Date, Target_km (other columns ignored).
    Returns number of entries imported.
    """
    plan_path = Path.home() / ".running-log" / "plan.yaml"
    plan_path.parent.mkdir(exist_ok=True)

    schedule = {}
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                run_date = date.fromisoformat(row["Date"])
                distance = float(row["Target_km"])
                schedule[run_date] = distance
            except (KeyError, ValueError):
                continue

    # Write to YAML
    yaml_data = {
        "schedule": {d.isoformat(): dist for d, dist in sorted(schedule.items())}
    }
    with open(plan_path, "w") as f:
        yaml.dump(yaml_data, f, default_flow_style=False)

    return len(schedule)
