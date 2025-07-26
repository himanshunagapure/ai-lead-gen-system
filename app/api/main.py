from fastapi import FastAPI, Depends, HTTPException, Query, BackgroundTasks, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from app.api.schemas import (
    SearchJobRequest, SearchJobResponse, CrawlJobRequest, CrawlJobResponse,
    LeadFilter, PaginatedLeadsResponse, LeadResponse, ErrorResponse
)
from typing import List, Optional
from datetime import datetime
import logging
import csv
import pandas as pd
import json as pyjson
import os
from contextlib import asynccontextmanager

# Import core pipeline modules
from app.core.search_orchestrator import SearchOrchestrator
from app.core.crawl_manager import CrawlManager
from app.core.http_crawler import SimpleHttpCrawler
from app.core.lead_extractor import extract_pattern_leads, extract_structured_leads, ai_extract_leads
from app.core.lead_scorer import score_lead
from app.core.background_tasks import JobQueue, BaseWorker, Job
from app.core.file_manager import save_extracted_data, EXPORTS_DIR, timestamped_filename
from app.core.monitoring import JsonLogger, get_system_metrics, PerformanceTracker
from app.core.lead_storage import lead_storage  # Add this import

integration_debug_logger = logging.getLogger("integration_debug")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    global workers
    integration_debug_logger.info("[lifespan] Starting background workers for job types: search, crawl, lead_processing")
    workers = [
        BaseWorker(job_queue, search_job_handler, 'search', job_timeout=30.0),
        BaseWorker(job_queue, crawl_job_handler, 'crawl', job_timeout=25.0),
        BaseWorker(job_queue, lead_processing_handler, 'lead_processing', job_timeout=20.0)
    ]
    for w in workers:
        integration_debug_logger.info(f"[lifespan] Starting worker: {w.handler.__name__} for job_type: {w.job_type}")
        w.start()
    yield
    # (Optional) Shutdown code here

app = FastAPI(title="Travel Lead Generation API", lifespan=lifespan)

# Monitoring and logging setup
logger = JsonLogger("leadgen", os.path.join("data", "logs", "app.log"))
perf_tracker = PerformanceTracker()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging
logging.basicConfig(level=logging.INFO)

# In-memory stores for demo (replace with DB in production)
search_orchestrator = SearchOrchestrator()
crawl_manager = CrawlManager()
leads_store = []  # List[dict]

# Background job system
job_queue = JobQueue()
workers = []

# Realistic handlers for jobs
import asyncio

def search_job_handler(job: Job):
    integration_debug_logger.info(f"[search_job_handler] job_type={job.type}, payload={{'query': job.payload.get('query'), 'priority': job.payload.get('priority', 0), 'max_results': job.payload.get('max_results', 30), 'intent': job.payload.get('intent'), 'location': job.payload.get('location')}}")
    logger.log("info", "search_job_handler_start", job_type=job.type, payload={"query": job.payload.get('query'), "priority": job.payload.get('priority', 0), "max_results": job.payload.get('max_results', 30), "intent": job.payload.get('intent'), "location": job.payload.get('location')})
    query = job.payload.get('query')
    priority = job.payload.get('priority', 0)
    max_results = job.payload.get('max_results', 30)
    intent = job.payload.get('intent')
    location = job.payload.get('location')

    try:
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        from app.core.search_client import GoogleSearchClient
        from app.core.search_result_processor import process_search_results
        client = GoogleSearchClient()
        
        async def do_search():
            search_query = query
            raw_results = await client.paginated_search(search_query, max_results=max_results)
            processed = process_search_results(raw_results)
            return processed, raw_results
        
        try:
            processed_results, raw_results = loop.run_until_complete(asyncio.wait_for(do_search(), timeout=20))
        except asyncio.TimeoutError:
            error_msg = f"Timeout during search for query: {query}"
            logger.log("error", "search_job_handler_timeout", query=query, error=error_msg)
            job.error = error_msg
            return {"search_results": [], "raw_results": [], "error": error_msg}
        except Exception as e:
            error_msg = f"Search failed for query {query}: {str(e)}"
            logger.log("error", "search_job_handler_failed", query=query, error=error_msg)
            job.error = error_msg
            return {"search_results": [], "raw_results": [], "error": error_msg}
        finally:
            loop.close()
        
        # integration_debug_logger.info(f"[search_job_handler] Processed search results: {processed_results}")  # REMOVE VERBOSE
        # integration_debug_logger.info(f"[search_job_handler] Raw Google search results: {raw_results}")  # REMOVE VERBOSE
        logger.log("info", "search_job_handler_end", processed_results_count=len(processed_results), raw_results_count=len(raw_results))
        return {"search_results": processed_results, "raw_results": raw_results}
        
    except Exception as e:
        error_msg = f"Exception during search for query {query}: {str(e)}"
        logger.log("error", "search_job_handler_exception", query=query, error=error_msg)
        job.error = error_msg
        return {"search_results": [], "raw_results": [], "error": error_msg}

