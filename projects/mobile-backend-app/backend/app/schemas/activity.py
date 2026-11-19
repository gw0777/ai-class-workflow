from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class LocationContextBase(BaseModel):
    """Base location context schema"""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    accuracy: Optional[float] = None
    location_name: Optional[str] = None
    address: Optional[str] = None


class LocationContextCreate(LocationContextBase):
    """Schema for location context creation"""
    pass


class LocationContext(LocationContextBase):
    """Schema for location context response"""
    id: UUID
    activity_log_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class ActivityLogBase(BaseModel):
    """Base activity log schema"""
    timestamp: datetime
    activity_category: str = Field(..., max_length=50)
    activity_detail: Optional[str] = Field(None, max_length=255)
    duration_minutes: int = Field(30, ge=1, le=1440)
    energy_level: Optional[int] = Field(None, ge=1, le=5)
    productivity_rating: Optional[int] = Field(None, ge=1, le=5)
    mood: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None


class ActivityLogCreate(ActivityLogBase):
    """Schema for activity log creation"""
    location_context: Optional[LocationContextCreate] = None


class ActivityLogUpdate(BaseModel):
    """Schema for activity log update"""
    activity_category: Optional[str] = None
    activity_detail: Optional[str] = None
    duration_minutes: Optional[int] = Field(None, ge=1, le=1440)
    energy_level: Optional[int] = Field(None, ge=1, le=5)
    productivity_rating: Optional[int] = Field(None, ge=1, le=5)
    mood: Optional[str] = None
    notes: Optional[str] = None


class ActivityLog(ActivityLogBase):
    """Schema for activity log response"""
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    location_context: Optional[LocationContext] = None

    class Config:
        from_attributes = True


class ActivityLogList(BaseModel):
    """Schema for activity log list response"""
    items: list[ActivityLog]
    total: int
    page: int
    page_size: int
