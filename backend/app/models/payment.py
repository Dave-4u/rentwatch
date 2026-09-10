import enum
from datetime import datetime, date, timezone

from sqlalchemy import String, DateTime, Date, Enum as SAEnum, Integer, Float, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database import Base


class PaymentMethod(str, enum.Enum):
    cash = "cash"
    transfer = "transfer"
    other = "other"


def _enum_col(enum_cls):
    return SAEnum(enum_cls, values_callable=lambda x: [e.value for e in x], native_enum=False)


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    lease_id: Mapped[int] = mapped_column(ForeignKey("leases.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    paid_on: Mapped[date] = mapped_column(Date, nullable=False)
    method: Mapped[PaymentMethod] = mapped_column(_enum_col(PaymentMethod), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    recorded_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    period_key: Mapped[str] = mapped_column(String(16), nullable=False)

    lease: Mapped["Lease"] = relationship("Lease", back_populates="payments")  # noqa: F821