def crawl_job_handler(job: Job):
    integration_debug_logger.info(f"[crawl_job_handler] job_type={job.type}, payload={job.payload}")
    logger.log("info", "crawl_job_handler_start", job_type=job.type)
    url = job.payload.get('url')
    url = str(url)
    
    try:
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Set a shorter timeout for crawling
        crawler = SimpleHttpCrawler(timeout=10)  # Reduced timeout to 10 seconds
        
        # Run the crawl operation with timeout
        try:
            results = loop.run_until_complete(asyncio.wait_for(crawler.crawl([url]), timeout=15))
        except asyncio.TimeoutError:
            error_msg = f"Timeout crawling URL: {url}"
            logger.log("error", "crawl_job_handler_timeout", url=url, error=error_msg)
            job.error = error_msg
            return {"crawl_results": [], "error": error_msg}
        except Exception as e:
            error_msg = f"Failed to crawl URL {url}: {str(e)}"
            logger.log("error", "crawl_job_handler_crawl_failed", url=url, error=error_msg)
            job.error = error_msg
            return {"crawl_results": [], "error": error_msg}
        finally:
            loop.close()
        
        if not results:
            error_msg = f"Failed to crawl URL: {url}"
            logger.log("error", "crawl_job_handler_failed", url=url, error=error_msg)
            job.error = error_msg
            return {"crawl_results": [], "error": error_msg}
        
        # Extract text from HTML for lead processing
        from bs4 import BeautifulSoup
        html_content = results[0].get('html', '') if results else ''
        soup = BeautifulSoup(html_content, 'html.parser')
        text_content = soup.get_text(separator=' ', strip=True)
        
        # Automatically trigger lead processing with the crawled content
        lead_job = Job('lead_processing', {
            'text': text_content,
            'html': html_content,
            'source_url': url
        })
        job_queue.add_job(lead_job)
        integration_debug_logger.info(f"[crawl_job_handler] Triggered lead processing job {lead_job.id} for URL {url}")
        logger.log("info", "crawl_job_handler_triggered_lead_processing", url=url, lead_job_id=lead_job.id)
        
        # Simplified logging for crawl_job_handler_end
        logger.log("info", "crawl_job_handler_end", url=url)
        return {"crawl_results": results}
        
    except Exception as e:
        error_msg = f"Exception during crawl of URL {url}: {str(e)}"
        logger.log("error", "crawl_job_handler_exception", url=url, error=error_msg)
        job.error = error_msg
        return {"crawl_results": [], "error": error_msg}

