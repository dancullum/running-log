"""Run logging routes for Running Log."""

from datetime import date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash

from ..models import db, Run, TrainingPlan
from .auth import login_required

runs_bp = Blueprint('runs', __name__)


@runs_bp.route('/log', methods=['GET', 'POST'])
@login_required
def log():
    """Log a run form and submission."""
    today = date.today()

    if request.method == 'POST':
        try:
            distance = float(request.form.get('distance', 0))
            run_date_str = request.form.get('date', today.isoformat())
            run_date = date.fromisoformat(run_date_str)

            if distance <= 0:
                flash('Please enter a positive distance.', 'error')
                return redirect(url_for('runs.log'))

            if distance > 100:
                flash('Distance seems too high. Please check.', 'error')
                return redirect(url_for('runs.log'))

            # Check if run already exists for this date
            existing = Run.query.filter_by(date=run_date).first()
            if existing:
                existing.distance = distance
            else:
                new_run = Run(date=run_date, distance=distance)
                db.session.add(new_run)

            db.session.commit()
            flash(f'Logged {distance:.1f} km for {run_date.strftime("%b %d")}!', 'success')
            return redirect(url_for('main.home'))

        except ValueError as e:
            flash(f'Invalid input: {e}', 'error')
            return redirect(url_for('runs.log'))

    # GET request - show form
    today_plan = TrainingPlan.query.filter_by(date=today).first()
    today_target = float(today_plan.target_distance) if today_plan else None

    # Get past 7 days for date selection
    available_dates = []
    for i in range(7):
        d = today - timedelta(days=i)
        plan_entry = TrainingPlan.query.filter_by(date=d).first()
        target = float(plan_entry.target_distance) if plan_entry else None
        run = Run.query.filter_by(date=d).first()
        logged = float(run.distance) if run else None
        available_dates.append({
            'date': d,
            'target': target,
            'logged': logged
        })

    return render_template('log.html',
                           today=today,
                           today_target=today_target,
                           available_dates=available_dates)


@runs_bp.route('/run/<int:run_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_run(run_id):
    """Edit a run."""
    run = Run.query.get_or_404(run_id)

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'delete':
            db.session.delete(run)
            db.session.commit()
            flash('Run deleted.', 'success')
            return redirect(url_for('dashboard.dashboard'))

        try:
            distance = float(request.form.get('distance', 0))
            if distance < 0:
                flash('Distance cannot be negative.', 'error')
                return redirect(url_for('runs.edit_run', run_id=run_id))

            run.distance = distance
            db.session.commit()
            flash('Run updated.', 'success')
            return redirect(url_for('dashboard.dashboard'))

        except ValueError:
            flash('Invalid distance.', 'error')
            return redirect(url_for('runs.edit_run', run_id=run_id))

    # GET - show edit form
    plan_entry = TrainingPlan.query.filter_by(date=run.date).first()
    target = float(plan_entry.target_distance) if plan_entry else None

    return render_template('edit_run.html',
                           run=run,
                           target=target)
