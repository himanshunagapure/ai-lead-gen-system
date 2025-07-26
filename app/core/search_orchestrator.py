import asyncio
import heapq
import time
from typing import Any, Dict, List, Optional, Tuple
from app.core.search_client import GoogleSearchClient
from app.core.query_builder import build_query
from app.core.search_result_processor import process_search_results

class SearchJob:
    def __init__(self, query: str, priority: int = 0, max_results: int = 30, intent: Optional[str] = None, location: Optional[str] = None):
        self.query = query
        self.priority = priority
        self.max_results = max_results
        self.intent = intent
        self.location = location
        self.timestamp = time.time()

    def __lt__(self, other):
        # Lower priority value means higher priority
        return (self.priority, self.timestamp) < (other.priority, other.timestamp)

class SearchJobQueue:
    def __init__(self):
        self._queue: List[Tuple[int, float, SearchJob]] = []
        self._lock = asyncio.Lock()

    async def add_job(self, job: SearchJob):
        async with self._lock:
            heapq.heappush(self._queue, (job.priority, job.timestamp, job))

    async def get_next_job(self) -> Optional[SearchJob]:
        async with self._lock:
            if self._queue:
                return heapq.heappop(self._queue)[2]
            return None

    def __len__(self):
        return len(self._queue)

class SearchOrchestrator:
    def __init__(self):
        self.job_queue = SearchJobQueue()
        self.client = GoogleSearchClient()
        self.metrics = {
            "total_jobs": 0,
            "total_results": 0,
            "deduped_results": 0,
            "start_time": None,
            "end_time": None,
        }

    async def submit_search_job(self, query: str, priority: int = 0, max_results: int = 30, intent: Optional[str] = None, location: Optional[str] = None):
        job = SearchJob(query, priority, max_results, intent, location)
        await self.job_queue.add_job(job)
        self.metrics["total_jobs"] += 1

    async def run(self):
        self.metrics["start_time"] = time.time()
        while len(self.job_queue) > 0:
            job = await self.job_queue.get_next_job()
            if not job:
                break
            # Build advanced query
            search_query = build_query(base=job.query, location=job.location)
            raw_results = await self.client.paginated_search(search_query, max_results=job.max_results)
            self.metrics["total_results"] += len(raw_results)
            processed = process_search_results(raw_results)
            self.metrics["deduped_results"] += len(processed)
            # Here you could store results to DB or return them
            print(f"Job: {job.query} | Results: {len(processed)}")
        self.metrics["end_time"] = time.time()

    async def run_and_return_results(self):
        all_results = []
        self.metrics["start_time"] = time.time()
        while len(self.job_queue) > 0:
            job = await self.job_queue.get_next_job()
            if not job:
                break
            search_query = build_query(base=job.query, location=job.location)
            raw_results = await self.client.paginated_search(search_query, max_results=job.max_results)
            self.metrics["total_results"] += len(raw_results)
            processed = process_search_results(raw_results)
            self.metrics["deduped_results"] += len(processed)
            all_results.extend(processed)
            print(f"Job: {job.query} | Results: {len(processed)}")
        self.metrics["end_time"] = time.time()
        return all_results

    def get_metrics(self) -> Dict[str, Any]:
        elapsed = None
        if self.metrics["start_time"] and self.metrics["end_time"]:
            elapsed = self.metrics["end_time"] - self.metrics["start_time"]
        return {
            **self.metrics,
            "elapsed_time": elapsed
        } 