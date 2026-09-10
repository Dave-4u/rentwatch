from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.deps import require_staff
from backend.app.models.user import User, UserRole, UserStatus
from backend.app.schemas.user import UserOut

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/pending-users", response_model=list[UserOut])
def pending_users(db: Session = Depends(get_db), _: User = Depends(require_staff)):
    return (
        db.query(User)
        .filter(User.status == UserStatus.pending, User.role != UserRole.landlord)
        .order_by(User.created_at.asc())
        .all()
    )


@router.post("/users/{user_id}/approve", response_model=UserOut)
def approve_user(
    user_id: int, db: Session = Depends(get_db), staff: User = Depends(require_staff)
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role == UserRole.landlord:
        raise HTTPException(status_code=400, detail="Cannot change landlord")
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
    user.status = UserStatus.suspended
    user.approved_by_id = staff.id
    user.approved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    return user
