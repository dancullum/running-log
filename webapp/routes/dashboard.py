"""Public dashboard route for Running Log."""

from datetime import date, timedelta
from flask import Blueprint, render_template, jsonify, session

from ..models import db, Run, TrainingPlan
from .auth import is_authenticated

dashboard_bp = Blueprint('dashboard', __name__)


def get_weekly_summaries():
    """Get summaries for all completed weeks with runs."""
    today = date.today()
    current_week_monday = today - timedelta(days=today.weekday())

    # Get all runs
    runs = Run.query.order_by(Run.date).all()
    if not runs:
        return []

    # Group runs by week (Monday of each week)
    weeks = {}
    for run in runs:
        week_monday = run.date - timedelta(days=run.date.weekday())
        if week_monday not in weeks:
            weeks[week_monday] = {'actual': 0, 'target': 0}
        weeks[week_monday]['actual'] += float(run.distance)

    # Add targets for each week
    plans = TrainingPlan.query.all()
    for plan in plans:
        week_monday = plan.date - timedelta(days=plan.date.weekday())
        if week_monday in weeks:
            weeks[week_monday]['target'] += float(plan.target_distance)

    # Build sorted list of completed weeks only (not current week)
    summaries = []
    for week_monday in sorted(weeks.keys(), reverse=True):
        if week_monday >= current_week_monday:
            continue  # Skip current week

        week_sunday = week_monday + timedelta(days=6)
        actual = weeks[week_monday]['actual']
        target = weeks[week_monday]['target']

        summaries.append({
            'week_start': week_monday,
            'week_end': week_sunday,
            'actual': actual,
            'target': target,
            'diff': actual - target if target > 0 else None
        })

    return summaries


@dashboard_bp.route('/dashboard')
def dashboard():
    """Public dashboard - stats, chart, and all runs."""
    # Get all runs
    runs = Run.query.order_by(Run.date.desc()).all()

    # Calculate stats
    total_runs = len(runs)
    total_distance = sum(float(r.distance) for r in runs)
    avg_distance = total_distance / total_runs if total_runs > 0 else 0

    # Build runs list with targets
    runs_list = []
    for run in runs:
        plan_entry = TrainingPlan.query.filter_by(date=run.date).first()
        target = float(plan_entry.target_distance) if plan_entry else None
        diff = float(run.distance) - target if target else None
        runs_list.append({
            'id': run.id,
            'date': run.date,
            'distance': float(run.distance),
            'target': target,
            'diff': diff
        })

    # Calculate weekly summaries for completed weeks
    weekly_summaries = get_weekly_summaries()

    return render_template('dashboard.html',
                           runs=runs_list,
                           total_runs=total_runs,
                           total_distance=total_distance,
                           avg_distance=avg_distance,
                           weekly_summaries=weekly_summaries,
                           is_authenticated=is_authenticated())


@dashboard_bp.route('/api/chart-data')
def chart_data():
    """API endpoint for chart data - actual vs target over time."""
    # Get all runs ordered by date
    runs = Run.query.order_by(Run.date).all()
    runs_by_date = {r.date: float(r.distance) for r in runs}

    # Get all training plan entries
    plans = TrainingPlan.query.order_by(TrainingPlan.date).all()

    # Build chart data - only include dates with either a run or a target
    dates = sorted(set(list(runs_by_date.keys()) + [p.date for p in plans]))

    # Only go up to today
    today = date.today()
    dates = [d for d in dates if d <= today]

    chart_labels = []
    actual_data = []
    target_data = []

    # Track cumulative totals
    cumulative_actual = 0
    cumulative_target = 0

    plans_by_date = {p.date: float(p.target_distance) for p in plans}

    for d in dates:
        chart_labels.append(d.strftime('%b %d'))

        # Add actual if run exists
        if d in runs_by_date:
            cumulative_actual += runs_by_date[d]

        # Add target if plan exists
        if d in plans_by_date:
            cumulative_target += plans_by_date[d]

        actual_data.append(round(cumulative_actual, 1))
        target_data.append(round(cumulative_target, 1))

    return jsonify({
        'labels': chart_labels,
        'actual': actual_data,
        'target': target_data
    })
