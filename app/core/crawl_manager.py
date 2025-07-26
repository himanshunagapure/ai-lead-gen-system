import asyncio
import time
from collections import defaultdict, deque
from typing import Dict, Set, Deque, Optional, List, Tuple
import requests
from urllib.parse import urlparse
import urllib.robotparser

class CrawlJob:
    def __init__(self, url: str, priority: int = 0, domain: Optional[str] = None):
        self.url = url
        self.priority = priority
        self.domain = domain or self.extract_domain(url)
        self.status = 'pending'  # pending, in_progress, done, failed, skipped
        self.retries = 0
        self.last_attempt = None
        self.result = None

    @staticmethod
    def extract_domain(url: str) -> str:
        from urllib.parse import urlparse
        return urlparse(url).netloc

    def __lt__(self, other):
        return (self.priority, self.url) < (other.priority, other.url)

class CrawlManager:
    """
    CrawlManager manages crawl jobs with politeness and crawl budget per domain.
    Production best practices:
    - crawl_budget_per_domain: Set to 100 by default (increase for more thorough crawling).
    - politeness_delay: Keep at 1–2 seconds or more to avoid overloading or getting blocked.
    - Always respect robots.txt in production to avoid legal/ethical issues.
    """
    def __init__(self, max_retries: int = 2, crawl_budget_per_domain: int = 100, politeness_delay: float = 2.0, user_agent: str = '*'):
        self.queue: List[CrawlJob] = []
        self.visited: Set[str] = set()
        self.failed: Set[str] = set()
        self.in_progress: Set[str] = set()
        self.domain_last_crawl: Dict[str, float] = defaultdict(lambda: 0.0)
        self.domain_crawl_budget: Dict[str, int] = defaultdict(lambda: crawl_budget_per_domain)
        self.max_retries = max_retries
        self.politeness_delay = politeness_delay
        self.status: Dict[str, str] = {}  # url -> status
        self.user_agent = user_agent
        self._robots_parsers: Dict[str, urllib.robotparser.RobotFileParser] = {}

    def _is_allowed_by_robots(self, url: str) -> bool:
        """
        Checks robots.txt for the domain of the given URL. Caches the parser per domain.
        Returns True if allowed, False if disallowed or robots.txt cannot be fetched.
        """
        parsed = urlparse(url)
        domain = parsed.netloc
        robots_url = f"{parsed.scheme}://{domain}/robots.txt"
        parser = self._robots_parsers.get(domain)
        if parser is None:
            parser = urllib.robotparser.RobotFileParser()
            try:
                resp = requests.get(robots_url, timeout=5)
                if resp.status_code == 200:
                    parser.parse(resp.text.splitlines())
                else:
                    # If robots.txt not found, allow by default
                    self._robots_parsers[domain] = parser
                    return True
            except Exception:
                # On network error, allow by default
                self._robots_parsers[domain] = parser
                return True
            self._robots_parsers[domain] = parser
        return parser.can_fetch(self.user_agent, url)

    def add_job(self, url: str, priority: int = 0):
        if url in self.visited or url in self.in_progress:
            return
        job = CrawlJob(url, priority)
        self.queue.append(job)
        self.queue.sort()  # maintain priority
        self.status[url] = 'pending'

    def get_next_job(self) -> Optional[CrawlJob]:
        while self.queue:
            job = self.queue.pop(0)
            if job.url in self.visited:
                continue
            if not self._is_allowed_by_robots(job.url):
                self.status[job.url] = 'skipped_robots'
                continue
            if self.domain_crawl_budget[job.domain] <= 0:
                self.status[job.url] = 'skipped'
                continue
            now = time.time()
            if now - self.domain_last_crawl[job.domain] < self.politeness_delay:
                # Requeue at end for politeness
                self.queue.append(job)
                continue
            self.in_progress.add(job.url)
            self.status[job.url] = 'in_progress'
            return job
        return None

    def mark_done(self, job: CrawlJob, result: Optional[dict] = None):
        self.visited.add(job.url)
        self.in_progress.discard(job.url)
        self.domain_last_crawl[job.domain] = time.time()
        self.domain_crawl_budget[job.domain] -= 1
        self.status[job.url] = 'done'
        job.status = 'done'
        job.result = result

    def mark_failed(self, job: CrawlJob):
        self.in_progress.discard(job.url)
        job.retries += 1
        job.last_attempt = time.time()
        if job.retries > self.max_retries:
            self.failed.add(job.url)
            self.status[job.url] = 'failed'
            job.status = 'failed'
        else:
            self.queue.append(job)
            self.status[job.url] = 'retrying'
            job.status = 'retrying'

    def get_status(self, url: str) -> str:
        return self.status.get(url, 'unknown')

    def get_all_statuses(self) -> Dict[str, str]:
        return dict(self.status)

    def get_failed_jobs(self) -> List[str]:
        return list(self.failed)

    def get_done_jobs(self) -> List[str]:
        return [url for url, status in self.status.items() if status == 'done'] 