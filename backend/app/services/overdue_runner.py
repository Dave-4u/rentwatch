"""Run overdue checks and create notifications when needed."""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session, joinedload

from backend.app.models.lease import Lease, LeaseStatus
from backend.app.models.notification import Notification
from backend.app.models.user import User, UserRole, UserStatus
from backend.app.services.overdue import (
    balance_due_for_period,
    current_period,
    is_lease_overdue,
    period_key_for,
)


def lease_payment_dicts(lease: Lease) -> list[dict]:
    return [{"period_key": p.period_key, "amount": p.amount} for p in lease.payments]


def check_and_notify_overdue(db: Session, today: date | None = None) -> list[Lease]:
    today = today or date.today()
    period = current_period(today)
    leases = (
        db.query(Lease)
        .options(joinedload(Lease.payments), joinedload(Lease.property), joinedload(Lease.tenant))
        .filter(Lease.status == LeaseStatus.active)
        .all()
    )
    overdue: list[Lease] = []
    for lease in leases:
        payments = lease_payment_dicts(lease)
        if not is_lease_overdue(
            rent_amount=lease.rent_amount,
            due_day=lease.due_day,
            start_date=lease.start_date,
            status=lease.status.value,
            payments=payments,
            today=today,
        ):
            continue
        overdue.append(lease)
        bal = balance_due_for_period(
            rent_amount=lease.rent_amount, payments=payments, period=period, today=today
        )
        prop_name = lease.property.name if lease.property else f"Property #{lease.property_id}"
        # Notify tenant once per period (avoid duplicates by title+period in message)
        marker = f"[overdue:{period}:lease:{lease.id}]"
        existing = (
            db.query(Notification)
            .filter(
                Notification.user_id == lease.tenant_id,
                Notification.message.contains(marker),
            )
            .first()
        )
        if not existing:
            db.add(
                Notification(
                    user_id=lease.tenant_id,
                    title="Rent overdue",
                    message=(
                        f"Your rent for {prop_name} ({period}) is overdue. "
                        f"Balance due: NGN {bal:,.2f}. {marker}"
                    ),
                )
            )
    if overdue:
        db.commit()
    return overdue


def enrich_lease(lease: Lease, today: date | None = None) -> dict:
    today = today or date.today()
    payments = lease_payment_dicts(lease)
    period = current_period(today)
    overdue = is_lease_overdue(
        rent_amount=lease.rent_amount,
        due_day=lease.due_day,
        start_date=lease.start_date,
        status=lease.status.value,
        payments=payments,
        today=today,
    )
    bal = balance_due_for_period(
        rent_amount=lease.rent_amount, payments=payments, period=period, today=today
    )
    return {
        "id": lease.id,
        "property_id": lease.property_id,
        "tenant_id": lease.tenant_id,
        "rent_amount": lease.rent_amount,
        "billing_period": lease.billing_period,
        "due_day": lease.due_day,
        "start_date": lease.start_date,
        "status": lease.status,
        "created_at": lease.created_at,
        "property_name": lease.property.name if lease.property else None,
        "property_type": (
            lease.property.property_type.value
            if lease.property and getattr(lease.property, "property_type", None)
            else None
        ),
        "tenant_name": lease.tenant.full_name if lease.tenant else None,
        "is_overdue": overdue,
        "balance_due": bal,
        "current_period": period,
    }
