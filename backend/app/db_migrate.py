"""Soft SQLite column adds for existing databases (no Alembic)."""

from __future__ import annotations

from calendar import monthrange
from datetime import date

from sqlalchemy import text
from sqlalchemy.engine import Engine


def _sqlite_columns(conn, table: str) -> set[str]:
    rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
    return {r[1] for r in rows}


def ensure_schema(engine: Engine) -> None:
    """Add missing columns and backfill due_date from due_day + start_date."""
    url = str(engine.url)
    if not url.startswith("sqlite"):
        return

    with engine.begin() as conn:
        tables = {
            r[0]
            for r in conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            ).fetchall()
        }
        if "leases" not in tables:
            return

        cols = _sqlite_columns(conn, "leases")
        if "due_date" not in cols:
            conn.execute(text("ALTER TABLE leases ADD COLUMN due_date DATE"))
            cols = _sqlite_columns(conn, "leases")

        if "due_date" in cols and "due_day" in cols and "start_date" in cols:
            rows = conn.execute(
                text(
                    "SELECT id, due_day, start_date, due_date FROM leases "
                    "WHERE due_date IS NULL AND due_day IS NOT NULL AND start_date IS NOT NULL"
                )
            ).fetchall()
            for row in rows:
                lease_id, due_day, start_date_raw, _ = row
                if isinstance(start_date_raw, date):
                    start = start_date_raw
                else:
                    start = date.fromisoformat(str(start_date_raw)[:10])
                day = max(1, min(28, int(due_day)))
                last = monthrange(start.year, start.month)[1]
                day = min(day, last)
                derived = date(start.year, start.month, day)
                conn.execute(
                    text("UPDATE leases SET due_date = :d WHERE id = :id"),
                    {"d": derived.isoformat(), "id": lease_id},
                )

        # Prefer yearly for rows still on the old monthly default with a due_date set
        if "billing_period" in cols:
            conn.execute(
                text(
                    "UPDATE leases SET billing_period = 'yearly' "
                    "WHERE billing_period IS NULL OR billing_period = ''"
                )
            )
