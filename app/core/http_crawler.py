import httpx
import asyncio
import random
from typing import List, Dict, Any, Optional
from fake_useragent import UserAgent

DEFAULT_TIMEOUT = 10
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    # Add more or use fake_useragent
]

CONTENT_TYPES = [
    "text/html", "application/xhtml+xml", "application/xml"
]

class SimpleHttpCrawler:
    def __init__(self, timeout: int = DEFAULT_TIMEOUT):
        self.timeout = timeout
        try:
            self.ua = UserAgent()
        except Exception:
            self.ua = None

    def get_random_user_agent(self) -> str:
        if self.ua:
            try:
                return self.ua.random
            except Exception:
                pass
        return random.choice(USER_AGENTS)

    async def fetch(self, url: str) -> Optional[Dict[str, Any]]:
        headers = {
            "User-Agent": self.get_random_user_agent(),
            "Accept": ", ".join(CONTENT_TYPES),
        }
        async with httpx.AsyncClient(follow_redirects=True, timeout=self.timeout) as client:
            try:
                response = await client.get(url, headers=headers)
                content_type = response.headers.get("content-type", "")
                if not any(ct in content_type for ct in CONTENT_TYPES):
                    return None  # Skip non-HTML content
                canonical_url = self.extract_canonical_url(response.text) or str(response.url)
                return {
                    "url": url,
                    "final_url": str(response.url),
                    "canonical_url": canonical_url,
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "content_type": content_type,
                    "content_length": len(response.content),
                    "html": response.text,
                }
            except httpx.TimeoutException:
                print(f"Timeout fetching {url}")
                return None
            except httpx.HTTPStatusError as e:
                print(f"HTTP error {e.response.status_code} for {url}")
                return None
            except Exception as e:
                print(f"Failed to fetch {url}: {e}")
                return None

    def extract_canonical_url(self, html: str) -> Optional[str]:
        import re
        match = re.search(r'<link rel=["\']canonical["\'] href=["\']([^"\']+)["\']', html, re.IGNORECASE)
        if match:
            return match.group(1)
        return None

    async def crawl(self, urls: List[str]) -> List[Dict[str, Any]]:
        results = []
        tasks = [self.fetch(url) for url in urls]
        for coro in asyncio.as_completed(tasks):
            result = await coro
            if result:
                results.append(result)
        return results 