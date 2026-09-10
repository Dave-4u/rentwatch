from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from backend.app.models.property import PropertyType


class PropertyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    address: str = Field(min_length=1, max_length=500)
    property_type: PropertyType
    description: Optional[str] = None
    default_rent: Optional[float] = Field(default=None, ge=0)


class PropertyUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    address: Optional[str] = Field(default=None, min_length=1, max_length=500)
    property_type: Optional[PropertyType] = None
    description: Optional[str] = None
    default_rent: Optional[float] = Field(default=None, ge=0)


class PropertyOut(BaseModel):
    id: int
    name: str
    address: str
    property_type: PropertyType
    description: Optional[str] = None
    default_rent: Optional[float] = None
    created_at: datetime

    model_config = {"from_attributes": True}
