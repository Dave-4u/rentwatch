from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from backend.app.database import get_db
from backend.app.deps import require_approved
from backend.app.models.lease import Lease, LeaseStatus
from backend.app.models.notification import Notification
from backend.app.models.payment import Payment
from backend.app.models.property import Property
from backend.app.models.user import User, UserRole, UserStatus
from backend.app.schemas.dashboard import AgentDashboard, LandlordDashboard, TenantDashboard
from backend.app.schemas.lease import LeaseOut
from backend.app.schemas.payment import PaymentOut
from backend.app.services.overdue_runner import check_and_notify_overdue, enrich_lease

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/landlord", response_model=LandlordDashboard)
def landlord_dashboard(db: Session = Depends(get_db), user: User = Depends(require_approved)):
    if user.role != UserRole.landlord:
        raise HTTPException(status_code=403, detail="Landlord only")
    overdue = check_and_notify_overdue(db)
    leases = (
        db.query(Lease)
        .options(joinedload(Lease.property), joinedload(Lease.tenant), joinedload(Lease.payments))
        .filter(Lease.status == LeaseStatus.active)
        .all()
    )
    overdue_out = [LeaseOut(**enrich_lease(l)) for l in leases if enrich_lease(l)["is_overdue"]]
    payments = db.query(Payment).order_by(Payment.paid_on.desc()).limit(10).all()
    pending = (
        db.query(User)
        .filter(User.status == UserStatus.pending, User.role != UserRole.landlord)
        .count()
    )
    return LandlordDashboard(
        property_count=db.query(Property).count(),
        active_leases=len(leases),
        pending_users=pending,
        overdue_count=len(overdue_out),
        overdue_leases=overdue_out,
        recent_payments=[PaymentOut.model_validate(p) for p in payments],
    )


@router.get("/agent", response_model=AgentDashboard)
def agent_dashboard(db: Session = Depends(get_db), user: User = Depends(require_approved)):
    if user.role != UserRole.agent:
        raise HTTPException(status_code=403, detail="Agent only")
    check_and_notify_overdue(db)
    leases = (
        db.query(Lease)
        .options(joinedload(Lease.property), joinedload(Lease.tenant), joinedload(Lease.payments))
        .filter(Lease.status == LeaseStatus.active)
        .all()
    )
    overdue_out = [LeaseOut(**enrich_lease(l)) for l in leases if enrich_lease(l)["is_overdue"]]
    payments = db.query(Payment).order_by(Payment.paid_on.desc()).limit(10).all()
    pending = (
        db.query(User)
        .filter(User.status == UserStatus.pending, User.role != UserRole.landlord)
        .count()
    )
    return AgentDashboard(
        property_count=db.query(Property).count(),
        active_leases=len(leases),
        pending_users=pending,
        overdue_count=len(overdue_out),
        overdue_leases=overdue_out,
        recent_payments=[PaymentOut.model_validate(p) for p in payments],
    )


@router.get("/tenant", response_model=TenantDashboard)
def tenant_dashboard(db: Session = Depends(get_db), user: User = Depends(require_approved)):
    if user.role != UserRole.tenant:
        raise HTTPException(status_code=403, detail="Tenant only")
    check_and_notify_overdue(db)
    leases = (
        db.query(Lease)
        .options(joinedload(Lease.property), joinedload(Lease.tenant), joinedload(Lease.payments))
        .filter(Lease.tenant_id == user.id)
        .all()
    )
    enriched = [LeaseOut(**enrich_lease(l)) for l in leases]
    payments = (
        db.query(Payment)
        .join(Lease)
        .filter(Lease.tenant_id == user.id)
        .order_by(Payment.paid_on.desc())
        .limit(20)
        .all()
    )
    unread = (
        db.query(Notification)
        .filter(Notification.user_id == user.id, Notification.is_read == False)  # noqa: E712
        .count()
    )
    total_bal = sum(l.balance_due or 0 for l in enriched if l.status == LeaseStatus.active)
    return TenantDashboard(
        leases=enriched,
        recent_payments=[PaymentOut.model_validate(p) for p in payments],
        unread_notifications=unread,
        total_balance_due=total_bal,
    )
