from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from ..database import Base


class Document(Base):
    """Uploaded HWP/HWPX document with extracted plain text"""

    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Original upload metadata
    filename = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=True)
    size_bytes = Column(BigInteger, nullable=False)
    format = Column(String(10), nullable=False)  # "hwp" or "hwpx"

    # Storage
    stored_path = Column(String(512), nullable=False)

    # Extraction result
    extracted_text = Column(Text, nullable=True)
    extraction_error = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="documents")

    def __repr__(self):
        return f"<Document(id={self.id}, filename={self.filename}, format={self.format})>"
