from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from pathlib import Path
from uuid import UUID, uuid4
import os

from ..config import settings
from ..database import get_db
from ..models import User, Document
from ..schemas import DocumentSummary, DocumentDetail, DocumentList
from ..services.auth import get_current_user
from ..services.hwp_extractor import (
    detect_format,
    extract_text,
    HwpExtractionError,
)

router = APIRouter()


def _user_upload_dir(user_id: UUID) -> Path:
    base = Path(settings.UPLOAD_DIR) / str(user_id)
    base.mkdir(parents=True, exist_ok=True)
    return base


@router.post("", response_model=DocumentDetail, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload an HWP/HWPX file. Stores the file on disk and persists
    extracted plain text alongside it."""
    if not file.filename:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Missing filename")

    try:
        fmt = detect_format(file.filename)
    except HwpExtractionError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    body = await file.read(max_bytes + 1)
    if len(body) > max_bytes:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            f"File exceeds {settings.MAX_UPLOAD_SIZE_MB} MB limit",
        )

    upload_dir = _user_upload_dir(current_user.id)
    stored_path = upload_dir / f"{uuid4()}.{fmt}"
    stored_path.write_bytes(body)

    extracted_text: str | None = None
    extraction_error: str | None = None
    try:
        extracted_text = extract_text(str(stored_path), fmt)
    except HwpExtractionError as e:
        extraction_error = str(e)[:255]

    document = Document(
        user_id=current_user.id,
        filename=file.filename,
        content_type=file.content_type,
        size_bytes=len(body),
        format=fmt,
        stored_path=str(stored_path),
        extracted_text=extracted_text,
        extraction_error=extraction_error,
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)
    return document


@router.get("", response_model=DocumentList)
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    base_query = select(Document).where(Document.user_id == current_user.id)

    total = (await db.execute(
        select(func.count()).select_from(base_query.subquery())
    )).scalar()

    rows = (await db.execute(
        base_query.order_by(Document.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )).scalars().all()

    return {"items": rows, "total": total, "page": page, "page_size": page_size}


async def _get_owned(db: AsyncSession, doc_id: UUID, user_id: UUID) -> Document:
    result = await db.execute(
        select(Document).where(
            and_(Document.id == doc_id, Document.user_id == user_id)
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    return doc


@router.get("/{document_id}", response_model=DocumentDetail)
async def get_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _get_owned(db, document_id, current_user.id)


@router.get("/{document_id}/download")
async def download_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    doc = await _get_owned(db, document_id, current_user.id)
    if not os.path.exists(doc.stored_path):
        raise HTTPException(status.HTTP_410_GONE, "Stored file is missing")
    return FileResponse(
        doc.stored_path,
        filename=doc.filename,
        media_type=doc.content_type or "application/octet-stream",
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    doc = await _get_owned(db, document_id, current_user.id)
    stored_path = doc.stored_path
    await db.delete(doc)
    await db.commit()
    try:
        os.remove(stored_path)
    except FileNotFoundError:
        pass
    return None
