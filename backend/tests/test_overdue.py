from datetime import date

from backend.app.services.overdue import (
    balance_due_for_period,
    current_period,
    due_date_for_period,
    is_lease_overdue,
    payments_sum_for_period,
    period_key_for,
)


def test_period_key_yearly_and_monthly():
    assert period_key_for(date(2026, 9, 10), "yearly") == "2026"
    assert period_key_for(date(2026, 9, 10), "monthly") == "2026-09"


def test_current_period_yearly_anniversary():
    due = date(2025, 9, 10)
    # Before anniversary in 2026 → still rent year 2025
    assert current_period(date(2026, 9, 9), billing_period="yearly", due_date=due) == "2025"
    # On/after anniversary → rent year 2026
    assert current_period(date(2026, 9, 10), billing_period="yearly", due_date=due) == "2026"
    assert current_period(date(2026, 12, 1), billing_period="yearly", due_date=due) == "2026"


def test_due_date_for_yearly_period():
    due = date(2025, 9, 10)
    assert due_date_for_period("2026", due_date=due, billing_period="yearly") == date(2026, 9, 10)


def test_due_date_monthly_clamped():
    assert due_date_for_period("2026-02", due_day=28, billing_period="monthly") == date(2026, 2, 28)
    assert due_date_for_period("2026-01", due_day=1, billing_period="monthly") == date(2026, 1, 1)


def test_payments_sum():
    payments = [
        {"period_key": "2026", "amount": 50_000},
        {"period_key": "2026", "amount": 20_000},
        {"period_key": "2025", "amount": 100_000},
    ]
    assert payments_sum_for_period(payments, "2026") == 70_000


def test_not_overdue_before_yearly_due():
    # Before this year's anniversary; prior rent year paid → not overdue yet
    payments = [{"period_key": "2025", "amount": 100_000}]
    assert (
        is_lease_overdue(
            rent_amount=100_000,
            due_date=date(2025, 9, 15),
            start_date=date(2025, 1, 1),
            status="active",
            payments=payments,
            today=date(2026, 9, 10),
            billing_period="yearly",
        )
        is False
    )
    # First rent year not due yet (start after prior anniversary)
    assert (
        is_lease_overdue(
            rent_amount=100_000,
            due_date=date(2026, 9, 15),
            start_date=date(2026, 1, 1),
            status="active",
            payments=[],
            today=date(2026, 9, 10),
            billing_period="yearly",
        )
        is False
    )


def test_overdue_after_yearly_due_unpaid():
    assert (
        is_lease_overdue(
            rent_amount=100_000,
            due_date=date(2026, 9, 5),
            start_date=date(2025, 1, 1),
            status="active",
            payments=[],
            today=date(2026, 9, 10),
            billing_period="yearly",
        )
        is True
    )


def test_not_overdue_when_fully_paid_yearly():
    payments = [{"period_key": "2026", "amount": 100_000}]
    assert (
        is_lease_overdue(
            rent_amount=100_000,
            due_date=date(2026, 9, 5),
            start_date=date(2025, 1, 1),
            status="active",
            payments=payments,
            today=date(2026, 9, 10),
            billing_period="yearly",
        )
        is False
    )


def test_partial_payment_still_overdue_yearly():
    payments = [{"period_key": "2026", "amount": 40_000}]
    assert (
        is_lease_overdue(
            rent_amount=100_000,
            due_date=date(2026, 9, 5),
            start_date=date(2025, 1, 1),
            status="active",
            payments=payments,
            today=date(2026, 9, 10),
            billing_period="yearly",
        )
        is True
    )
    assert (
        balance_due_for_period(
            rent_amount=100_000,
            payments=payments,
            period="2026",
            billing_period="yearly",
            due_date=date(2026, 9, 5),
        )
        == 60_000
    )


def test_ended_lease_not_overdue():
    assert (
        is_lease_overdue(
            rent_amount=100_000,
            due_date=date(2026, 9, 5),
            start_date=date(2025, 1, 1),
            status="ended",
            payments=[],
            today=date(2026, 9, 10),
            billing_period="yearly",
        )
        is False
    )


def test_monthly_overdue_still_works():
    assert (
        is_lease_overdue(
            rent_amount=100_000,
            due_day=5,
            due_date=date(2026, 1, 5),
            start_date=date(2026, 1, 1),
            status="active",
            payments=[],
            today=date(2026, 9, 10),
            billing_period="monthly",
        )
        is True
    )
    assert (
        is_lease_overdue(
            rent_amount=100_000,
            due_day=15,
            due_date=date(2026, 1, 15),
            start_date=date(2026, 1, 1),
            status="active",
            payments=[],
            today=date(2026, 9, 10),
            billing_period="monthly",
        )
        is False
    )
