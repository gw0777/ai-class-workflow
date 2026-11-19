from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from ..database import Base


class User(Base):
    """User model for authentication and profile"""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # Settings
    timezone = Column(String(50), default="Asia/Seoul")
    notification_enabled = Column(Boolean, default=True)
    notification_start_hour = Column(String(5), default="09:00")  # HH:MM format
    notification_end_hour = Column(String(5), default="22:00")    # HH:MM format

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    activity_logs = relationship("ActivityLog", back_populates="user", cascade="all, delete-orphan")
    user_inputs = relationship("UserInput", back_populates="user", cascade="all, delete-orphan")
    analysis_reports = relationship("AnalysisReport", back_populates="user", cascade="all, delete-orphan")
    location_clusters = relationship("LocationCluster", back_populates="user", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"
