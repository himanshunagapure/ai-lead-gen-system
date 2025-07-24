from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from .base import Base

class SearchQuery(Base):
    __tablename__ = 'search_query'
    query_text = Column(Text, nullable=False)
    search_engine = Column(String(32), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    status = Column(String(32), nullable=False, default='pending')
    total_results_found = Column(Integer, default=0) 