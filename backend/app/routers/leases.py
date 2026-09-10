from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from backend.app.database import get_db
from backend.app.deps import require_approved, require_staff
from backend.app.models.lease import Lease
from backend.app.models.property import Property
from backend.app.models.user import User, UserRole, UserStatus
from backend.app.schemas.lease import LeaseCreate, LeaseOut, LeaseUpdate
from backend.app.services.overdue_runner import check_and_notify_overdue, enrich_lease

router = APIRouter(prefix="/leases", tags=["leases"])


@router.get("", response_model=list[LeaseOut])
def list_leases(db: Session = Depends(get_db), user: User = Depends(require_approved)):
    check_and_notify_overdue(db)
    q = db.query(Lease).options(
        joinedload(Lease.property), joinedload(Lease.tenant), joinedload(Lease.payments)
    )
    if user.role == UserRole.tenant:
        q = q.filter(Lease.tenant_id == user.id)
    leases = q.order_by(Lease.id.desc()).all()
    return [LeaseOut(**enrich_lease(l)) for l in leases]


@router.get("/meta/tenants")
def list_tenants_for_lease(db: Session = Depends(get_db), _: User = Depends(require_staff)):
    tenants = (
        db.query(User)
        .filter(User.role == UserRole.tenant, User.status == UserStatus.approved)
        .order_by(User.full_name.asc())
        .all()
    )
    return [{"id": t.id, "full_name": t.full_name, "email": t.email} for t in tenants]


@router.post("", response_model=LeaseOut, status_code=201)
def create_lease(
    payload: LeaseCreate, db: Session = Depends(get_db), _: User = Depends(require_staff)
):
    prop = db.get(Property, payload.property_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    tenant = db.get(User, payload.tenant_id)
    if not tenant or tenant.role != UserRole.tenant:
        raise HTTPException(status_code=400, detail="tenant_id must be a tenant user")
    if tenant.status != UserStatus.approved:
        raise HTTPException(status_code=400, detail="Tenant must be approved")
    lease = Lease(
        property_id=payload.property_id,
        tenant_id=payload.tenant_id,
        rent_amount=payload.rent_amount,
        due_day=payload.due_day,
        start_date=payload.start_date,
        status=payload.status,
        billing_period="monthly",
    )
    db.add(lease)
    db.commit()
    db.refresh(lease)
    lease = (
        db.query(Lease)
        .options(joinedload(Lease.property), joinedload(Lease.tenant), joinedload(Lease.payments))
        .filter(Lease.id == lease.id)
        .one()
    )
    return LeaseOut(**enrich_lease(lease))


@router.get("/{lease_id}", response_model=LeaseOut)
def get_lease(
    lease_id: int, db: Session = Depends(get_db), user: User = Depends(require_approved)
):
    lease = (
        db.query(Lease)
        .options(joinedload(Lease.property), joinedload(Lease.tenant), joinedload(Lease.payments))
        .filter(Lease.id == lease_id)
        .first()
    )
    if not lease:
        raise HTTPException(status_code=404, detail="Lease not found")
    if user.role == UserRole.tenant and lease.tenant_id != user.id:
        raise HTTPException(status_code=403, detail="Not your lease")
    return LeaseOut(**enrich_lease(lease))


@router.patch("/{lease_id}", response_model=LeaseOut)
def update_lease(
    lease_id: int,
    payload: LeaseUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
):
    lease = db.get(Lease, lease_id)
    if not lease:
        raise HTTPException(status_code=404, detail="Lease not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(lease, k, v)
    db.commit()
    lease = (
        db.query(Lease)
        .options(joinedload(Lease.property), joinedload(Lease.tenant), joinedload(Lease.payments))
        .filter(Lease.id == lease_id)
        .one()
    )
    return LeaseOut(**enrich_lease(lease))


@router.delete("/{lease_id}", status_code=204)
def delete_lease(
    lease_id: int, db: Session = Depends(get_db), _: User = Depends(require_staff)
):
    lease = db.get(Lease, lease_id)
    if not lease:
        raise HTTPException(status_code=404, detail="Lease not found")
    db.delete(lease)
    db.commit()
    return None