def lead_processing_handler(job: Job):
    integration_debug_logger.info(f"[lead_processing_handler] job_type={job.type}, payload={job.payload}")
    logger.log("info", "lead_processing_handler_start:", job_type=job.type)
    text = job.payload.get('text', '')
    html = job.payload.get('html', '')
    source_url = job.payload.get('source_url', 'unknown')
    
    # Log content lengths for debugging
    text_length = len(text) if text else 0
    html_length = len(html) if html else 0
    integration_debug_logger.info(f"[lead_processing_handler] Processing content from {source_url}: text_length={text_length}, html_length={html_length}")
    
    try:
        # Extract leads using all methods with timeout protection
        import concurrent.futures
        
        # Pattern extraction (fast, no timeout needed)
        pattern_leads = extract_pattern_leads(text)
        
        # Structured extraction (fast, no timeout needed)
        structured_leads = extract_structured_leads(html)
        
        # AI extraction with timeout
        ai_leads = {"ai_leads": [], "confidence": 0.0, "explanation": "AI extraction skipped due to timeout"}
        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(ai_extract_leads, text, html)
                try:
                    ai_leads = future.result(timeout=20)  # 20 second timeout for AI extraction
                except concurrent.futures.TimeoutError:
                    integration_debug_logger.warning(f"[lead_processing_handler] AI extraction timed out for {source_url}")
                    ai_leads = {"ai_leads": [], "confidence": 0.0, "explanation": "AI extraction timed out"}
        except Exception as e:
            integration_debug_logger.error(f"[lead_processing_handler] AI extraction failed for {source_url}: {e}")
            ai_leads = {"ai_leads": [], "confidence": 0.0, "explanation": f"AI extraction failed: {e}"}
        
        # Store pattern-based leads as well
        pattern_lead_objects = []
        for email in pattern_leads.get('emails', []):
            pattern_lead_objects.append({
                'business_name': 'Unknown Business',
                'contact_person': None,
                'email': email,
                'phone': None,
                'address': None,
                'website': None,
                'lead_type': 'email_contact',
                'confidence_score': 0.9,
                'extraction_method': 'pattern_extraction',
                'created_at': datetime.utcnow(),
                'source_url': source_url
            })
        
        for phone in pattern_leads.get('phones', []):
            pattern_lead_objects.append({
                'business_name': 'Unknown Business',
                'contact_person': None,
                'email': None,
                'phone': phone,
                'address': None,
                'website': None,
                'lead_type': 'phone_contact',
                'confidence_score': 0.8,
                'extraction_method': 'pattern_extraction',
                'created_at': datetime.utcnow(),
                'source_url': source_url
            })
        
        for business_name in pattern_leads.get('business_names', []):
            pattern_lead_objects.append({
                'business_name': business_name,
                'contact_person': None,
                'email': None,
                'phone': None,
                'address': None,
                'website': None,
                'lead_type': 'business_name',
                'confidence_score': 0.7,
                'extraction_method': 'pattern_extraction',
                'created_at': datetime.utcnow(),
                'source_url': source_url
            })
        
        # Score and store pattern leads
        for lead in pattern_lead_objects:
            try:
                lead['scoring'] = score_lead(lead)
                leads_store.append(lead)
                # Store in database
                lead_storage.store_lead_in_db(lead)
            except Exception as e:
                integration_debug_logger.error(f"[lead_processing_handler] Failed to score pattern lead: {e}")
                lead['scoring'] = {"completeness_score": 0.0, "relevance_score": 0.0, "freshness_score": 0.0, "final_score": 0.0}
                leads_store.append(lead)
                # Store in database even if scoring failed
                lead_storage.store_lead_in_db(lead)
        
        # Score all AI leads and store them
        scored = []
        for lead in ai_leads.get('ai_leads', []):
            try:
                # Ensure lead has required fields and proper structure
                if isinstance(lead, dict):
                    # Add missing fields with defaults
                    lead.setdefault('business_name', 'Unknown Business')
                    lead.setdefault('contact_person', None)
                    lead.setdefault('email', None)
                    lead.setdefault('phone', None)
                    lead.setdefault('address', None)
                    lead.setdefault('website', None)
                    lead.setdefault('lead_type', 'travel_business')
                    lead.setdefault('confidence_score', 0.5)
                    lead.setdefault('extraction_method', 'ai_extraction')
                    lead.setdefault('created_at', datetime.utcnow())
                    
                    lead['scoring'] = score_lead(lead)
                    lead['source_url'] = source_url  # Add source URL to track origin
                    leads_store.append(lead)
                    # Store in database
                    lead_storage.store_lead_in_db(lead)
                    scored.append(lead)
                else:
                    integration_debug_logger.warning(f"[lead_processing_handler] Skipping invalid lead format: {lead}")
            except Exception as e:
                integration_debug_logger.error(f"[lead_processing_handler] Failed to process AI lead: {e}")
                continue
        
        # Log detailed results for debugging
        total_pattern_leads = len(pattern_lead_objects)
        total_ai_leads = len(scored)
        total_leads = total_pattern_leads + total_ai_leads
        integration_debug_logger.info(f"[lead_processing_handler] Extracted {total_leads} total leads from {source_url} (pattern: {total_pattern_leads}, AI: {total_ai_leads})")
        
        logger.log("info", "lead_processing_handler_end", total_leads=total_leads)
        return {"pattern_leads": pattern_leads, "structured_leads": structured_leads, "ai_leads": scored, "pattern_lead_objects": pattern_lead_objects}
        
    except Exception as e:
        error_msg = f"Exception during lead processing for {source_url}: {str(e)}"
        logger.log("error", "lead_processing_handler_exception", source_url=source_url, error=error_msg)
        job.error = error_msg
        return {"pattern_leads": {}, "structured_leads": {}, "ai_leads": [], "pattern_lead_objects": [], "error": error_msg}

