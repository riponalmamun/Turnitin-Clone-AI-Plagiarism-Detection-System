from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    
    # Submission relationship (one-to-one)
    submission_id = Column(Integer, ForeignKey("submissions.id"), unique=True, nullable=False)
    submission = relationship("Submission", back_populates="report")
    
    # Report content
    html_content = Column(Text)  # HTML with highlighted matches
    json_data = Column(JSON)  # Structured data
    
    # File paths
    pdf_path = Column(String)  # Generated PDF report
    
    # Summary
    summary = Column(Text)
    recommendations = Column(Text)
    
    # Timestamps
    generated_at = Column(DateTime(timezone=True), server_default=func.now())