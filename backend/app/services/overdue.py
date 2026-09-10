"""Overdue rent helpers — pure functions for tests and API use."""

from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime, timezone
from typing import Iterable


def period_key_for(d: date) -> str:
    return f"{d.year:04d}-{d.month:02d}"


def current_period(today: date | None = None) -> str:
    return period_key_for(today or date.today())


def due_date_for_period(period: str, due_day: int) -> date:
    """Return the due date within a YYYY-MM period (clamped to 1–28)."""
    year, month = map(int, period.split("-"))
    day = max(1, min(28, due_day))
    last = monthrange(year, month)[1]
    day = min(day, last)
    return date(year, month, day)


def payments_sum_for_period(payments: Iterable[dict], period: str) -> float:
    total = 0.0
    for p in payments:
        if p.get("period_key") == period:
            total += float(p.get("amount") or 0)
    return total


def is_lease_overdue(
    *,
    rent_amount: float,
    due_day: int,
    start_date: date,
    status: str,
    payments: Iterable[dict],
    today: date | None = None,
) -> bool:
    """Active lease is overdue if after due date and period payments < rent."""
    if status != "active":
        return False
    today = today or date.today()
    if today < start_date:
        return False
    period = period_key_for(today)
    # Lease must have started before or during this period
    if period_key_for(start_date) > period:
        return False
    due = due_date_for_period(period, due_day)
    if today <= due:
        return False
    paid = payments_sum_for_period(payments, period)
    return paid < float(rent_amount)


def balance_due_for_period(
    *,
    rent_amount: float,
    payments: Iterable[dict],
    period: str | None = None,
    today: date | None = None,
) -> float:
    period = period or current_period(today)
    paid = payments_sum_for_period(payments, period)
    return max(0.0, float(rent_amount) - paid)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
