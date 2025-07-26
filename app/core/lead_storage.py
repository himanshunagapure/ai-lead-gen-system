"""
Lead Storage Service - Handles database persistence and file exports
"""
import os
import csv
import json
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging

from app.db.session import SessionLocal
# Import all models to avoid circular import issues
from app.db.base import Base
from app.models.extracted_lead import ExtractedLead
from app.models.lead_score import LeadScore
from app.models.crawled_content import CrawledContent
from app.models.url import URLModel
from app.models.search_query import SearchQuery
from app.core.file_manager import EXPORTS_DIR, timestamped_filename

logger = logging.getLogger(__name__)

class LeadStorageService:
    """Service for storing and managing leads in database and files"""
    
    def __init__(self):
        self.exports_dir = EXPORTS_DIR
        os.makedirs(self.exports_dir, exist_ok=True)
    
    def store_lead_in_db(self, lead_data: Dict[str, Any]) -> Optional[int]:
        """
        Store a lead in the database
        Returns the lead ID if successful, None if failed
        """
        db = SessionLocal()
        try:
            # First, create or get crawled content record
            source_url = lead_data.get('source_url', 'unknown')
            crawled_content = self._get_or_create_crawled_content(db, source_url)
            
            # Create the lead record
            lead = ExtractedLead(
                content_id=crawled_content.id,
                business_name=lead_data.get('business_name'),
                contact_person=lead_data.get('contact_person'),
                email=lead_data.get('email'),
                phone=lead_data.get('phone'),
                address=lead_data.get('address'),
                website=lead_data.get('website'),
                lead_type=lead_data.get('lead_type'),
                confidence_score=lead_data.get('confidence_score'),
                extraction_method=lead_data.get('extraction_method')
                # created_at has a default value in the model
            )
            
            db.add(lead)
            db.flush()  # Get the ID
            
            # Store scoring data if available
            if 'scoring' in lead_data and lead_data['scoring']:
                scoring_data = lead_data['scoring']
                lead_score = LeadScore(
                    lead_id=lead.id,
                    completeness_score=scoring_data.get('completeness_score'),
                    relevance_score=scoring_data.get('relevance_score'),
                    freshness_score=scoring_data.get('freshness_score'),
                    final_score=scoring_data.get('final_score'),
                    scoring_factors=scoring_data.get('scoring_factors', {})
                    # scored_at has a default value in the model
                )
                db.add(lead_score)
            
            db.commit()
            logger.info(f"Successfully stored lead {lead.id} in database")
            return lead.id
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Failed to store lead in database: {e}")
            return None
        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error storing lead: {e}")
            return None
        finally:
            db.close()
    
    def _get_or_create_crawled_content(self, db: Session, source_url: str) -> CrawledContent:
        """Get existing crawled content or create new one"""
        # Handle None or invalid source_url
        if not source_url or source_url == 'unknown' or source_url == 'None':
            source_url = 'https://test.example.com/contact'  # Default URL for test leads
        
        # First, get or create the URL record
        url_record = db.query(URLModel).filter_by(url=source_url).first()
        if not url_record:
            # Extract domain from URL
            from urllib.parse import urlparse
            try:
                parsed = urlparse(source_url)
                domain = parsed.netloc if parsed.netloc else 'unknown'
            except Exception:
                domain = 'unknown'
            
            url_record = URLModel(
                url=source_url,
                domain=domain,
                discovered_from="lead_extraction",
                search_query_id=None,  # No search query for manually added leads
                crawl_status="completed"
            )
            db.add(url_record)
            db.flush()
        
        # Check if we already have crawled content for this URL
        existing = db.query(CrawledContent).filter_by(url_id=url_record.id).first()
        if existing:
            return existing
        
        # Create new crawled content record
        crawled_content = CrawledContent(
            url_id=url_record.id,
            raw_html_path="",  # We don't store HTML for leads
            title=f"Content from {source_url}",
            extracted_text="",  # We don't store full content in DB for leads
            processing_status="completed"
        )
        db.add(crawled_content)
        db.flush()
        return crawled_content
    
    def export_leads_to_csv(self, leads: List[Dict[str, Any]], filename: Optional[str] = None) -> str:
        """Export leads to CSV file"""
        if not filename:
            filename = timestamped_filename("leads", "csv")
        
        filepath = os.path.join(self.exports_dir, filename)
        
        try:
            # Flatten the scoring data for CSV export
            flattened_leads = []
            for lead in leads:
                flattened_lead = lead.copy()
                
                # Extract scoring data
                if 'scoring' in lead and lead['scoring']:
                    scoring = lead['scoring']
                    flattened_lead.update({
                        'completeness_score': scoring.get('completeness_score'),
                        'relevance_score': scoring.get('relevance_score'),
                        'freshness_score': scoring.get('freshness_score'),
                        'final_score': scoring.get('final_score'),
                        'scored_at': scoring.get('scored_at')
                    })
                
                # Remove nested scoring object
                flattened_lead.pop('scoring', None)
                flattened_leads.append(flattened_lead)
            
            # Write to CSV
            if flattened_leads:
                df = pd.DataFrame(flattened_leads)
                df.to_csv(filepath, index=False, encoding='utf-8')
                logger.info(f"Exported {len(leads)} leads to CSV: {filepath}")
            else:
                # Create empty CSV with headers
                with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = [
                        'business_name', 'contact_person', 'email', 'phone', 'address',
                        'website', 'lead_type', 'confidence_score', 'extraction_method',
                        'created_at', 'source_url', 'completeness_score', 'relevance_score',
                        'freshness_score', 'final_score', 'scored_at'
                    ]
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                logger.info(f"Created empty CSV file: {filepath}")
            
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to export leads to CSV: {e}")
            raise
    
    def export_leads_to_excel(self, leads: List[Dict[str, Any]], filename: Optional[str] = None) -> str:
        """Export leads to Excel file"""
        if not filename:
            filename = timestamped_filename("leads", "xlsx")
        
        filepath = os.path.join(self.exports_dir, filename)
        
        try:
            # Flatten the scoring data for Excel export
            flattened_leads = []
            for lead in leads:
                flattened_lead = lead.copy()
                
                # Extract scoring data
                if 'scoring' in lead and lead['scoring']:
                    scoring = lead['scoring']
                    flattened_lead.update({
                        'completeness_score': scoring.get('completeness_score'),
                        'relevance_score': scoring.get('relevance_score'),
                        'freshness_score': scoring.get('freshness_score'),
                        'final_score': scoring.get('final_score'),
                        'scored_at': scoring.get('scored_at')
                    })
                
                # Remove nested scoring object
                flattened_lead.pop('scoring', None)
                flattened_leads.append(flattened_lead)
            
            # Write to Excel
            if flattened_leads:
                df = pd.DataFrame(flattened_leads)
                df.to_excel(filepath, index=False, engine='openpyxl')
                logger.info(f"Exported {len(leads)} leads to Excel: {filepath}")
            else:
                # Create empty Excel with headers
                df = pd.DataFrame(columns=[
                    'business_name', 'contact_person', 'email', 'phone', 'address',
                    'website', 'lead_type', 'confidence_score', 'extraction_method',
                    'created_at', 'source_url', 'completeness_score', 'relevance_score',
                    'freshness_score', 'final_score', 'scored_at'
                ])
                df.to_excel(filepath, index=False, engine='openpyxl')
                logger.info(f"Created empty Excel file: {filepath}")
            
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to export leads to Excel: {e}")
            raise
    
    def export_leads_to_json(self, leads: List[Dict[str, Any]], filename: Optional[str] = None) -> str:
        """Export leads to JSON file"""
        if not filename:
            filename = timestamped_filename("leads", "json")
        
        filepath = os.path.join(self.exports_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(leads, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"Exported {len(leads)} leads to JSON: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to export leads to JSON: {e}")
            raise
    
    def get_leads_from_db(self, limit: Optional[int] = None, offset: int = 0) -> List[Dict[str, Any]]:
        """Retrieve leads from database"""
        db = SessionLocal()
        try:
            query = db.query(ExtractedLead).offset(offset)
            if limit:
                query = query.limit(limit)
            
            leads = query.all()
            
            # Convert to dictionary format
            lead_dicts = []
            for lead in leads:
                # Get the source URL from the URL table
                source_url = None
                try:
                    if hasattr(lead, 'crawled_content') and lead.crawled_content and lead.crawled_content.url_id:
                        url_record = db.query(URLModel).filter_by(id=lead.crawled_content.url_id).first()
                        if url_record:
                            source_url = url_record.url
                except Exception as e:
                    logger.warning(f"Could not get source URL for lead {lead.id}: {e}")
                    # Fallback: try to get URL directly from content_id
                    try:
                        content = db.query(CrawledContent).filter_by(id=lead.content_id).first()
                        if content and content.url_id:
                            url_record = db.query(URLModel).filter_by(id=content.url_id).first()
                            if url_record:
                                source_url = url_record.url
                    except Exception as e2:
                        logger.warning(f"Fallback URL retrieval also failed for lead {lead.id}: {e2}")
                
                lead_dict = {
                    'id': lead.id,
                    'business_name': lead.business_name,
                    'contact_person': lead.contact_person,
                    'email': lead.email,
                    'phone': lead.phone,
                    'address': lead.address,
                    'website': lead.website,
                    'lead_type': lead.lead_type,
                    'confidence_score': lead.confidence_score,
                    'extraction_method': lead.extraction_method,
                    'created_at': lead.created_at,
                    'source_url': source_url
                }
                
                # Add scoring data if available
                lead_score = db.query(LeadScore).filter_by(lead_id=lead.id).first()
                if lead_score:
                    lead_dict['scoring'] = {
                        'completeness_score': lead_score.completeness_score,
                        'relevance_score': lead_score.relevance_score,
                        'freshness_score': lead_score.freshness_score,
                        'final_score': lead_score.final_score,
                        'scoring_factors': lead_score.scoring_factors,
                        'scored_at': lead_score.scored_at
                    }
                
                lead_dicts.append(lead_dict)
            
            return lead_dicts
            
        except Exception as e:
            logger.error(f"Failed to retrieve leads from database: {e}")
            return []
        finally:
            db.close()
    
    def get_lead_count_from_db(self) -> int:
        """Get total number of leads in database"""
        db = SessionLocal()
        try:
            count = db.query(ExtractedLead).count()
            return count
        except Exception as e:
            logger.error(f"Failed to get lead count from database: {e}")
            return 0
        finally:
            db.close()

# Global instance
lead_storage = LeadStorageService() 