"""Run overdue checks and create notifications when needed."""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session, joinedload

from backend.app.models.lease import Lease, LeaseStatus
from backend.app.models.notification import Notification
from backend.app.services.overdue import (
    balance_due_for_period,
    current_period,
    effective_due_date,
    is_lease_overdue,
)


def lease_payment_dicts(lease: Lease) -> list[dict]:
    return [{"period_key": p.period_key, "amount": p.amount} for p in lease.payments]


def _lease_due(lease: Lease) -> date:
    return effective_due_date(
        due_date=lease.due_date,
        due_day=lease.due_day,
        start_date=lease.start_date,
    )


def check_and_notify_overdue(db: Session, today: date | None = None) -> list[Lease]:
    today = today or date.today()
    leases = (
        db.query(Lease)
        .options(joinedload(Lease.payments), joinedload(Lease.property), joinedload(Lease.tenant))
        .filter(Lease.status == LeaseStatus.active)
        .all()
    )
    overdue: list[Lease] = []
    for lease in leases:
        payments = lease_payment_dicts(lease)
        billing = lease.billing_period or "yearly"
        resolved = _lease_due(lease)
        if not is_lease_overdue(
            rent_amount=lease.rent_amount,
            start_date=lease.start_date,
            status=lease.status.value,
            payments=payments,
            today=today,
            billing_period=billing,
            due_date=resolved,
            due_day=lease.due_day,
        ):
            continue
        overdue.append(lease)
        period = current_period(today, billing_period=billing, due_date=resolved)
        bal = balance_due_for_period(
            rent_amount=lease.rent_amount,
            payments=payments,
            period=period,
            today=today,
            billing_period=billing,
            due_date=resolved,
        )
        prop_name = lease.property.name if lease.property else f"Property #{lease.property_id}"
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
    billing = lease.billing_period or "yearly"
    resolved = _lease_due(lease)
    period = current_period(today, billing_period=billing, due_date=resolved)
    overdue = is_lease_overdue(
        rent_amount=lease.rent_amount,
        start_date=lease.start_date,
        status=lease.status.value,
        payments=payments,
        today=today,
        billing_period=billing,
        due_date=resolved,
        due_day=lease.due_day,
    )
    bal = balance_due_for_period(
        rent_amount=lease.rent_amount,
        payments=payments,
        period=period,
        today=today,
        billing_period=billing,
        due_date=resolved,
    )
    return {
        "id": lease.id,
        "property_id": lease.property_id,
        "tenant_id": lease.tenant_id,
        "rent_amount": lease.rent_amount,
        "billing_period": billing,
        "due_day": lease.due_day if lease.due_day is not None else resolved.day,
        "due_date": resolved,
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
