from typing import List, Dict, Any, Set
import re
from app.core.monitoring import JsonLogger
import os
import logging
logger = JsonLogger("search_result_processor", os.path.join("data", "logs", "app.log"), log_level=logging.DEBUG)

TRAVEL_DOMAINS = [
    "hotel", "resort", "hostel", "restaurant", "tour", "travel", "blog", "event"
]

CONTENT_TYPES = {
    "blog": ["blog", "post"],
    "business": ["hotel", "resort", "restaurant", "agency", "operator"],
    "social": ["facebook", "instagram", "twitter", "linkedin"]
}

def filter_domain_quality(url: str) -> bool:
    # Simple filter: avoid spammy or irrelevant domains
    spam_domains = ["pinterest.com", "yelp.com", "tripadvisor.com", "reddit.com", "quora.com"]
    for spam in spam_domains:
        if spam in url:
            return False
    return True

def deduplicate_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen: Set[str] = set()
    deduped = []
    for item in results:
        url = item.get("url")  # FIXED: use 'url' instead of 'link'
        if url and url not in seen:
            seen.add(url)
            deduped.append(item)
    return deduped

def categorize_result(url: str, title: str = "") -> str:
    for ctype, keywords in CONTENT_TYPES.items():
        for kw in keywords:
            if kw in url.lower() or kw in title.lower():
                return ctype
    return "other"

def process_search_results(raw_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    processed = []
    for item in raw_results:
        url = item.get("link")
        title = item.get("title", "")
        description = item.get("snippet", "")
        if not url:
            logger.log("debug", "process_search_results_skip", reason="missing_url")
            continue
        if not filter_domain_quality(url):
            logger.log("debug", "process_search_results_filtered", reason="domain_quality", url=url)
            continue
        category = categorize_result(url, title)
        logger.log("debug", "process_search_results_accepted", url=url, category=category)
        processed.append({
            "url": url,
            "title": title,
            "description": description,
            "category": category,
            # Do not log or include pagemap or full item in logs
            "metadata": {
                "displayLink": item.get("displayLink"),
                "cacheId": item.get("cacheId"),
            }
        })
    logger.log("debug", "process_search_results_summary", total_accepted=len(processed), total_input=len(raw_results))
    return deduplicate_results(processed) 