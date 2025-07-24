from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import List, Set, Optional
import re
import requests

def extract_links(html: str, base_url: str) -> List[str]:
    soup = BeautifulSoup(html, "lxml")
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.startswith("#") or href.lower().startswith("javascript:"):
            continue
        full_url = urljoin(base_url, href)
        links.add(full_url)
    return list(links)

def filter_travel_links(links: List[str]) -> List[str]:
    travel_keywords = [
        "hotel", "resort", "hostel", "restaurant", "tour", "travel", "blog", "event", "booking", "trip"
    ]
    filtered = [
        link for link in links if any(kw in link.lower() for kw in travel_keywords)
    ]
    return filtered

def parse_sitemap_xml(sitemap_url: str) -> List[str]:
    try:
        resp = requests.get(sitemap_url, timeout=10)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content, "xml")
            return [loc.text for loc in soup.find_all("loc")]
    except Exception:
        pass
    return []

def is_same_domain(url1: str, url2: str) -> bool:
    return urlparse(url1).netloc == urlparse(url2).netloc

def depth_limited_crawl(start_url: str, html: str, max_depth: int = 2, domain_rule: Optional[str] = None) -> Set[str]:
    visited = set([start_url])
    to_visit = [(start_url, html, 0)]
    all_links = set()
    while to_visit:
        url, html_content, depth = to_visit.pop(0)
        if depth >= max_depth:
            continue
        links = extract_links(html_content, url)
        for link in links:
            if link not in visited and (not domain_rule or domain_rule in link):
                try:
                    resp = requests.get(link, timeout=5)
                    if resp.status_code == 200:
                        to_visit.append((link, resp.text, depth + 1))
                        all_links.add(link)
                        visited.add(link)
                except Exception:
                    continue
    return all_links 