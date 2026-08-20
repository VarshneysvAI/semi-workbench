from .base_search import BaseSearchProvider, SearchResult
from backend.pipeline.logger_setup import logger
import urllib.parse
from backend.pipeline.shared_crawler import get_crawler

class Crawl4AISearch(BaseSearchProvider):
    name = "crawl4ai_search"
    
    async def search(self, query: str, max_results: int = 10):
        try:
            # Use Yahoo Search as it has highly relaxed bot protections compared to Google
            url = f"https://search.yahoo.com/search?p={urllib.parse.quote(query)}"
            
            crawler = await get_crawler()
            result = await crawler.arun(url=url, bypass_cache=True)
            links_dict = result.links if hasattr(result, 'links') else {}
            
            results = []
            internal_domains = ["yahoo.com", "bing.com", "flickr.com", "duckduckgo.com"]
            
            # Crawl4AI categorizes links into 'internal' and 'external'
            for link in links_dict.get("external", []):
                href = link.get("href", "")
                text = link.get("text", "").strip()
                if href and text and not any(d in href for d in internal_domains):
                    results.append(SearchResult(href, text, "", self.name))
                    if len(results) >= max_results: 
                        break
                        
            return results
        except Exception as e:
            logger.warning(f"Crawl4AISearch failed: {e}")
            return []
