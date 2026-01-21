"""SQLite database operations for run logging."""

import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Optional


def get_db_path() -> Path:
    """Get the database file path, creating directory if needed."""
    db_dir = Path.home() / ".running-log"
    db_dir.mkdir(exist_ok=True)
    return db_dir / "runs.db"


def get_connection() -> sqlite3.Connection:
    """Get a database connection, creating tables if needed."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    _init_db(conn)
    return conn


def _init_db(conn: sqlite3.Connection) -> None:
    """Initialize database schema."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL UNIQUE,
            distance_km REAL NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()


def log_run(run_date: date, distance_km: float) -> None:
    """Log a run for a given date. Updates if entry exists."""
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO runs (date, distance_km, created_at)
            VALUES (?, ?, ?)
            ON CONFLICT(date) DO UPDATE SET
                distance_km = excluded.distance_km,
                created_at = excluded.created_at
        """, (run_date.isoformat(), distance_km, datetime.now().isoformat()))
        conn.commit()
    finally:
        conn.close()


def get_run(run_date: date) -> Optional[float]:
    """Get distance for a specific date, or None if not logged."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT distance_km FROM runs WHERE date = ?",
            (run_date.isoformat(),)
        ).fetchone()
        return row["distance_km"] if row else None
    finally:
        conn.close()


def get_runs_in_range(start_date: date, end_date: date) -> list[tuple[date, float]]:
    """Get all runs within a date range (inclusive)."""
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT date, distance_km FROM runs
            WHERE date >= ? AND date <= ?
            ORDER BY date
        """, (start_date.isoformat(), end_date.isoformat())).fetchall()
        return [(date.fromisoformat(r["date"]), r["distance_km"]) for r in rows]
    finally:
        conn.close()


def get_all_runs() -> list[tuple[date, float]]:
    """Get all logged runs ordered by date."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT date, distance_km FROM runs ORDER BY date DESC"
        ).fetchall()
        return [(date.fromisoformat(r["date"]), r["distance_km"]) for r in rows]
    finally:
        conn.close()


def get_total_distance() -> float:
    """Get total distance logged across all runs."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT COALESCE(SUM(distance_km), 0) as total FROM runs"
        ).fetchone()
        return row["total"]
    finally:
        conn.close()


def get_run_count() -> int:
    """Get number of days with logged runs."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT COUNT(*) as count FROM runs").fetchone()
        return row["count"]
    finally:
        conn.close()
