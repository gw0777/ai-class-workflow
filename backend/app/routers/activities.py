from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional
from datetime import datetime
from uuid import UUID

from ..database import get_db
from ..models import User, ActivityLog, LocationContext
from ..schemas import (
    ActivityLogCreate,
    ActivityLogUpdate,
    ActivityLog as ActivityLogSchema,
    ActivityLogList,
)
from ..services.auth import get_current_user

router = APIRouter()


@router.post("", response_model=ActivityLogSchema, status_code=status.HTTP_201_CREATED)
async def create_activity_log(
    activity_data: ActivityLogCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new activity log entry
    """
    # Create activity log
    activity_log = ActivityLog(
        user_id=current_user.id,
        timestamp=activity_data.timestamp,
        activity_category=activity_data.activity_category,
        activity_detail=activity_data.activity_detail,
        duration_minutes=activity_data.duration_minutes,
        energy_level=activity_data.energy_level,
        productivity_rating=activity_data.productivity_rating,
        mood=activity_data.mood,
        notes=activity_data.notes,
    )

    db.add(activity_log)
    await db.flush()  # Flush to get the activity_log.id

    # Create location context if provided
    if activity_data.location_context:
        location = LocationContext(
            activity_log_id=activity_log.id,
            latitude=activity_data.location_context.latitude,
            longitude=activity_data.location_context.longitude,
            accuracy=activity_data.location_context.accuracy,
            location_name=activity_data.location_context.location_name,
            address=activity_data.location_context.address,
        )
        db.add(location)

    await db.commit()
    await db.refresh(activity_log)

    return activity_log


@router.get("", response_model=ActivityLogList)
async def get_activity_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get activity logs for the current user with pagination and filters
    """
    # Build query
    query = select(ActivityLog).where(ActivityLog.user_id == current_user.id)

    # Apply filters
    if start_date:
        query = query.where(ActivityLog.timestamp >= start_date)
    if end_date:
        query = query.where(ActivityLog.timestamp <= end_date)
    if category:
        query = query.where(ActivityLog.activity_category == category)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply pagination and ordering
    query = query.order_by(ActivityLog.timestamp.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    # Execute query
    result = await db.execute(query)
    activities = result.scalars().all()

    return {
        "items": activities,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{activity_id}", response_model=ActivityLogSchema)
async def get_activity_log(
    activity_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific activity log by ID
    """
    result = await db.execute(
        select(ActivityLog).where(
            and_(
                ActivityLog.id == activity_id,
                ActivityLog.user_id == current_user.id
            )
        )
    )
    activity = result.scalar_one_or_none()

    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity log not found"
        )

    return activity


@router.put("/{activity_id}", response_model=ActivityLogSchema)
async def update_activity_log(
    activity_id: UUID,
    activity_data: ActivityLogUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update an activity log entry
    """
    result = await db.execute(
        select(ActivityLog).where(
            and_(
                ActivityLog.id == activity_id,
                ActivityLog.user_id == current_user.id
            )
        )
    )
    activity = result.scalar_one_or_none()

    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity log not found"
        )

    # Update fields if provided
    update_data = activity_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(activity, field, value)

    await db.commit()
    await db.refresh(activity)

    return activity


@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_activity_log(
    activity_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete an activity log entry
    """
    result = await db.execute(
        select(ActivityLog).where(
            and_(
                ActivityLog.id == activity_id,
                ActivityLog.user_id == current_user.id
            )
        )
    )
    activity = result.scalar_one_or_none()

    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity log not found"
        )

    await db.delete(activity)
    await db.commit()

    return None
