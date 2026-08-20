import os
import requests
from .base_search import BaseSearchProvider, SearchResult
from backend.pipeline.logger_setup import logger

class TavilySearch(BaseSearchProvider):
    name = "tavily"
    
    def search(self, query: str, max_results: int = 10):
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            logger.warning("TAVILY_API_KEY not found in environment.")
            return []
            
        try:
            url = "https://api.tavily.com/search"
            payload = {
                "api_key": api_key,
                "query": query,
                "search_depth": "basic",
                "max_results": max_results
            }
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                results = []
                for r in data.get("results", []):
                    href = r.get("url", "")
                    title = r.get("title", "")
                    body = r.get("content", "")
                    if href:
                        results.append(SearchResult(href, title, body, self.name))
                return results
            else:
                logger.warning(f"Tavily search failed with status {response.status_code}: {response.text}")
                return []
        except Exception as e:
            logger.warning(f"Tavily search failed: {e}")
            return []
