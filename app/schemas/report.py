from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime


class ReportResponse(BaseModel):
    id: int
    submission_id: int
    html_content: Optional[str]
    json_data: Optional[Dict]
    summary: Optional[str]
    recommendations: Optional[str]
    pdf_path: Optional[str]
    generated_at: datetime

    class Config:
        from_attributes = True