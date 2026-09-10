from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from backend.app.database import get_db
from backend.app.deps import require_approved, require_staff
from backend.app.models.lease import Lease
from backend.app.models.payment import Payment
from backend.app.models.user import User, UserRole
from backend.app.schemas.payment import PaymentCreate, PaymentOut
from backend.app.services.overdue import period_key_for

router = APIRouter(prefix="/payments", tags=["payments"])


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
    period = payload.period_key or period_key_for(payload.paid_on)
    if len(period) != 7 or period[4] != "-":
        raise HTTPException(status_code=400, detail="period_key must be YYYY-MM")
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
