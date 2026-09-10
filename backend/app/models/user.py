import enum
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Enum as SAEnum, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database import Base


class UserRole(str, enum.Enum):
    landlord = "landlord"
    agent = "agent"
    tenant = "tenant"


class UserStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    suspended = "suspended"
    deleted = "deleted"


def _enum_col(enum_cls):
    return SAEnum(enum_cls, values_callable=lambda x: [e.value for e in x], native_enum=False)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    role: Mapped[UserRole] = mapped_column(_enum_col(UserRole), nullable=False)
    status: Mapped[UserStatus] = mapped_column(
        _enum_col(UserStatus), nullable=False, default=UserStatus.pending
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    approved_by_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    leases: Mapped[list["Lease"]] = relationship(  # noqa: F821
        "Lease", back_populates="tenant", foreign_keys="Lease.tenant_id"
    )
    notifications: Mapped[list["Notification"]] = relationship(  # noqa: F821
        "Notification", back_populates="user"
    )
