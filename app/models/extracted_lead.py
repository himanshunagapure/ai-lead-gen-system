from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from .base import Base

class ExtractedLead(Base):
    __tablename__ = 'extracted_lead'
    content_id = Column(Integer, ForeignKey('crawled_content.id'), nullable=False)
    business_name = Column(String(255))
    contact_person = Column(String(255))
    email = Column(String(255), index=True)
    phone = Column(String(32))
    address = Column(Text)
    website = Column(String(255))
    lead_type = Column(String(64))
    confidence_score = Column(Float)
    extraction_method = Column(String(64))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False) 