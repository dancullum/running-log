"""Main routes (Home, Plan) for Running Log."""

from datetime import date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash
from sqlalchemy import func

from ..models import db, Run, TrainingPlan
from .auth import login_required

main_bp = Blueprint('main', __name__)


def get_week_summary():
    """Get summary for current week (Monday-Sunday)."""
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)

    # Get runs this week
    runs = Run.query.filter(
        Run.date >= monday,
        Run.date <= sunday
    ).all()

    # Get targets this week
    targets = TrainingPlan.query.filter(
        TrainingPlan.date >= monday,
        TrainingPlan.date <= sunday
    ).all()

    total_run = sum(float(r.distance) for r in runs)
    total_target = sum(float(t.target_distance) for t in targets)
    days_logged = len(runs)

    return {
        'start': monday,
        'end': sunday,
        'total_run': total_run,
        'total_target': total_target,
        'days_logged': days_logged,
        'progress_percent': (total_run / total_target * 100) if total_target > 0 else 0
    }


def get_recent_runs(limit=3):
    """Get the most recent logged runs."""
    runs = Run.query.order_by(Run.date.desc()).limit(limit).all()
    result = []
    for run in runs:
        target = TrainingPlan.query.filter_by(date=run.date).first()
        target_km = float(target.target_distance) if target else None
        diff = float(run.distance) - target_km if target_km else None
        result.append({
            'id': run.id,
            'date': run.date,
            'distance': float(run.distance),
            'target': target_km,
            'diff': diff
        })
    return result


@main_bp.route('/')
@login_required
def home():
    """Home page - weekly progress and recent runs."""
    today = date.today()

    # Get today's target
    today_plan = TrainingPlan.query.filter_by(date=today).first()
    today_target = float(today_plan.target_distance) if today_plan else None

    # Get today's logged run
    today_run = Run.query.filter_by(date=today).first()
    today_distance = float(today_run.distance) if today_run else None

    week_summary = get_week_summary()
    recent_runs = get_recent_runs(3)

    return render_template('home.html',
                           today=today,
                           today_target=today_target,
                           today_distance=today_distance,
                           week_summary=week_summary,
                           recent_runs=recent_runs)


@main_bp.route('/plan')
@login_required
def plan():
    """Training plan page - shows schedule from yesterday onward."""
    today = date.today()
    yesterday = today - timedelta(days=1)

    # Get all planned days from yesterday onward
    planned_days = TrainingPlan.query.filter(
        TrainingPlan.date >= yesterday
    ).order_by(TrainingPlan.date).all()

    # Get runs for these dates
    dates = [p.date for p in planned_days]
    runs = Run.query.filter(Run.date.in_(dates)).all()
    runs_by_date = {r.date: float(r.distance) for r in runs}

    # Calculate total distance run so far
    all_runs = Run.query.all()
    total_run = sum(float(r.distance) for r in all_runs)

    # Calculate total planned distance (entire plan)
    all_plans = TrainingPlan.query.all()
    total_planned = sum(float(p.target_distance) for p in all_plans)

    # Calculate days remaining until race day (last day of plan)
    last_plan = TrainingPlan.query.order_by(TrainingPlan.date.desc()).first()
    if last_plan:
        race_day = last_plan.date
        days_remaining = (race_day - today).days
    else:
        race_day = None
        days_remaining = 0

    schedule = []
    for plan_entry in planned_days:
        is_today = plan_entry.date == today
        is_past = plan_entry.date < today
        logged = runs_by_date.get(plan_entry.date)

        schedule.append({
            'id': plan_entry.id,
            'date': plan_entry.date,
            'target': float(plan_entry.target_distance),
            'logged': logged,
            'is_today': is_today,
            'is_past': is_past
        })

    return render_template('plan.html',
                           today=today,
                           schedule=schedule,
                           total_run=total_run,
                           total_planned=total_planned,
                           days_remaining=days_remaining,
                           race_day=race_day)


@main_bp.route('/plan/<int:plan_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_plan(plan_id):
    """Edit a training plan entry."""
    plan_entry = TrainingPlan.query.get_or_404(plan_id)

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'delete':
            db.session.delete(plan_entry)
            db.session.commit()
            flash('Plan entry deleted.', 'success')
            return redirect(url_for('main.plan'))

        try:
            target = float(request.form.get('target_distance', 0))
            if target < 0:
                flash('Target must be 0 or positive.', 'error')
                return redirect(url_for('main.edit_plan', plan_id=plan_id))

            plan_entry.target_distance = target
            db.session.commit()
            flash('Plan updated.', 'success')
            return redirect(url_for('main.plan'))

        except ValueError:
            flash('Invalid distance.', 'error')
            return redirect(url_for('main.edit_plan', plan_id=plan_id))

    return render_template('edit_plan.html', plan_entry=plan_entry)
