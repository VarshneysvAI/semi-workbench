from .base_search import BaseSearchProvider, SearchResult
from backend.pipeline.logger_setup import logger
from duckduckgo_search import DDGS

class DuckDuckGoSearch(BaseSearchProvider):
    name = "duckduckgo"
    
    def search(self, query: str, max_results: int = 10):
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
