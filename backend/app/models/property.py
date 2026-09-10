import enum
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Enum as SAEnum, Integer, Text, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database import Base


class PropertyType(str, enum.Enum):
    self = "Self"
    one_bedroom = "One bedroom"
    two_bedroom = "Two bedroom"
    three_bedroom = "Three bedroom"
    store = "Store"
    duplex = "Duplex"


class Property(Base):
    __tablename__ = "properties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    property_type: Mapped[PropertyType] = mapped_column(
        SAEnum(PropertyType, values_callable=lambda x: [e.value for e in x], native_enum=False),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    default_rent: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    leases: Mapped[list["Lease"]] = relationship(  # noqa: F821
        "Lease", back_populates="property"
    )
