from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database.session import Base


class MatchType(str, enum.Enum):
    EXACT = "exact"
    PARAPHRASE = "paraphrase"
    SEMANTIC = "semantic"


class SourceType(str, enum.Enum):
    WEB = "web"
    DATABASE = "database"
    INSTITUTION = "institution"


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    
    # Submission relationship
    submission_id = Column(Integer, ForeignKey("submissions.id"), nullable=False)
    submission = relationship("Submission", back_populates="matches")
    
    # Match details
    match_type = Column(Enum(MatchType))
    source_type = Column(Enum(SourceType))
    
    # Matched content
    matched_text = Column(Text)  # Text from submitted document
    source_text = Column(Text)  # Text from source
    
    # Position in document
    start_position = Column(Integer)
    end_position = Column(Integer)
    
    # Similarity score
    similarity_score = Column(Float)  # 0-100
    
    # Source information
    source_url = Column(String)
    source_title = Column(String)
    source_document_id = Column(Integer, ForeignKey("documents.id"))  # If from database
    
    # Additional metadata
    match_metadata = Column(JSON, default={})  # ✅ Changed from 'metadata'
    
    # Timestamp
    detected_at = Column(DateTime(timezone=True), server_default=func.now())