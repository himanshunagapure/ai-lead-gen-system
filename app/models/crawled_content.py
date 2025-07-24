from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from .base import Base

class CrawledContent(Base):
    __tablename__ = 'crawled_content'
    url_id = Column(Integer, ForeignKey('url.id'), nullable=False)
    raw_html_path = Column(String(255), nullable=False)
    title = Column(Text)
    meta_description = Column(Text)
    extracted_text = Column(Text)
    language = Column(String(16))
    crawl_timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    processing_status = Column(String(32), default='pending') 