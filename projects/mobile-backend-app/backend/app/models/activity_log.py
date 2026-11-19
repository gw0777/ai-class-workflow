from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from ..database import Base


class ActivityLog(Base):
    """Activity log model for tracking user activities every 30 minutes"""

    __tablename__ = "activity_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Activity details
    timestamp = Column(DateTime, nullable=False, index=True)
    activity_category = Column(String(50), nullable=False, index=True)  # work, study, exercise, leisure, sleep, etc.
    activity_detail = Column(String(255), nullable=True)
    duration_minutes = Column(Integer, default=30)

    # User ratings
    energy_level = Column(Integer, nullable=True)  # 1-5 scale
    productivity_rating = Column(Integer, nullable=True)  # 1-5 scale
    mood = Column(String(50), nullable=True)  # happy, neutral, sad, stressed, etc.

    # Additional notes
    notes = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="activity_logs")
    location_context = relationship("LocationContext", back_populates="activity_log", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ActivityLog(id={self.id}, category={self.activity_category}, timestamp={self.timestamp})>"