@app.post("/search", response_model=SearchJobResponse)
def submit_search_job(req: SearchJobRequest):
    job = Job('search', req.model_dump(), priority=req.priority)
    job_queue.add_job(job)
    logger.log("info", "submit_search_job", job_id=job.id, status="queued", submitted_at=job.created_at)
    return SearchJobResponse(job_id=job.id, status="queued", submitted_at=job.created_at)

@app.post("/crawl", response_model=CrawlJobResponse)
def submit_crawl_job(req: CrawlJobRequest):
    job = Job('crawl', req.model_dump(), priority=req.priority)
    job_queue.add_job(job)
    logger.log("info", "submit_crawl_job", job_id=job.id, status="queued", submitted_at=job.created_at)
    return CrawlJobResponse(job_id=job.id, status="queued", submitted_at=job.created_at)

@app.post("/leads/process", response_model=dict)
def process_leads(text: str = '', html: str = ''):
    job = Job('lead_processing', {'text': text, 'html': html})
    job_queue.add_job(job)
    logger.log("info", "process_leads", job_id=job.id, status="queued", submitted_at=job.created_at)
    return {"job_id": job.id, "status": "queued", "submitted_at": job.created_at}

@app.post("/search_and_crawl", response_model=dict)
def search_and_crawl(req: SearchJobRequest, background_tasks: BackgroundTasks):
    integration_debug_logger.info("[search_and_crawl] Submitting search job...")
    job = Job('search', req.model_dump(), priority=req.priority)
    job_queue.add_job(job)
    integration_debug_logger.info(f"[search_and_crawl] Search job submitted: {job.id}")
    def chain_crawl_jobs():
        import time
        # Wait for search job to complete with better timeout handling
        timeout = 45  # Reduced timeout to prevent hanging
        poll_interval = 0.5  # Faster polling
        waited = 0
        max_retries = 3
        retry_count = 0
        
        while waited < timeout and retry_count < max_retries:
            try:
                j = job_queue.get_job(job.id)
                if j and j.status == 'completed' and j.result:
                    integration_debug_logger.info(f"[search_and_crawl] Search job {job.id} completed. Result: {j.result}")
                    search_results = j.result.get('search_results', [])
                    integration_debug_logger.info(f"[search_and_crawl] URLs to crawl: {[item.get('url') for item in search_results]}")
                    
                    # Limit the number of crawl jobs to prevent overwhelming the system
                    max_crawl_jobs = 10
                    crawl_jobs_created = 0
                    
                    for idx, item in enumerate(search_results):
                        if crawl_jobs_created >= max_crawl_jobs:
                            integration_debug_logger.info(f"[search_and_crawl] Reached max crawl jobs limit ({max_crawl_jobs})")
                            break
                            
                        url = item.get('url') or item.get('link')
                        if url:
                            try:
                                crawl_job = Job('crawl', {'url': url})
                                job_queue.add_job(crawl_job)
                                crawl_jobs_created += 1
                                integration_debug_logger.info(f"[search_and_crawl] Submitted crawl job for URL {url} (job_id={crawl_job.id})")
                            except Exception as e:
                                integration_debug_logger.error(f"[search_and_crawl] Failed to create crawl job for {url}: {e}")
                                continue
                    return
                elif j and j.status == 'failed':
                    integration_debug_logger.error(f"[search_and_crawl] Search job {job.id} failed: {j.error}")
                    return
                elif j and j.status == 'cancelled':
                    integration_debug_logger.error(f"[search_and_crawl] Search job {job.id} was cancelled")
                    return
                elif not j:
                    integration_debug_logger.warning(f"[search_and_crawl] Job {job.id} not found, retrying...")
                    retry_count += 1
                    
            except Exception as e:
                integration_debug_logger.error(f"[search_and_crawl] Error checking job status: {e}")
                retry_count += 1
                
            time.sleep(poll_interval)
            waited += poll_interval
            
        integration_debug_logger.error(f"[search_and_crawl] Timeout waiting for search job {job.id} to complete after {timeout} seconds.")
    background_tasks.add_task(chain_crawl_jobs)
    return {"search_job_id": job.id, "status": "search_queued"}

