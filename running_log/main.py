"""Main entry point and menu loop for Running Log."""

import csv
from datetime import date, timedelta
from pathlib import Path

from . import db, plan, ui


def show_menu() -> None:
    """Display the main menu."""
    ui.print_header("Running Log")
    print("1. Log run")
    print("2. Upcoming targets")
    print("3. Browse date")
    print("4. This week")
    print("5. History")
    print("6. Export CSV")
    print("7. Import plan")
    print("8. Stats")
    print("0. Exit")
    print()


def log_run() -> None:
    """Log a run for today."""
    today = date.today()
    distance = ui.prompt_float("Distance (km)")

    if distance is None:
        ui.print_error("Invalid distance")
        return

    if distance < 0:
        ui.print_error("Distance must be positive")
        return

    db.log_run(today, distance)
    target = plan.get_target(today)

    if target and target > 0:
        diff = distance - target
        if diff >= 0:
            ui.print_success(f"{ui.format_distance(distance)} logged (+{diff:.1f} vs target)")
        else:
            ui.print_success(f"{ui.format_distance(distance)} logged ({diff:.1f} vs target)")
    else:
        ui.print_success(f"{ui.format_distance(distance)} logged")


def show_upcoming_targets() -> None:
    """Show targets for the next 7 days."""
    today = date.today()

    ui.print_header("Upcoming Targets")
    ui.print_divider()

    for i in range(7):
        current = today + timedelta(days=i)
        target = plan.get_target(current)
        day_str = ui.format_date_short(current)

        if target is not None:
            print(f"{day_str}: {ui.format_distance(target)}")
        else:
            print(f"{day_str}: -")


def browse_date() -> None:
    """Browse dates using up/down arrows."""
    today = date.today()
    offset = 0  # Days from today

    while True:
        ui.clear_screen()
        current_date = today + timedelta(days=offset)
        target = plan.get_target(current_date)

        ui.print_header("Browse Date")
        print(f"{ui.format_date_full(current_date)}")
        print(f"{ui.format_date_short(current_date)}")
        ui.print_divider()

        if target is not None:
            print(f"Target: {ui.format_distance(target)}")
        else:
            print("Target: -")

        # Past dates: show logged vs target
        if current_date < today:
            actual = db.get_run(current_date)
            if actual is not None:
                print(f"Logged: {ui.format_distance(actual)}")
                if target and target > 0:
                    diff = actual - target
                    print(f"Diff:   {diff:+.1f} km")
            else:
                print("Logged: -")
        elif current_date == today:
            actual = db.get_run(current_date)
            if actual is not None:
                print(f"Logged: {ui.format_distance(actual)}")

        ui.print_divider()
        print("Up=past Down=future Q=quit")

        key = ui.read_key()
        if key == 'up':
            offset -= 1
        elif key == 'down':
            offset += 1
        elif key == 'q':
            break


def show_week() -> None:
    """Show this week's summary."""
    today = date.today()
    monday, sunday = ui.get_week_bounds(today)

    ui.print_header("This Week")
    print(f"{ui.format_date_short(monday)} - {ui.format_date_short(sunday)}")
    ui.print_divider()

    runs = dict(db.get_runs_in_range(monday, sunday))
    targets = plan.get_targets_in_range(monday, sunday)

    total_actual = 0.0
    total_target = 0.0

    current = monday
    while current <= sunday:
        actual = runs.get(current)
        target = targets.get(current)

        day_marker = ">" if current == today else " "
        day_str = ui.format_date_short(current)

        if actual is not None:
            total_actual += actual
            status = ui.format_comparison(actual, target)
        elif target is not None:
            status = f"Target: {ui.format_distance(target)}"
        else:
            status = "-"

        if target:
            total_target += target

        print(f"{day_marker}{day_str}: {status}")
        current += __import__('datetime').timedelta(days=1)

    ui.print_divider()
    print(f"Week total: {ui.format_distance(total_actual)}")
    if total_target > 0:
        pct = (total_actual / total_target) * 100
        print(f"vs target:  {pct:.0f}%")


def show_history() -> None:
    """Show all logged runs."""
    runs = db.get_all_runs()

    ui.print_header("History")

    if not runs:
        print("No runs logged yet")
        return

    training_plan = plan.load_plan()

    for run_date, distance in runs[:20]:  # Show last 20
        target = training_plan.get(run_date)
        comparison = ui.format_comparison(distance, target)
        print(f"{ui.format_date_full(run_date)}: {comparison}")

    if len(runs) > 20:
        print(f"... and {len(runs) - 20} more")


def export_csv() -> None:
    """Export all runs to CSV."""
    runs = db.get_all_runs()
    training_plan = plan.load_plan()

    export_path = Path.home() / "running-log-export.csv"

    with open(export_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "distance_km", "target_km", "difference"])

        for run_date, distance in sorted(runs):
            target = training_plan.get(run_date, 0)
            diff = distance - target if target else distance
            writer.writerow([
                run_date.isoformat(),
                f"{distance:.1f}",
                f"{target:.1f}" if target else "",
                f"{diff:+.1f}" if target else ""
            ])

    ui.print_success(f"Exported {len(runs)} runs to ~/running-log-export.csv")


def import_plan() -> None:
    """Import training plan from CSV file."""
    print("Enter CSV file path:")
    csv_path = input("> ").strip()

    if not csv_path:
        ui.print_error("No path entered")
        return

    csv_path = Path(csv_path).expanduser()
    if not csv_path.exists():
        ui.print_error("File not found")
        return

    try:
        count = plan.import_from_csv(str(csv_path))
        ui.print_success(f"Imported {count} training days")
    except Exception as e:
        ui.print_error(f"Import failed: {e}")


def show_stats() -> None:
    """Show overall statistics."""
    ui.print_header("Stats")

    total_distance = db.get_total_distance()
    run_count = db.get_run_count()
    total_planned = plan.get_total_planned()
    planned_days = plan.get_planned_days()

    print(f"Total logged: {ui.format_distance(total_distance)}")
    print(f"Days run:     {run_count}")

    if total_planned > 0:
        pct = (total_distance / total_planned) * 100
        print(f"Plan total:   {ui.format_distance(total_planned)}")
        print(f"Completed:    {pct:.1f}%")

    if planned_days > 0:
        day_pct = (run_count / planned_days) * 100
        print(f"Days done:    {run_count}/{planned_days} ({day_pct:.0f}%)")

    # Goal tracking
    goal_km = 50
    if total_distance > 0:
        print(f"\n50km goal:    {(total_distance/goal_km)*100:.1f}%")


def main() -> None:
    """Main menu loop."""
    while True:
        ui.clear_screen()
        show_menu()

        choice = ui.prompt_choice(">", 8)

        if choice is None:
            ui.print_error("Invalid choice")
            ui.wait_for_key()
            continue

        if choice == 0:
            print("Goodbye!")
            break
        elif choice == 1:
            log_run()
        elif choice == 2:
            show_upcoming_targets()
        elif choice == 3:
            browse_date()
        elif choice == 4:
            show_week()
        elif choice == 5:
            show_history()
        elif choice == 6:
            export_csv()
        elif choice == 7:
            import_plan()
        elif choice == 8:
            show_stats()

        if choice != 0:
            ui.wait_for_key()


if __name__ == "__main__":
    main()
