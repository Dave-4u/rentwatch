from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.user import User, UserRole, UserStatus
from backend.app.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    user_id = decode_access_token(token)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = db.get(User, int(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_approved(user: User = Depends(get_current_user)) -> User:
    if user.status != UserStatus.approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account pending approval or not active",
        )
    return user


def require_staff(user: User = Depends(require_approved)) -> User:
    if user.role not in (UserRole.landlord, UserRole.agent):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Staff only")
    return user


def require_landlord(user: User = Depends(require_approved)) -> User:
    if user.role != UserRole.landlord:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Landlord only")
    return user
