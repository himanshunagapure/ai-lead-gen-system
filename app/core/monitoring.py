import logging
import json
import os
import psutil
from datetime import datetime
from typing import Dict, Any

LOGS_DIR = os.path.join("data", "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

# Structured JSON logger
class JsonLogger:
    def __init__(self, name: str, log_file: str = None, log_level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)
        if log_file:
            handler = logging.FileHandler(log_file)
            handler.setFormatter(logging.Formatter('%(message)s'))
            self.logger.addHandler(handler)

    def log(self, level: str, event: str, **kwargs):
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "event": event,
            **kwargs
        }
        self.logger.log(getattr(logging, level.upper(), logging.INFO), json.dumps(entry, default=str))

# System monitoring

def get_system_metrics() -> Dict[str, Any]:
    return {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent,
        "uptime_seconds": (datetime.utcnow() - datetime.fromtimestamp(psutil.boot_time())).total_seconds(),
        "timestamp": datetime.utcnow().isoformat()
    }

# Performance analytics
class PerformanceTracker:
    def __init__(self):
        self.metrics = {
            "pages_crawled": 0,
            "leads_extracted": 0,
            "api_calls": 0,
            "api_cost": 0.0,
            "start_time": datetime.utcnow(),
            "crawl_efficiency": [],  # (domain, pages/hour)
        }

    def record_crawl(self, domain: str, pages: int, duration_sec: float):
        self.metrics["pages_crawled"] += pages
        if duration_sec > 0:
            self.metrics["crawl_efficiency"].append((domain, pages / (duration_sec / 3600)))

    def record_lead(self, count: int = 1):
        self.metrics["leads_extracted"] += count

    def record_api_call(self, cost: float = 0.0):
        self.metrics["api_calls"] += 1
        self.metrics["api_cost"] += cost

    def get_analytics(self) -> Dict[str, Any]:
        elapsed = (datetime.utcnow() - self.metrics["start_time"]).total_seconds() / 3600
        return {
            **self.metrics,
            "leads_per_hour": self.metrics["leads_extracted"] / elapsed if elapsed > 0 else 0,
            "pages_per_hour": self.metrics["pages_crawled"] / elapsed if elapsed > 0 else 0,
            "avg_api_cost_per_lead": (self.metrics["api_cost"] / self.metrics["leads_extracted"]) if self.metrics["leads_extracted"] else 0,
            "uptime_hours": elapsed
        } 