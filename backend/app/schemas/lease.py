from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

from backend.app.models.lease import LeaseStatus

BillingPeriod = Literal["yearly", "monthly"]


class LeaseCreate(BaseModel):
    property_id: int
    tenant_id: int
    rent_amount: float = Field(gt=0)
    due_date: date
    start_date: date
    billing_period: BillingPeriod = "yearly"
    status: LeaseStatus = LeaseStatus.active
    # Optional legacy field; ignored when due_date is set
    due_day: Optional[int] = Field(default=None, ge=1, le=28)


class LeaseUpdate(BaseModel):
    rent_amount: Optional[float] = Field(default=None, gt=0)
    due_date: Optional[date] = None
    due_day: Optional[int] = Field(default=None, ge=1, le=28)
    start_date: Optional[date] = None
    billing_period: Optional[BillingPeriod] = None
    status: Optional[LeaseStatus] = None


class LeaseOut(BaseModel):
    id: int
    property_id: int
    tenant_id: int
    rent_amount: float
    billing_period: str
    due_day: Optional[int] = None
    due_date: Optional[date] = None
    start_date: date
    status: LeaseStatus
    created_at: datetime
    property_name: Optional[str] = None
    property_type: Optional[str] = None
    tenant_name: Optional[str] = None
    is_overdue: Optional[bool] = None
    balance_due: Optional[float] = None
    current_period: Optional[str] = None

    model_config = {"from_attributes": True}
