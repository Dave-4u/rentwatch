"""Seed the sole landlord account."""

from sqlalchemy.orm import Session

from backend.app.database import SessionLocal, Base, engine
from backend.app.models.user import User, UserRole, UserStatus
from backend.app.security import hash_password

LANDLORD_EMAIL = "landlord@rentwatch.local"
LANDLORD_PASSWORD = "ChangeMe123!"
LANDLORD_NAME = "Mr Eli Stephen"


def ensure_landlord(db: Session) -> User:
    user = db.query(User).filter(User.email == LANDLORD_EMAIL).first()
    if user:
        return user
    user = User(
        email=LANDLORD_EMAIL,
        hashed_password=hash_password(LANDLORD_PASSWORD),
        full_name=LANDLORD_NAME,
        phone=None,
        role=UserRole.landlord,
        status=UserStatus.approved,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        user = ensure_landlord(db)
        print(f"Landlord ready: {user.email} / {LANDLORD_PASSWORD}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
