import requests
import random
from .base_search import BaseSearchProvider, SearchResult
from backend.config import SEARXNG_BASE_URLS, SEARCH_TIMEOUT
from backend.pipeline.logger_setup import logger

class SearxngSearch(BaseSearchProvider):
    name = "searxng"
    
    def search(self, query: str, max_results: int = 10):
        # Expanded list of public SearXNG instances that are more reliable
        urls = [
            "https://searx.be",
            "https://search.bus-hit.me",
            "https://searx.tiekoetter.com",
            "https://searx.foss.tw",
            "https://searx.work"
        ]
        
        # Override with env config if user provides it, otherwise use our robust list
        if SEARXNG_BASE_URLS and SEARXNG_BASE_URLS != "https://searx.be,https://search.bus-hit.me,https://searx.tiekoetter.com":
            urls = [u.strip() for u in SEARXNG_BASE_URLS.split(",")]
            
        random.shuffle(urls) # Rotate to prevent hitting the same one
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        
        for url in urls:
            try:
                res = requests.get(
                    f"{url.strip()}/search?q={query}&format=json", 
                    timeout=SEARCH_TIMEOUT,
                    headers=headers
                )
                if res.status_code == 200:
                    data = res.json()
                    results = [SearchResult(r["url"], r.get("title", ""), r.get("content", ""), self.name) for r in data.get("results", [])[:max_results]]
                    if results:
                        return results
                elif res.status_code == 429:
                    logger.debug(f"SearXNG Rate limited on {url}")
            except Exception as e:
                logger.debug(f"SearXNG failed on {url}: {e}")
                continue
        return []
