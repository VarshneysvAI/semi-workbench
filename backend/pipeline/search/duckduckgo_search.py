from duckduckgo_search import DDGS
from .base_search import BaseSearchProvider, SearchResult
import time

class DuckDuckGoSearch(BaseSearchProvider):
    name = "duckduckgo"
    def search(self, query: str, max_results: int = 10):
        try:
            time.sleep(2) # Rate limit protection
            results = DDGS().text(query, max_results=max_results)
            return [SearchResult(r["href"], r["title"], r["body"], self.name) for r in results]
        except Exception:
            return []
