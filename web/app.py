"""Flask web application for running log."""

import sys
from datetime import date, timedelta
from pathlib import Path

# Add parent directory to path to import running_log modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, render_template, request, redirect, url_for, flash

from running_log import db, plan

app = Flask(__name__)
app.secret_key = 'running-log-secret-key-change-in-production'

# Goal: 50km ultra marathon
ULTRA_GOAL_KM = 50.0


def get_progress_stats():
    """Calculate overall progress statistics."""
    total_distance = db.get_total_distance()
    run_count = db.get_run_count()
    total_planned = plan.get_total_planned()
    planned_days = plan.get_planned_days()

    # Calculate percentage towards ultra goal
    ultra_progress = min(100, (total_distance / ULTRA_GOAL_KM) * 100) if ULTRA_GOAL_KM > 0 else 0

    # Calculate plan completion percentage
    plan_progress = (total_distance / total_planned * 100) if total_planned > 0 else 0

    return {
        'total_distance': total_distance,
        'run_count': run_count,
        'total_planned': total_planned,
        'planned_days': planned_days,
        'ultra_progress': ultra_progress,
        'plan_progress': plan_progress,
        'ultra_goal': ULTRA_GOAL_KM,
    }


def get_recent_runs(limit=5):
    """Get the most recent logged runs."""
    all_runs = db.get_all_runs()
    recent = []
    for run_date, distance in all_runs[:limit]:
        target = plan.get_target(run_date)
        diff = None
        if target and target > 0:
            diff = distance - target
        recent.append({
            'date': run_date,
            'distance': distance,
            'target': target,
            'diff': diff,
        })
    return recent


def get_week_summary():
    """Get summary for current week."""
    today = date.today()
    # Week starts Monday
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)

    runs = db.get_runs_in_range(monday, sunday)
    targets = plan.get_targets_in_range(monday, sunday)

    total_run = sum(dist for _, dist in runs)
    total_target = sum(targets.values())

    return {
        'start': monday,
        'end': sunday,
        'total_run': total_run,
        'total_target': total_target,
        'days_logged': len(runs),
    }


@app.route('/')
def dashboard():
    """Main dashboard - shows today's target, recent runs, and progress."""
    today = date.today()
    today_target = plan.get_target(today)
    today_run = db.get_run(today)

    stats = get_progress_stats()
    recent_runs = get_recent_runs(5)
    week_summary = get_week_summary()

    return render_template('dashboard.html',
                         today=today,
                         today_target=today_target,
                         today_run=today_run,
                         stats=stats,
                         recent_runs=recent_runs,
                         week_summary=week_summary)


@app.route('/log', methods=['GET'])
def log_form():
    """Display form to log a run."""
    today = date.today()
    today_target = plan.get_target(today)
    today_run = db.get_run(today)

    # Allow logging for past 7 days
    available_dates = []
    for i in range(7):
        d = today - timedelta(days=i)
        target = plan.get_target(d)
        logged = db.get_run(d)
        available_dates.append({
            'date': d,
            'target': target,
            'logged': logged,
        })

    return render_template('log.html',
                         today=today,
                         today_target=today_target,
                         today_run=today_run,
                         available_dates=available_dates)


@app.route('/log', methods=['POST'])
def log_submit():
    """Submit a logged run."""
    try:
        distance = float(request.form.get('distance', 0))
        run_date_str = request.form.get('date', date.today().isoformat())
        run_date = date.fromisoformat(run_date_str)

        if distance <= 0:
            flash('Please enter a positive distance.', 'error')
            return redirect(url_for('log_form'))

        if distance > 100:
            flash('Distance seems too high. Please check.', 'error')
            return redirect(url_for('log_form'))

        db.log_run(run_date, distance)
        flash(f'Logged {distance:.1f} km for {run_date.strftime("%b %d")}!', 'success')

    except ValueError as e:
        flash(f'Invalid input: {e}', 'error')
        return redirect(url_for('log_form'))

    return redirect(url_for('dashboard'))


@app.route('/upcoming')
def upcoming():
    """Show next 7 days of targets."""
    today = date.today()
    upcoming_days = []

    for i in range(7):
        d = today + timedelta(days=i)
        target = plan.get_target(d)
        logged = db.get_run(d)
        upcoming_days.append({
            'date': d,
            'target': target,
            'logged': logged,
            'is_today': d == today,
        })

    return render_template('upcoming.html',
                         today=today,
                         upcoming_days=upcoming_days)


@app.route('/history')
def history():
    """Show all logged runs."""
    all_runs = db.get_all_runs()

    runs_with_targets = []
    for run_date, distance in all_runs:
        target = plan.get_target(run_date)
        diff = None
        if target and target > 0:
            diff = distance - target
        runs_with_targets.append({
            'date': run_date,
            'distance': distance,
            'target': target,
            'diff': diff,
        })

    return render_template('history.html',
                         runs=runs_with_targets,
                         total_runs=len(runs_with_targets))


@app.route('/stats')
def stats():
    """Show detailed statistics."""
    stats = get_progress_stats()
    week_summary = get_week_summary()
    all_runs = db.get_all_runs()

    # Calculate additional stats
    if all_runs:
        distances = [dist for _, dist in all_runs]
        avg_distance = sum(distances) / len(distances)
        max_distance = max(distances)
        min_distance = min(distances)

        # Find best and worst weeks
        # Group by week
        weeks = {}
        for run_date, dist in all_runs:
            monday = run_date - timedelta(days=run_date.weekday())
            if monday not in weeks:
                weeks[monday] = 0
            weeks[monday] += dist

        best_week = max(weeks.items(), key=lambda x: x[1]) if weeks else None

        # Streak calculation
        today = date.today()
        streak = 0
        check_date = today
        while True:
            if db.get_run(check_date):
                streak += 1
                check_date -= timedelta(days=1)
            else:
                break
    else:
        avg_distance = 0
        max_distance = 0
        min_distance = 0
        best_week = None
        streak = 0

    return render_template('stats.html',
                         stats=stats,
                         week_summary=week_summary,
                         avg_distance=avg_distance,
                         max_distance=max_distance,
                         min_distance=min_distance,
                         best_week=best_week,
                         streak=streak)


# Template filters
@app.template_filter('format_date')
def format_date(d):
    """Format date for display."""
    if d == date.today():
        return 'Today'
    elif d == date.today() - timedelta(days=1):
        return 'Yesterday'
    return d.strftime('%a %b %d')


@app.template_filter('format_date_short')
def format_date_short(d):
    """Format date shortly."""
    return d.strftime('%a %d')


@app.template_filter('format_distance')
def format_distance(km):
    """Format distance for display."""
    if km is None:
        return '-'
    if km == int(km):
        return f'{int(km)} km'
    return f'{km:.1f} km'


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
