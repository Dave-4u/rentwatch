from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from backend.app.database import get_db
from backend.app.deps import require_approved, require_staff
from backend.app.models.lease import Lease
from backend.app.models.payment import Payment
from backend.app.models.user import User, UserRole
from backend.app.schemas.payment import PaymentCreate, PaymentOut
from backend.app.services.overdue import (
    current_period,
    effective_due_date,
)

router = APIRouter(prefix="/payments", tags=["payments"])


def _valid_period_key(period: str, billing_period: str) -> bool:
    if billing_period == "monthly":
        return len(period) == 7 and period[4] == "-" and period[:4].isdigit() and period[5:].isdigit()
    # yearly: YYYY
    return len(period) == 4 and period.isdigit()


@router.get("", response_model=list[PaymentOut])
def list_payments(
    lease_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(require_approved),
):
    q = db.query(Payment).options(joinedload(Payment.lease))
    if lease_id is not None:
        q = q.filter(Payment.lease_id == lease_id)
        lease = db.get(Lease, lease_id)
        if not lease:
            raise HTTPException(status_code=404, detail="Lease not found")
        if user.role == UserRole.tenant and lease.tenant_id != user.id:
            raise HTTPException(status_code=403, detail="Not your lease")
    elif user.role == UserRole.tenant:
        q = q.join(Lease).filter(Lease.tenant_id == user.id)
    return q.order_by(Payment.paid_on.desc(), Payment.id.desc()).all()


@router.post("", response_model=PaymentOut, status_code=201)
def create_payment(
    payload: PaymentCreate, db: Session = Depends(get_db), staff: User = Depends(require_staff)
):
    lease = db.get(Lease, payload.lease_id)
    if not lease:
        raise HTTPException(status_code=404, detail="Lease not found")
    billing = lease.billing_period or "yearly"
    resolved = effective_due_date(
        due_date=lease.due_date, due_day=lease.due_day, start_date=lease.start_date
    )
    if payload.period_key:
        period = payload.period_key
    else:
        period = current_period(
            payload.paid_on, billing_period=billing, due_date=resolved
        )
    if not _valid_period_key(period, billing):
        expect = "YYYY-MM" if billing == "monthly" else "YYYY"
        raise HTTPException(status_code=400, detail=f"period_key must be {expect}")
    payment = Payment(
        lease_id=payload.lease_id,
        amount=payload.amount,
        paid_on=payload.paid_on,
        method=payload.method,
        note=payload.note,
        recorded_by_id=staff.id,
        period_key=period,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment
