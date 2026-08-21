from .base_search import BaseSearchProvider, SearchResult
from backend.pipeline.logger_setup import logger

try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None

class DuckDuckGoSearch(BaseSearchProvider):
    name = "duckduckgo"
    
    def search(self, query: str, max_results: int = 10):
        if DDGS is None:
            logger.warning("duckduckgo_search module not installed, skipping DuckDuckGo provider")
            return []
        try:
            results = []
            with DDGS() as ddgs:
                ddg_results = ddgs.text(query, max_results=max_results)
                if not ddg_results:
                    return []
                for r in ddg_results:
                    href = r.get("href", "")
                    title = r.get("title", "")
                    body = r.get("body", "")
                    if href:
                        results.append(SearchResult(href, title, body, self.name))
            return results
        except Exception as e:
            logger.warning(f"DuckDuckGo search failed: {e}")
            return []

