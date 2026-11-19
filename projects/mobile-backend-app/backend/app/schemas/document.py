from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


class DocumentSummary(BaseModel):
    """List/summary view — no extracted text body"""
    id: UUID
    user_id: UUID
    filename: str
    content_type: Optional[str] = None
    size_bytes: int
    format: str
    extraction_error: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentDetail(DocumentSummary):
    """Detail view — includes extracted text"""
    extracted_text: Optional[str] = None


class DocumentList(BaseModel):
    items: list[DocumentSummary]
    total: int
    page: int
    page_size: int
