from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    
    # File info
    filename = Column(String, nullable=False)
    original_filename = Column(String)
    file_path = Column(String)
    file_size = Column(Integer)  # in bytes
    file_type = Column(String)  # pdf, docx, txt
    
    # Content
    content = Column(Text)  # Extracted text
    content_hash = Column(String, unique=True, index=True)  # For deduplication
    
    # Metadata
    word_count = Column(Integer)
    char_count = Column(Integer)
    language = Column(String, default="en")
    
    # Embedding for vector search
    embedding_stored = Column(Boolean, default=False)
    
    # Additional metadata
    doc_metadata = Column(JSON, default={})
    
    # Ownership
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="documents")
    
    institution_id = Column(Integer, ForeignKey("institutions.id"))
    institution = relationship("Institution", back_populates="documents")
    
    # Timestamps
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    submissions = relationship("Submission", back_populates="document", cascade="all, delete-orphan")