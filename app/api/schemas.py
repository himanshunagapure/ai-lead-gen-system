from pydantic import BaseModel, Field, EmailStr, HttpUrl
from typing import Optional, List, Any, Dict
from datetime import datetime
import random

class SearchJobRequest(BaseModel):
    query: str
    priority: Optional[int] = 0
    max_results: Optional[int] = 30
    intent: Optional[str] = None
    location: Optional[str] = None

class SearchJobResponse(BaseModel):
    job_id: str
    status: str
    submitted_at: datetime

class CrawlJobRequest(BaseModel):
    url: HttpUrl
    priority: Optional[int] = 0

class CrawlJobResponse(BaseModel):
    job_id: str
    status: str
    submitted_at: datetime

class LeadFilter(BaseModel):
    lead_type: Optional[str] = None
    min_score: Optional[float] = 0.0
    max_score: Optional[float] = 1.0
    keyword: Optional[str] = None
    location: Optional[str] = None
    page: Optional[int] = 1
    page_size: Optional[int] = 20

class LeadResponse(BaseModel):
    id: int = Field(default_factory=lambda: random.randint(1, 1_000_000))
    business_name: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    website: Optional[HttpUrl] = None
    lead_type: Optional[str] = None
    confidence_score: Optional[float] = None
    extraction_method: Optional[str] = None
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    scoring: Optional[Dict[str, Any]] = None

class PaginatedLeadsResponse(BaseModel):
    leads: List[LeadResponse]
    total: int
    page: int
    page_size: int

class ErrorResponse(BaseModel):
    detail: str 