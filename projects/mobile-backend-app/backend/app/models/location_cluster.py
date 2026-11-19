from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from ..database import Base


class LocationCluster(Base):
    """Location clusters identified from user's location data"""

    __tablename__ = "location_clusters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Cluster metadata
    cluster_name = Column(String(255), nullable=False)  # e.g., "Home", "Work", "Gym"
    cluster_label = Column(String(50), nullable=True)  # User-defined label

    # Cluster center
    center_latitude = Column(Float, nullable=False)
    center_longitude = Column(Float, nullable=False)
    radius_meters = Column(Float, nullable=False)  # Cluster radius in meters

    # Statistics
    visit_count = Column(Integer, default=0)
    total_time_minutes = Column(Integer, default=0)
    avg_duration_minutes = Column(Float, nullable=True)

    # Most common activity at this location
    primary_activity_category = Column(String(50), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_visited = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="location_clusters")

    def __repr__(self):
        return f"<LocationCluster(id={self.id}, name={self.cluster_name}, visits={self.visit_count})>"
