from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field

from backend.app.models.lease import LeaseStatus


class LeaseCreate(BaseModel):
    property_id: int
    tenant_id: int
    rent_amount: float = Field(gt=0)
    due_day: int = Field(ge=1, le=28)
    start_date: date
    status: LeaseStatus = LeaseStatus.active


class LeaseUpdate(BaseModel):
    rent_amount: Optional[float] = Field(default=None, gt=0)
    due_day: Optional[int] = Field(default=None, ge=1, le=28)
    start_date: Optional[date] = None
    status: Optional[LeaseStatus] = None


class LeaseOut(BaseModel):
    id: int
    property_id: int
    tenant_id: int
    rent_amount: float
    billing_period: str
    due_day: int
    start_date: date
    status: LeaseStatus
    created_at: datetime
    property_name: Optional[str] = None
    tenant_name: Optional[str] = None
    is_overdue: Optional[bool] = None
    balance_due: Optional[float] = None
    current_period: Optional[str] = None

    model_config = {"from_attributes": True}
