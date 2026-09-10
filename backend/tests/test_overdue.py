from datetime import date

from backend.app.services.overdue import (
    balance_due_for_period,
    due_date_for_period,
    is_lease_overdue,
    payments_sum_for_period,
    period_key_for,
)


def test_period_key():
    assert period_key_for(date(2026, 9, 10)) == "2026-09"


def test_due_date_clamped():
    assert due_date_for_period("2026-02", 28) == date(2026, 2, 28)
    assert due_date_for_period("2026-01", 1) == date(2026, 1, 1)


def test_payments_sum():
    payments = [
        {"period_key": "2026-09", "amount": 50_000},
        {"period_key": "2026-09", "amount": 20_000},
        {"period_key": "2026-08", "amount": 100_000},
    ]
    assert payments_sum_for_period(payments, "2026-09") == 70_000


def test_not_overdue_before_due_day():
    assert (
        is_lease_overdue(
            rent_amount=100_000,
            due_day=15,
            start_date=date(2026, 1, 1),
            status="active",
            payments=[],
            today=date(2026, 9, 10),
        )
        is False
    )


def test_overdue_after_due_unpaid():
    assert (
        is_lease_overdue(
            rent_amount=100_000,
            due_day=5,
            start_date=date(2026, 1, 1),
            status="active",
            payments=[],
            today=date(2026, 9, 10),
        )
        is True
    )


def test_not_overdue_when_fully_paid():
    payments = [{"period_key": "2026-09", "amount": 100_000}]
    assert (
        is_lease_overdue(
            rent_amount=100_000,
            due_day=5,
            start_date=date(2026, 1, 1),
            status="active",
            payments=payments,
            today=date(2026, 9, 10),
        )
        is False
    )


def test_partial_payment_still_overdue():
    payments = [{"period_key": "2026-09", "amount": 40_000}]
    assert (
        is_lease_overdue(
            rent_amount=100_000,
            due_day=5,
            start_date=date(2026, 1, 1),
            status="active",
            payments=payments,
            today=date(2026, 9, 10),
        )
        is True
    )
    assert balance_due_for_period(
        rent_amount=100_000, payments=payments, period="2026-09"
    ) == 60_000


def test_ended_lease_not_overdue():
    assert (
        is_lease_overdue(
            rent_amount=100_000,
            due_day=5,
            start_date=date(2026, 1, 1),
            status="ended",
            payments=[],
            today=date(2026, 9, 10),
        )
        is False
    )
