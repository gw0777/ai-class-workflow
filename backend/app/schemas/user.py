from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class UserBase(BaseModel):
    """Base user schema"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr


class UserCreate(UserBase):
    """Schema for user creation"""
    password: str = Field(..., min_length=6, max_length=100)


class UserUpdate(BaseModel):
    """Schema for user update"""
    email: Optional[EmailStr] = None
    timezone: Optional[str] = None
    notification_enabled: Optional[bool] = None
    notification_start_hour: Optional[str] = None
    notification_end_hour: Optional[str] = None


class UserInDB(UserBase):
    """Schema for user in database"""
    id: UUID
    timezone: str
    notification_enabled: bool
    notification_start_hour: str
    notification_end_hour: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class User(UserInDB):
    """Schema for user response"""
    pass


class Token(BaseModel):
    """Schema for JWT token"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for token data"""
    user_id: Optional[str] = None
