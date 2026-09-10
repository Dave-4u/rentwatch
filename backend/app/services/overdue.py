"""Overdue rent helpers — pure functions for tests and API use."""

from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime, timezone
from typing import Iterable


def anniversary_on_year(anchor: date, year: int) -> date:
    """Map an anniversary (month/day) onto a specific year."""
    last = monthrange(year, anchor.month)[1]
    day = min(anchor.day, last)
    return date(year, anchor.month, day)


def period_key_for(d: date, billing_period: str = "yearly") -> str:
    if billing_period == "monthly":
        return f"{d.year:04d}-{d.month:02d}"
    return f"{d.year:04d}"


def current_period(
    today: date | None = None,
    *,
    billing_period: str = "yearly",
    due_date: date | None = None,
) -> str:
    today = today or date.today()
    if billing_period == "monthly":
        return period_key_for(today, "monthly")
    if due_date is None:
        return f"{today.year:04d}"
    this_ann = anniversary_on_year(due_date, today.year)
    if today >= this_ann:
        return f"{today.year:04d}"
    return f"{today.year - 1:04d}"


def due_date_for_period(
    period: str,
    *,
    due_date: date | None = None,
    due_day: int | None = None,
    billing_period: str = "yearly",
) -> date:
    """Calendar due date for a billing period key."""
    if billing_period == "monthly" or (len(period) == 7 and period[4] == "-"):
        year, month = map(int, period.split("-"))
        day = due_day if due_day is not None else (due_date.day if due_date else 1)
        day = max(1, min(28, day))
        last = monthrange(year, month)[1]
        day = min(day, last)
        return date(year, month, day)

    year = int(period[:4])
    if due_date is not None:
        return anniversary_on_year(due_date, year)
    day = max(1, min(28, due_day or 1))
    return date(year, 1, day)


def effective_due_date(
    *,
    due_date: date | None,
    due_day: int | None,
    start_date: date,
) -> date:
    """Resolve a lease due date, deriving from due_day + start_date when needed."""
    if due_date is not None:
        return due_date
    day = max(1, min(28, due_day or 1))
    last = monthrange(start_date.year, start_date.month)[1]
    day = min(day, last)
    return date(start_date.year, start_date.month, day)


def payments_sum_for_period(payments: Iterable[dict], period: str) -> float:
    total = 0.0
    for p in payments:
        if p.get("period_key") == period:
            total += float(p.get("amount") or 0)
    return total


def is_lease_overdue(
    *,
    rent_amount: float,
    start_date: date,
    status: str,
    payments: Iterable[dict],
    today: date | None = None,
    billing_period: str = "yearly",
    due_date: date | None = None,
    due_day: int | None = None,
) -> bool:
    """Active lease is overdue if after the period due date and payments < rent."""
    if status != "active":
        return False
    today = today or date.today()
    if today < start_date:
        return False

    resolved = effective_due_date(due_date=due_date, due_day=due_day, start_date=start_date)
    period = current_period(today, billing_period=billing_period, due_date=resolved)
    due = due_date_for_period(
        period,
        due_date=resolved,
        due_day=due_day if due_day is not None else resolved.day,
        billing_period=billing_period,
    )
    if start_date > due:
        return False
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
    billing_period: str = "yearly",
    due_date: date | None = None,
) -> float:
    period = period or current_period(
        today, billing_period=billing_period, due_date=due_date
    )
    paid = payments_sum_for_period(payments, period)
    return max(0.0, float(rent_amount) - paid)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
