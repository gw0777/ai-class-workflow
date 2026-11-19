from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from ..database import Base


class UserInput(Base):
    """User input records for tracking questions and answers"""

    __tablename__ = "user_inputs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Question/Answer data
    question_type = Column(String(50), nullable=False, index=True)  # activity, location, mood, goal, etc.
    question_text = Column(Text, nullable=False)
    answer = Column(JSON, nullable=False)  # Flexible JSON structure for various answer types

    # Timestamps
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="user_inputs")

    def __repr__(self):
        return f"<UserInput(id={self.id}, type={self.question_type}, timestamp={self.timestamp})>"
