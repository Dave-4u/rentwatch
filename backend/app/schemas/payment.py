from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field

from backend.app.models.payment import PaymentMethod


class PaymentCreate(BaseModel):
    lease_id: int
    amount: float = Field(gt=0)
    paid_on: date
    method: PaymentMethod
    note: Optional[str] = None
    # Yearly: YYYY ; monthly: YYYY-MM. Defaults from lease + paid_on.
    period_key: Optional[str] = None


class PaymentOut(BaseModel):
    id: int
    lease_id: int
    amount: float
    paid_on: date
    method: PaymentMethod
    note: Optional[str] = None
    recorded_by_id: int
    period_key: str
    created_at: datetime

    model_config = {"from_attributes": True}
