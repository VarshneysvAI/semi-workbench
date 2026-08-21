import urllib.parse
import requests
from bs4 import BeautifulSoup
from .base_search import BaseSearchProvider, SearchResult
from backend.pipeline.logger_setup import logger

try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None

try:
    from curl_cffi import requests as curl_requests
except ImportError:
    curl_requests = None


class DuckDuckGoSearch(BaseSearchProvider):
    name = "duckduckgo"
    
    def search(self, query: str, max_results: int = 10):
        # Strategy 1: DDGS Python package
        if DDGS is not None:
            try:
                results = list(DDGS().text(query, max_results=max_results))
                output = []
                for r in results:
                    href = r.get("href") or r.get("link")
                    title = r.get("title", "")
                    snippet = r.get("body", "") or r.get("snippet", "")
                    if href:
                        output.append(SearchResult(href, title, snippet, self.name))
                if output:
                    return output
            except Exception as e:
                logger.warning(f"DuckDuckGo DDGS search failed: {e}")

        # Strategy 2: curl_cffi Chrome TLS impersonation (bypasses datacenter blocks)
        if curl_requests is not None:
            try:
                res = curl_requests.get(
                    f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}",
                    impersonate="chrome120",
                    timeout=15
                )
                if res.status_code == 200:
                    soup = BeautifulSoup(res.text, 'html.parser')
                    results = []
                    for a in soup.select('.result__a'):
                        href = a.get('href', '')
                        if href and href.startswith('//duckduckgo.com/l/?'):
                            parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                            if 'uddg' in parsed:
                                href = parsed['uddg'][0]
                        elif href.startswith('/'):
                            continue
                        
                        title = a.get_text(strip=True)
                        if href:
                            results.append(SearchResult(href, title, "", self.name))
                            if len(results) >= max_results:
                                break
                    if results:
                        return results
            except Exception as e:
                logger.warning(f"curl_cffi DDG search failed: {e}")

        # Strategy 3: Standard requests fallback
        try:
            res = requests.post(
                'https://html.duckduckgo.com/html/', 
                data={'q': query}, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'},
                timeout=15
            )
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                results = []
                for a in soup.select('.result__a'):
                    href = a.get('href', '')
                    if href and href.startswith('//duckduckgo.com/l/?'):
                        parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                        if 'uddg' in parsed:
                            href = parsed['uddg'][0]
                    elif href.startswith('/'):
                        continue
                    
                    title = a.get_text(strip=True)
                    if href:
                        results.append(SearchResult(href, title, "", self.name))
                        if len(results) >= max_results:
                            break
                return results
        except Exception as e:
            logger.warning(f"Standard requests DDG search failed: {e}")

        return []