@app.get("/jobs/{job_id}", response_model=dict)
def get_job_status(job_id: str):
    job = job_queue.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job_id": job.id,
        "type": job.type,
        "status": job.status,
        "progress": job.progress,
        "result": job.result,
        "error": job.error,
        "payload": job.payload,  # ADD PAYLOAD FOR URL
        "created_at": job.created_at,
        "updated_at": job.updated_at
    }

@app.get("/jobs", response_model=List[dict])
def list_jobs():
    return [
        {
            "job_id": job.id,
            "type": job.type,
            "status": job.status,
            "progress": job.progress,
            "payload": job.payload,  # ADD PAYLOAD FOR URL
            "created_at": job.created_at,
            "updated_at": job.updated_at
        }
        for job in job_queue.all_jobs()
    ]

@app.get("/status", response_model=dict)
def system_status():
    return {
        "search_jobs": len([j for j in job_queue.all_jobs() if j.type == 'search' and j.status in ('pending', 'in_progress')]),
        "crawl_jobs": len([j for j in job_queue.all_jobs() if j.type == 'crawl' and j.status in ('pending', 'in_progress')]),
        "leads": len(leads_store),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/export", response_model=List[LeadResponse])
def export_leads():
    # Try to get leads from database first, fallback to memory
    try:
        db_leads = lead_storage.get_leads_from_db()
        if db_leads:
            mapped_leads = []
            for lead in db_leads:
                try:
                    # Map database fields to LeadResponse schema
                    mapped_lead = {
                        "id": lead.get("id", None),
                        "business_name": lead.get("business_name", None),
                        "contact_person": lead.get("contact_person", None),
                        "email": lead.get("email", None),
                        "phone": lead.get("phone", None),
                        "address": lead.get("address", None),
                        "website": lead.get("website", None),
                        "lead_type": lead.get("lead_type", None),
                        "confidence_score": lead.get("confidence_score", None),
                        "extraction_method": lead.get("extraction_method", None),
                        "created_at": lead.get("created_at", None),
                        "scoring": lead.get("scoring", None),
                        "source_url": lead.get("source_url", None)
                    }
                    # Remove None values to avoid validation issues
                    mapped_lead = {k: v for k, v in mapped_lead.items() if v is not None}
                    mapped_leads.append(LeadResponse(**mapped_lead))
                except Exception as e:
                    integration_debug_logger.error(f"[export_leads] Failed to map database lead: {lead}, error: {e}")
                    continue
            return mapped_leads
    except Exception as e:
        integration_debug_logger.error(f"[export_leads] Failed to get leads from database: {e}")
    
    # Fallback to memory store
    mapped_leads = []
    for lead in leads_store:
        try:
            # Map AI extraction fields to LeadResponse schema
            mapped_lead = {
                "id": lead.get("id", None),
                "business_name": lead.get("business_name", None),
                "contact_person": lead.get("contact_person", None),
                "email": lead.get("email", None),
                "phone": lead.get("phone", None),
                "address": lead.get("address", None),
                "website": lead.get("website", None),
                "lead_type": lead.get("lead_type", None),
                "confidence_score": lead.get("confidence_score", None),
                "extraction_method": lead.get("extraction_method", None),
                "created_at": lead.get("created_at", None),
                "scoring": lead.get("scoring", None),
                "source_url": lead.get("source_url", None)  # Additional field for tracking
            }
            # Remove None values to avoid validation issues
            mapped_lead = {k: v for k, v in mapped_lead.items() if v is not None}
            mapped_leads.append(LeadResponse(**mapped_lead))
        except Exception as e:
            # Log the problematic lead and skip it
            integration_debug_logger.error(f"[export_leads] Failed to map memory lead: {lead}, error: {e}")
            continue
    return mapped_leads

@app.post("/leads/add", response_model=LeadResponse)
def add_lead(lead: LeadResponse):
    # Use model_dump(mode='json') if available (Pydantic v2+), else fallback to json.loads(lead.json())
    if hasattr(lead, "model_dump"):
        lead_dict = lead.model_dump(mode="json")
    else:
        import json
        lead_dict = json.loads(lead.json())
    scoring = score_lead(lead_dict)
    lead_dict["scoring"] = scoring
    leads_store.append(lead_dict)
    # Store in database
    lead_storage.store_lead_in_db(lead_dict)
    return LeadResponse(**lead_dict)

@app.get("/export/csv", response_class=FileResponse)
def export_leads_csv():
    try:
        # Try to get leads from database first
        db_leads = lead_storage.get_leads_from_db()
        if db_leads:
            filepath = lead_storage.export_leads_to_csv(db_leads)
            filename = os.path.basename(filepath)
            return FileResponse(filepath, filename=filename, media_type="text/csv")
    except Exception as e:
        integration_debug_logger.error(f"[export_leads_csv] Failed to export from database: {e}")
    
    # Fallback to memory store
    if leads_store:
        filepath = lead_storage.export_leads_to_csv(leads_store)
        filename = os.path.basename(filepath)
        return FileResponse(filepath, filename=filename, media_type="text/csv")
    
    # If no leads in database or memory, create empty CSV
    try:
        empty_leads = []
        filepath = lead_storage.export_leads_to_csv(empty_leads, "empty_leads.csv")
        filename = os.path.basename(filepath)
        return FileResponse(filepath, filename=filename, media_type="text/csv")
    except Exception as e:
        integration_debug_logger.error(f"[export_leads_csv] Failed to create empty CSV: {e}")
        raise HTTPException(status_code=500, detail="Failed to create CSV export")

@app.get("/export/excel", response_class=FileResponse)
def export_leads_excel():
    try:
        # Try to get leads from database first
        db_leads = lead_storage.get_leads_from_db()
        if db_leads:
            filepath = lead_storage.export_leads_to_excel(db_leads)
            filename = os.path.basename(filepath)
            return FileResponse(filepath, filename=filename, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception as e:
        integration_debug_logger.error(f"[export_leads_excel] Failed to export from database: {e}")
    
    # Fallback to memory store
    if not leads_store:
        raise HTTPException(status_code=404, detail="No leads to export")
    
    filepath = lead_storage.export_leads_to_excel(leads_store)
    filename = os.path.basename(filepath)
    return FileResponse(filepath, filename=filename, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@app.get("/export/json", response_class=FileResponse)
def export_leads_json():
    try:
        # Try to get leads from database first
        db_leads = lead_storage.get_leads_from_db()
        if db_leads:
            filepath = lead_storage.export_leads_to_json(db_leads)
            filename = os.path.basename(filepath)
            return FileResponse(filepath, filename=filename, media_type="application/json")
    except Exception as e:
        integration_debug_logger.error(f"[export_leads_json] Failed to export from database: {e}")
    
    # Fallback to memory store
    if not leads_store:
        raise HTTPException(status_code=404, detail="No leads to export")
    
    filepath = lead_storage.export_leads_to_json(leads_store)
    filename = os.path.basename(filepath)
    return FileResponse(filepath, filename=filename, media_type="application/json")

@app.get("/metrics", response_model=dict)
def system_metrics():
    return get_system_metrics()

@app.get("/analytics", response_model=dict)
def analytics():
    return perf_tracker.get_analytics()

@app.post("/log", response_model=dict)
def log_event(event: str, level: str = "info", details: dict = {}):
    logger.log(level, event, **details)
    return {"status": "logged"} 

@app.get("/leads/stats", response_model=dict)
def get_lead_stats():
    """Get lead statistics from database"""
    try:
        db_count = lead_storage.get_lead_count_from_db()
        memory_count = len(leads_store)
        
        return {
            "database_leads": db_count,
            "memory_leads": memory_count,
            "total_leads": max(db_count, memory_count),  # Use the higher count
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        integration_debug_logger.error(f"[get_lead_stats] Error: {e}")
        return {
            "database_leads": 0,
            "memory_leads": len(leads_store),
            "total_leads": len(leads_store),
            "timestamp": datetime.utcnow().isoformat()
        }

@app.get("/leads/db", response_model=List[LeadResponse])
def get_leads_from_db(limit: Optional[int] = Query(None, description="Maximum number of leads to return"), 
                      offset: int = Query(0, description="Number of leads to skip")):
    """Get leads from database"""
    try:
        db_leads = lead_storage.get_leads_from_db(limit=limit, offset=offset)
        mapped_leads = []
        for lead in db_leads:
            try:
                mapped_lead = {
                    "id": lead.get("id", None),
                    "business_name": lead.get("business_name", None),
                    "contact_person": lead.get("contact_person", None),
                    "email": lead.get("email", None),
                    "phone": lead.get("phone", None),
                    "address": lead.get("address", None),
                    "website": lead.get("website", None),
                    "lead_type": lead.get("lead_type", None),
                    "confidence_score": lead.get("confidence_score", None),
                    "extraction_method": lead.get("extraction_method", None),
                    "created_at": lead.get("created_at", None),
                    "scoring": lead.get("scoring", None),
                    "source_url": lead.get("source_url", None)
                }
                mapped_lead = {k: v for k, v in mapped_lead.items() if v is not None}
                mapped_leads.append(LeadResponse(**mapped_lead))
            except Exception as e:
                integration_debug_logger.error(f"[get_leads_from_db] Failed to map lead: {lead}, error: {e}")
                continue
        return mapped_leads
    except Exception as e:
        integration_debug_logger.error(f"[get_leads_from_db] Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve leads from database: {str(e)}")

@app.post("/leads/export/all", response_model=dict)
def export_all_leads():
    """Export all leads to all formats (CSV, Excel, JSON)"""
    try:
        # Get leads from database first, fallback to memory
        leads_to_export = []
        try:
            db_leads = lead_storage.get_leads_from_db()
            if db_leads:
                leads_to_export = db_leads
        except Exception as e:
            integration_debug_logger.error(f"[export_all_leads] Failed to get leads from database: {e}")
        
        if not leads_to_export:
            leads_to_export = leads_store
        
        if not leads_to_export:
            raise HTTPException(status_code=404, detail="No leads to export")
        
        # Export to all formats
        csv_file = lead_storage.export_leads_to_csv(leads_to_export)
        excel_file = lead_storage.export_leads_to_excel(leads_to_export)
        json_file = lead_storage.export_leads_to_json(leads_to_export)
        
        return {
            "message": f"Successfully exported {len(leads_to_export)} leads to all formats",
            "files": {
                "csv": os.path.basename(csv_file),
                "excel": os.path.basename(excel_file),
                "json": os.path.basename(json_file)
            },
            "lead_count": len(leads_to_export),
            "exported_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        integration_debug_logger.error(f"[export_all_leads] Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export leads: {str(e)}") 