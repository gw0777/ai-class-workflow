from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from ..database import Base


class LocationContext(Base):
    """Location context for activity logs"""

    __tablename__ = "location_contexts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    activity_log_id = Column(UUID(as_uuid=True), ForeignKey("activity_logs.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    # Location data
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    accuracy = Column(Float, nullable=True)  # meters

    # Location metadata
    location_name = Column(String(255), nullable=True)  # e.g., "Home", "Office", "Gym"
    address = Column(String(500), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    activity_log = relationship("ActivityLog", back_populates="location_context")

    def __repr__(self):
        return f"<LocationContext(id={self.id}, lat={self.latitude}, lng={self.longitude})>"
