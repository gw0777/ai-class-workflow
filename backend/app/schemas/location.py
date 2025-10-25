from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class LocationClusterBase(BaseModel):
    """Base location cluster schema"""
    cluster_name: str = Field(..., max_length=255)
    cluster_label: Optional[str] = None
    center_latitude: float = Field(..., ge=-90, le=90)
    center_longitude: float = Field(..., ge=-180, le=180)
    radius_meters: float = Field(..., gt=0)


class LocationClusterCreate(LocationClusterBase):
    """Schema for location cluster creation"""
    pass


class LocationClusterUpdate(BaseModel):
    """Schema for location cluster update"""
    cluster_label: Optional[str] = None
    cluster_name: Optional[str] = None


class LocationCluster(LocationClusterBase):
    """Schema for location cluster response"""
    id: UUID
    user_id: UUID
    visit_count: int
    total_time_minutes: int
    avg_duration_minutes: Optional[float] = None
    primary_activity_category: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_visited: Optional[datetime] = None

    class Config:
        from_attributes = True
