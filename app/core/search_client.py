import os
import httpx
import asyncio
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GOOGLE_SEARCH_ENGINE_ID = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
MAX_CONCURRENT_REQUESTS = int(os.getenv('MAX_CONCURRENT_REQUESTS', 5))
CRAWL_DELAY_SECONDS = float(os.getenv('CRAWL_DELAY_SECONDS', 1))

GOOGLE_SEARCH_URL = "https://www.googleapis.com/customsearch/v1"

class GoogleSearchClient:
    def __init__(self, api_key: Optional[str] = None, search_engine_id: Optional[str] = None):
        self.api_key = api_key or GOOGLE_API_KEY
        self.search_engine_id = search_engine_id or GOOGLE_SEARCH_ENGINE_ID
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    async def search(self, query: str, num: int = 10, start: int = 1, **kwargs) -> Dict[str, Any]:
        params = {
            "key": self.api_key,
            "cx": self.search_engine_id,
            "q": query,
            "num": num,
            "start": start,
        }
        params.update(kwargs)
        async with self.semaphore:
            async with httpx.AsyncClient(timeout=15) as client:
                try:
                    response = await client.get(GOOGLE_SEARCH_URL, params=params)
                    response.raise_for_status()
                    data = response.json()
                    # Optionally store raw response for debugging
                    self._store_raw_response(query, data)
                    return data
                except httpx.HTTPStatusError as e:
                    print(f"HTTP error: {e.response.status_code} - {e.response.text}")
                    return {"error": str(e)}
                except Exception as e:
                    print(f"Request failed: {e}")
                    return {"error": str(e)}

    def _store_raw_response(self, query: str, data: Dict[str, Any]):
        # Store raw API response for debugging (optional, can be improved)
        os.makedirs("app/db/raw_search_responses", exist_ok=True)
        safe_query = query.replace("/", "_").replace(" ", "_")[:50]
        filename = f"app/db/raw_search_responses/{safe_query}.json"
        try:
            import json
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Failed to store raw response: {e}")

    async def paginated_search(self, query: str, max_results: int = 30) -> List[Dict[str, Any]]:
        results = []
        start = 1
        while len(results) < max_results:
            remaining = max_results - len(results)
            num = min(10, remaining)
            data = await self.search(query, num=num, start=start)
            if "items" in data:
                results.extend(data["items"])
                if len(data["items"]) < num:
                    break  # No more results
            else:
                break  # Error or no items
            start += num
            await asyncio.sleep(CRAWL_DELAY_SECONDS)
        return results 