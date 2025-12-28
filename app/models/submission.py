from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, JSON, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database.session import Base


class SubmissionStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    
    # Status
    status = Column(Enum(SubmissionStatus), default=SubmissionStatus.PENDING)
    
    # Celery task ID
    task_id = Column(String, unique=True, index=True)
    
    # Scores
    originality_score = Column(Float)  # 0-100
    plagiarism_percentage = Column(Float)  # 0-100
    
    # Match statistics
    total_matches = Column(Integer, default=0)
    web_matches = Column(Integer, default=0)
    database_matches = Column(Integer, default=0)
    
    # Processing info
    processing_time = Column(Float)  # in seconds
    error_message = Column(Text)
    
    # Settings used
    check_settings = Column(JSON, default={})
    
    # Document relationship
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    document = relationship("Document", back_populates="submissions")
    
    # User relationship
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="submissions")
    
    # Timestamps
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    matches = relationship("Match", back_populates="submission", cascade="all, delete-orphan")
    report = relationship("Report", back_populates="submission", uselist=False, cascade="all, delete-orphan")