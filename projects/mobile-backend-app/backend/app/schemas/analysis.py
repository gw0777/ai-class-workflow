from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class AnalysisReportBase(BaseModel):
    """Base analysis report schema"""
    report_type: str
    period_start: datetime
    period_end: datetime
    insights: Optional[Dict[str, Any]] = None
    recommendations: Optional[Dict[str, Any]] = None
    time_distribution: Optional[Dict[str, Any]] = None
    productivity_analysis: Optional[Dict[str, Any]] = None
    location_analysis: Optional[Dict[str, Any]] = None


class AnalysisReportCreate(AnalysisReportBase):
    """Schema for analysis report creation"""
    pass


class AnalysisReport(AnalysisReportBase):
    """Schema for analysis report response"""
    id: UUID
    user_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class DailyAnalysisRequest(BaseModel):
    """Schema for daily analysis request"""
    date: datetime


class WeeklyAnalysisRequest(BaseModel):
    """Schema for weekly analysis request"""
    start_date: datetime


class InsightsResponse(BaseModel):
    """Schema for AI insights response"""
    summary: str
    key_patterns: list[str]
    recommendations: list[str]
    time_distribution: Dict[str, int]
    productivity_score: float
