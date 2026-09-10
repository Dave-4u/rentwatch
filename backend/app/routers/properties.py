from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from backend.app.database import get_db
from backend.app.deps import require_approved, require_landlord, require_staff
from backend.app.models.lease import Lease, LeaseStatus
from backend.app.models.property import Property
from backend.app.models.user import User, UserRole
from backend.app.schemas.property import PropertyCreate, PropertyOut, PropertyUpdate

router = APIRouter(prefix="/properties", tags=["properties"])


@router.get("", response_model=list[PropertyOut])
def list_properties(
    db: Session = Depends(get_db), user: User = Depends(require_approved)
):
    if user.role in (UserRole.landlord, UserRole.agent):
        return db.query(Property).order_by(Property.name.asc()).all()
    # Tenants: only properties with an active lease assignment
    leases = (
        db.query(Lease)
        .filter(Lease.tenant_id == user.id, Lease.status == LeaseStatus.active)
        .options(joinedload(Lease.property))
        .all()
    )
    props = {l.property_id: l.property for l in leases if l.property}
    return list(props.values())


@router.post("", response_model=PropertyOut, status_code=201)
def create_property(
    payload: PropertyCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_landlord),
):
    count = db.query(Property).count()
    if count >= 100:
        raise HTTPException(status_code=400, detail="Property limit reached (100)")
    prop = Property(**payload.model_dump())
    db.add(prop)
    db.commit()
    db.refresh(prop)
    return prop


@router.get("/{property_id}", response_model=PropertyOut)
def get_property(
    property_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_approved),
):
    prop = db.get(Property, property_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    if user.role == UserRole.tenant:
        lease = (
            db.query(Lease)
            .filter(Lease.property_id == property_id, Lease.tenant_id == user.id)
            .first()
        )
        if not lease:
            raise HTTPException(status_code=403, detail="Not assigned to this property")
    return prop


@router.patch("/{property_id}", response_model=PropertyOut)
def update_property(
    property_id: int,
    payload: PropertyUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_staff),
):
    prop = db.get(Property, property_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(prop, k, v)
    db.commit()
    db.refresh(prop)
    return prop


@router.delete("/{property_id}", status_code=204)
def delete_property(
    property_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_landlord),
):
    prop = db.get(Property, property_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    active = (
        db.query(Lease)
        .filter(Lease.property_id == property_id, Lease.status == LeaseStatus.active)
        .count()
    )
    if active:
        raise HTTPException(status_code=400, detail="Cannot delete property with active leases")
    db.delete(prop)
    db.commit()
    return None
