from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum


class SubmissionStatusEnum(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class PlagiarismCheckRequest(BaseModel):
    document_id: int
    check_web: bool = True
    check_database: bool = True
    check_institution: bool = True


class MatchResponse(BaseModel):
    id: int
    match_type: str
    source_type: str
    matched_text: str
    source_text: str
    similarity_score: float
    source_url: Optional[str]
    source_title: Optional[str]
    start_position: int
    end_position: int

    class Config:
        from_attributes = True


class PlagiarismCheckResponse(BaseModel):
    submission_id: int
    task_id: str
    status: SubmissionStatusEnum
    originality_score: Optional[float]
    plagiarism_percentage: Optional[float]
    total_matches: int
    web_matches: int
    database_matches: int
    processing_time: Optional[float]
    submitted_at: datetime
    completed_at: Optional[datetime]
    matches: List[MatchResponse] = []

    class Config:
        from_attributes = True