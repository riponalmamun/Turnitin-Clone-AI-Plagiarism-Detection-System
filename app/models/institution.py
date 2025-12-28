from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base


class Institution(Base):
    __tablename__ = "institutions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    domain = Column(String, unique=True)  # e.g., university.edu
    
    # Institution type: university, school, company
    type = Column(String, default="university")
    
    # Settings
    settings = Column(JSON, default={})
    # Example: {"allow_cross_check": true, "retention_days": 365}
    
    is_active = Column(Boolean, default=True)
    
    # Subscription
    subscription_tier = Column(String, default="free")  # free, basic, pro
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    users = relationship("User", back_populates="institution")
    documents = relationship("Document", back_populates="institution")