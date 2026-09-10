from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.deps import require_staff
from backend.app.models.lease import Lease, LeaseStatus
from backend.app.models.notification import Notification
from backend.app.models.user import User, UserRole, UserStatus
from backend.app.schemas.user import UserOut

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/pending-users", response_model=list[UserOut])
def pending_users(db: Session = Depends(get_db), _: User = Depends(require_staff)):
    return (
        db.query(User)
        .filter(
            User.status == UserStatus.pending,
            User.role != UserRole.landlord,
        )
        .order_by(User.created_at.asc())
        .all()
    )


@router.get("/users", response_model=list[UserOut])
def list_users(
    role: UserRole | None = Query(default=None),
    db: Session = Depends(get_db),
    staff: User = Depends(require_staff),
):
    q = db.query(User).filter(User.status != UserStatus.deleted)
    if staff.role == UserRole.agent:
        # Agents manage tenants only
        q = q.filter(User.role == UserRole.tenant)
    else:
        q = q.filter(User.role != UserRole.landlord)
    if role is not None:
        if staff.role == UserRole.agent and role != UserRole.tenant:
            raise HTTPException(status_code=403, detail="Agents can only list tenants")
        q = q.filter(User.role == role)
    return q.order_by(User.role.asc(), User.full_name.asc()).all()


@router.post("/users/{user_id}/approve", response_model=UserOut)
def approve_user(
    user_id: int, db: Session = Depends(get_db), staff: User = Depends(require_staff)
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role == UserRole.landlord:
        raise HTTPException(status_code=400, detail="Cannot change landlord")
    if user.status == UserStatus.deleted:
        raise HTTPException(status_code=400, detail="Cannot approve a deleted account")
    user.status = UserStatus.approved
    user.approved_by_id = staff.id
    user.approved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    return user


@router.post("/users/{user_id}/reject", response_model=UserOut)
def reject_user(
    user_id: int, db: Session = Depends(get_db), staff: User = Depends(require_staff)
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role == UserRole.landlord:
        raise HTTPException(status_code=400, detail="Cannot change landlord")
    if user.status == UserStatus.deleted:
        raise HTTPException(status_code=400, detail="Account already deleted")
    user.status = UserStatus.rejected
    user.approved_by_id = staff.id
    user.approved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    return user


@router.post("/users/{user_id}/suspend", response_model=UserOut)
def suspend_user(
    user_id: int, db: Session = Depends(get_db), staff: User = Depends(require_staff)
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role == UserRole.landlord:
        raise HTTPException(status_code=400, detail="Cannot change landlord")
    if user.status == UserStatus.deleted:
        raise HTTPException(status_code=400, detail="Account already deleted")
    user.status = UserStatus.suspended
    user.approved_by_id = staff.id
    user.approved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}", response_model=UserOut)
def delete_user(
    user_id: int, db: Session = Depends(get_db), staff: User = Depends(require_staff)
):
    """
    Soft-delete an account. Ends active leases for tenants first so payment
    history stays attached to ended leases. Landlord-only for agents;
    landlord or agent for tenants. Cannot delete landlord or self.
    """
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if target.id == staff.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    if target.role == UserRole.landlord:
        raise HTTPException(status_code=400, detail="Cannot delete the landlord account")
    if target.status == UserStatus.deleted:
        raise HTTPException(status_code=400, detail="Account already deleted")
    if target.role == UserRole.agent:
        if staff.role != UserRole.landlord:
            raise HTTPException(status_code=403, detail="Only the landlord can delete agents")
    elif target.role == UserRole.tenant:
        if staff.role not in (UserRole.landlord, UserRole.agent):
            raise HTTPException(status_code=403, detail="Staff only")
    else:
        raise HTTPException(status_code=400, detail="Unsupported role")

    # End active leases so the tenant is unassigned; keep rows for payment history
    active_leases = (
        db.query(Lease)
        .filter(Lease.tenant_id == target.id, Lease.status == LeaseStatus.active)
        .all()
    )
    for lease in active_leases:
        lease.status = LeaseStatus.ended

    # Drop pending notifications for the deleted account
    db.query(Notification).filter(Notification.user_id == target.id).delete(
        synchronize_session=False
    )

    target.status = UserStatus.deleted
    target.approved_by_id = staff.id
    target.approved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(target)
    return target
