import asyncio
import time
from typing import Dict, Any, Callable, Optional, List
from collections import deque
from datetime import datetime
import threading
import logging
import os

# Setup logger for integration debug
os.makedirs('data/logs', exist_ok=True)
logging.basicConfig(
    filename='data/logs/integration_debug.log',
    filemode='a',
    format='%(asctime)s %(levelname)s %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("integration_debug")

class Job:
    def __init__(self, job_type: str, payload: dict, priority: int = 0):
        self.id = f"job-{int(time.time() * 1000)}"
        self.type = job_type
        self.payload = payload
        self.priority = priority
        self.status = 'pending'  # pending, in_progress, done, failed, cancelled
        self.result = None
        self.error = None
        self.created_at = datetime.utcnow()
        self.updated_at = self.created_at
        self.progress = 0.0
        self.cancelled = False
        self.retries = 0
        self.max_retries = 2

class JobQueue:
    def __init__(self):
        self.queue: List[Job] = []
        self.jobs: Dict[str, Job] = {}
        self.lock = threading.Lock()

    def add_job(self, job: Job):
        with self.lock:
            self.queue.append(job)
            self.queue.sort(key=lambda j: (j.priority, j.created_at))
            self.jobs[job.id] = job

    def get_next_job(self) -> Optional[Job]:
        with self.lock:
            for i, job in enumerate(self.queue):
                if job.status == 'pending' and not job.cancelled:
                    job.status = 'in_progress'
                    job.updated_at = datetime.utcnow()
                    return self.queue.pop(i)
        return None

    def get_next_job_of_type(self, job_type: str) -> Optional[Job]:
        with self.lock:
            for i, job in enumerate(self.queue):
                if job.status == 'pending' and not job.cancelled and job.type == job_type:
                    job.status = 'in_progress'
                    job.updated_at = datetime.utcnow()
                    return self.queue.pop(i)
        return None

    def get_job(self, job_id: str) -> Optional[Job]:
        return self.jobs.get(job_id)

    def cancel_job(self, job_id: str):
        job = self.get_job(job_id)
        if job:
            job.cancelled = True
            job.status = 'cancelled'
            job.updated_at = datetime.utcnow()

    def update_progress(self, job_id: str, progress: float):
        job = self.get_job(job_id)
        if job:
            job.progress = progress
            job.updated_at = datetime.utcnow()

    def all_jobs(self):
        return list(self.jobs.values())

class BaseWorker(threading.Thread):
    def __init__(self, job_queue: JobQueue, handler: Callable[[Job], Any], job_type: str, poll_interval: float = 1.0, job_timeout: float = 60.0):
        super().__init__(daemon=True)
        self.job_queue = job_queue
        self.handler = handler
        self.job_type = job_type
        self.poll_interval = poll_interval
        self.job_timeout = job_timeout
        self.running = True

    def run(self):
        while self.running:
            job = self.job_queue.get_next_job_of_type(self.job_type)
            if job:
                logger.info(f"[BaseWorker] Handling job: id={job.id}, type={job.type}, payload={job.payload}")
                try:
                    # Use threading.Timer for cross-platform timeout handling
                    import threading
                    import queue
                    
                    # Create a queue to communicate between threads
                    result_queue = queue.Queue()
                    exception_queue = queue.Queue()
                    
                    def job_worker():
                        try:
                            result = self.handler(job)
                            result_queue.put(('success', result))
                        except Exception as e:
                            exception_queue.put(('error', e))
                    
                    # Start the job in a separate thread
                    worker_thread = threading.Thread(target=job_worker, daemon=True)
                    worker_thread.start()
                    
                    # Wait for completion with timeout
                    try:
                        worker_thread.join(timeout=self.job_timeout)
                        
                        if worker_thread.is_alive():
                            # Job timed out
                            logger.error(f"[BaseWorker] Job {job.id} timed out after {self.job_timeout} seconds")
                            job.error = f"Job timed out after {self.job_timeout} seconds"
                            job.status = 'failed'
                            job.progress = 1.0
                            job.updated_at = datetime.utcnow()
                        else:
                            # Check for exceptions first
                            try:
                                exc_type, exc_value = exception_queue.get_nowait()
                                logger.error(f"[BaseWorker] Handler {self.handler.__name__} failed for job {job.id}: {exc_value}")
                                job.error = str(exc_value)
                                job.status = 'failed'
                                job.progress = 1.0
                                job.updated_at = datetime.utcnow()
                            except queue.Empty:
                                # No exception, check for result
                                try:
                                    result_type, result = result_queue.get_nowait()
                                    logger.info(f"[BaseWorker] Handler {self.handler.__name__} returned result for job {job.id}")
                                    job.result = result
                                    job.status = 'completed'
                                    job.progress = 1.0
                                    job.updated_at = datetime.utcnow()
                                except queue.Empty:
                                    # This shouldn't happen, but handle it gracefully
                                    logger.error(f"[BaseWorker] No result or exception for job {job.id}")
                                    job.error = "No result or exception returned"
                                    job.status = 'failed'
                                    job.progress = 1.0
                                    job.updated_at = datetime.utcnow()
                                    
                    except Exception as e:
                        logger.error(f"[BaseWorker] Unexpected error handling job {job.id}: {e}")
                        job.error = str(e)
                        job.status = 'failed'
                        job.progress = 1.0
                        job.updated_at = datetime.utcnow()
                            
                except Exception as e:
                    logger.error(f"[BaseWorker] Handler {self.handler.__name__} failed for job {job.id}: {e}")
                    job.error = str(e)
                    job.status = 'failed'
                    job.progress = 1.0
                    job.updated_at = datetime.utcnow()
            time.sleep(self.poll_interval)

    def stop(self):
        self.running = False

# This module only defines the job queue and worker system. All job handlers should be defined elsewhere and imported as needed. 