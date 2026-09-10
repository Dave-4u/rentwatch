from datetime import datetime
from typing import Optional
import re

from pydantic import BaseModel, Field, field_validator

from backend.app.models.user import UserRole, UserStatus

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validate_email(v: str) -> str:
    v = v.strip().lower()
    if not EMAIL_RE.match(v):
        raise ValueError("Invalid email address")
    return v


class UserRegister(BaseModel):
    email: str
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)
    phone: Optional[str] = None
    role: UserRole

    @field_validator("email")
    @classmethod
    def email_ok(cls, v: str) -> str:
        return _validate_email(v)

    @field_validator("role")
    @classmethod
    def no_landlord(cls, v: UserRole) -> UserRole:
        if v == UserRole.landlord:
            raise ValueError("Cannot register as landlord")
        if v not in (UserRole.agent, UserRole.tenant):
            raise ValueError("Role must be agent or tenant")
        return v


class UserLogin(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def email_ok(cls, v: str) -> str:
        return _validate_email(v)


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    phone: Optional[str] = None
    role: UserRole
    status: UserStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
