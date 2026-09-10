from typing import Optional

from pydantic import BaseModel

from backend.app.schemas.lease import LeaseOut
from backend.app.schemas.property import PropertyOut
from backend.app.schemas.payment import PaymentOut
from backend.app.schemas.user import UserOut


class LandlordDashboard(BaseModel):
    property_count: int
    active_leases: int
    pending_users: int
    overdue_count: int
    overdue_leases: list[LeaseOut]
    recent_payments: list[PaymentOut]


class AgentDashboard(BaseModel):
    property_count: int
    active_leases: int
    pending_users: int
    overdue_count: int
    overdue_leases: list[LeaseOut]
    recent_payments: list[PaymentOut]


class TenantDashboard(BaseModel):
    leases: list[LeaseOut]
    recent_payments: list[PaymentOut]
    unread_notifications: int
    total_balance_due: float
