import requests
from bs4 import BeautifulSoup
from .base_search import BaseSearchProvider, SearchResult
from backend.pipeline.logger_setup import logger

class DuckDuckGoSearch(BaseSearchProvider):
    name = "duckduckgo"
    
    def search(self, query: str, max_results: int = 10):
        try:
            res = requests.post(
                'https://html.duckduckgo.com/html/', 
                data={'q': query}, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'},
                timeout=15
            )
            if res.status_code != 200:
                logger.warning(f"DuckDuckGo HTML search failed with status {res.status_code}")
                return []
                
            soup = BeautifulSoup(res.text, 'html.parser')
            results = []
            
            for a in soup.select('.result__a'):
                href = a.get('href')
                if href and href.startswith('//duckduckgo.com/l/?'):
                    # Sometimes DDG routes through redirect, sometimes direct.
                    import urllib.parse
                    parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                    if 'uddg' in parsed:
                        href = parsed['uddg'][0]
                elif href and href.startswith('/'):
                    continue # Internal link
                
                title = a.get_text(strip=True)
                
                if href:
                    results.append(SearchResult(href, title, "", self.name))
                    if len(results) >= max_results:
                        break
                        
            return results
        except Exception as e:
            logger.warning(f"DuckDuckGo search failed: {e}")
            return []
