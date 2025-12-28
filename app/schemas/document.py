from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DocumentUpload(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None


class DocumentResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_size: int
    file_type: str
    word_count: Optional[int]
    content_hash: str
    uploaded_at: datetime

    class Config:
        from_attributes = True