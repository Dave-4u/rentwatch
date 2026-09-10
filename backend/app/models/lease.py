import enum
from datetime import datetime, date, timezone

from sqlalchemy import String, DateTime, Date, Enum as SAEnum, Integer, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database import Base


class LeaseStatus(str, enum.Enum):
    active = "active"
    ended = "ended"


def _enum_col(enum_cls):
    return SAEnum(enum_cls, values_callable=lambda x: [e.value for e in x], native_enum=False)


class Lease(Base):
    __tablename__ = "leases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"), nullable=False)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    rent_amount: Mapped[float] = mapped_column(Float, nullable=False)
    billing_period: Mapped[str] = mapped_column(String(20), default="yearly", nullable=False)
    # Legacy day-of-month; kept for older rows / monthly leases. Prefer due_date.
    due_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[LeaseStatus] = mapped_column(
        _enum_col(LeaseStatus), nullable=False, default=LeaseStatus.active
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    property: Mapped["Property"] = relationship("Property", back_populates="leases")  # noqa: F821
    tenant: Mapped["User"] = relationship(  # noqa: F821
        "User", back_populates="leases", foreign_keys=[tenant_id]
    )
    payments: Mapped[list["Payment"]] = relationship(  # noqa: F821
        "Payment", back_populates="lease", cascade="all, delete-orphan"
    )
