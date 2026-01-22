"""Main routes (Home, Plan) for Running Log."""

from datetime import date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash
from sqlalchemy import func

from ..models import db, Run, TrainingPlan
from .auth import login_required, is_authenticated

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
    # Auto-sync from Strava if connected and not synced recently
    from ..services.strava import auto_sync_if_needed
    synced = auto_sync_if_needed(minutes=1)
    if synced and synced > 0:
        flash(f'Synced {synced} new run{"s" if synced != 1 else ""} from Strava.', 'success')

    today = date.today()

    # Get today's target
    today_plan = TrainingPlan.query.filter_by(date=today).first()
    today_target = float(today_plan.target_distance) if today_plan else None

    # Get today's logged runs (sum if multiple)
    today_runs = Run.query.filter_by(date=today).all()
    today_distance = sum(float(r.distance) for r in today_runs) if today_runs else None

    week_summary = get_week_summary()
    recent_runs = get_recent_runs(3)

    return render_template('home.html',
                           today=today,
                           today_target=today_target,
                           today_distance=today_distance,
                           week_summary=week_summary,
                           recent_runs=recent_runs)


@main_bp.route('/plan')
def plan():
    """Training plan page - shows this week's plan and future schedule."""
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)

    # Get all runs and sum by date
    all_runs = Run.query.all()
    runs_by_date = {}
    for r in all_runs:
        if r.date in runs_by_date:
            runs_by_date[r.date] += float(r.distance)
        else:
            runs_by_date[r.date] = float(r.distance)

    # Get this week's plan (Monday to Sunday)
    this_week_plans = TrainingPlan.query.filter(
        TrainingPlan.date >= monday,
        TrainingPlan.date <= sunday
    ).order_by(TrainingPlan.date).all()

    this_week = []
    week_target_total = 0
    week_logged_total = 0
    for plan_entry in this_week_plans:
        is_today = plan_entry.date == today
        is_past = plan_entry.date < today
        logged = runs_by_date.get(plan_entry.date)
        target = float(plan_entry.target_distance)
        week_target_total += target
        if logged:
            week_logged_total += logged
        this_week.append({
            'id': plan_entry.id,
            'date': plan_entry.date,
            'target': target,
            'logged': logged,
            'is_today': is_today,
            'is_past': is_past
        })

    # Get future planned days (after this week)
    future_plans = TrainingPlan.query.filter(
        TrainingPlan.date > sunday
    ).order_by(TrainingPlan.date).all()

    future_schedule = []
    for plan_entry in future_plans:
        logged = runs_by_date.get(plan_entry.date)
        future_schedule.append({
            'id': plan_entry.id,
            'date': plan_entry.date,
            'target': float(plan_entry.target_distance),
            'logged': logged,
            'is_today': False,
            'is_past': False
        })

    # Calculate total distance run so far
    total_run = sum(runs_by_date.values())

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

    return render_template('plan.html',
                           today=today,
                           monday=monday,
                           sunday=sunday,
                           this_week=this_week,
                           week_target_total=week_target_total,
                           week_logged_total=week_logged_total,
                           future_schedule=future_schedule,
                           total_run=total_run,
                           total_planned=total_planned,
                           days_remaining=days_remaining,
                           race_day=race_day,
                           is_authenticated=is_authenticated())


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
