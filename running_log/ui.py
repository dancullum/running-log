"""Display helpers for terminal UI."""

import sys
import tty
import termios
from datetime import date, timedelta
from typing import Optional


def format_distance(km: float) -> str:
    """Format distance for display."""
    if km == int(km):
        return f"{int(km)} km"
    return f"{km:.1f} km"


def format_date_short(d: date) -> str:
    """Format date for small screen (e.g., 'Mon 20')."""
    return d.strftime("%a %d")


def format_date_full(d: date) -> str:
    """Format date fully (e.g., '2025-01-20')."""
    return d.isoformat()


def format_comparison(actual: Optional[float], target: Optional[float]) -> str:
    """Format actual vs target comparison."""
    if actual is None and target is None:
        return "No data"

    if target is None or target == 0:
        if actual:
            return f"{format_distance(actual)} (no target)"
        return "Rest day"

    if actual is None:
        return f"Target: {format_distance(target)}"

    diff = actual - target
    if diff >= 0:
        return f"{format_distance(actual)} (+{diff:.1f})"
    return f"{format_distance(actual)} ({diff:.1f})"


def get_week_bounds(d: date) -> tuple[date, date]:
    """Get Monday and Sunday of the week containing date."""
    monday = d - timedelta(days=d.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday


def clear_screen() -> None:
    """Clear terminal screen."""
    print("\033[2J\033[H", end="")


def print_header(title: str) -> None:
    """Print a section header."""
    print(f"\n=== {title.upper()} ===")


def print_divider() -> None:
    """Print a visual divider."""
    print("-" * 20)


def print_success(msg: str) -> None:
    """Print success message with checkmark."""
    print(f"+ {msg}")


def print_error(msg: str) -> None:
    """Print error message."""
    print(f"! {msg}")


def prompt_float(msg: str) -> Optional[float]:
    """Prompt user for a float value. Returns None on invalid input."""
    try:
        value = input(f"{msg}: ").strip()
        if not value:
            return None
        return float(value)
    except (ValueError, EOFError):
        return None


def prompt_choice(msg: str, max_choice: int) -> Optional[int]:
    """Prompt user for a menu choice. Returns None on invalid input."""
    try:
        value = input(f"{msg}: ").strip()
        if not value:
            return None
        choice = int(value)
        if 0 <= choice <= max_choice:
            return choice
        return None
    except (ValueError, EOFError):
        return None


def wait_for_key() -> None:
    """Wait for user to press enter."""
    try:
        input("\nPress Enter...")
    except EOFError:
        pass


def read_key() -> str:
    """Read a single keypress, including arrow keys.

    Returns:
        'up', 'down', 'q', or the character pressed
    """
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)

        # Handle escape sequences (arrow keys)
        if ch == '\x1b':
            ch2 = sys.stdin.read(1)
            if ch2 == '[':
                ch3 = sys.stdin.read(1)
                if ch3 == 'A':
                    return 'up'
                elif ch3 == 'B':
                    return 'down'
        elif ch == 'q' or ch == 'Q':
            return 'q'
        elif ch == '\r' or ch == '\n':
            return 'enter'

        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
