from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class URLModel(Base):
    __tablename__ = 'url'
    url = Column(String(255), unique=True, nullable=False)
    domain = Column(String(255), index=True, nullable=False)
    discovered_from = Column(String(255), nullable=False)
    search_query_id = Column(Integer, ForeignKey('search_query.id'), nullable=True)
    first_seen = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_crawled = Column(DateTime(timezone=True))
    crawl_status = Column(String(32), index=True, default='pending')
    http_status_code = Column(Integer)
    content_type = Column(String(64))
    content_length = Column(Integer)
    robots_allowed = Column(Boolean, default=True)
    
    # Relationships - using string references to avoid circular imports
    crawled_contents = relationship("CrawledContent", back_populates="url_record") 