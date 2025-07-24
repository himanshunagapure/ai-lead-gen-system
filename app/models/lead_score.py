from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from .base import Base

class LeadScore(Base):
    __tablename__ = 'lead_score'
    lead_id = Column(Integer, ForeignKey('extracted_lead.id'), nullable=False)
    completeness_score = Column(Float)
    relevance_score = Column(Float)
    freshness_score = Column(Float)
    final_score = Column(Float)
    scoring_factors = Column(JSON)
    scored_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False) 