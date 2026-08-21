import asyncio
from backend.pipeline.logger_setup import logger

try:
    from crawl4ai import AsyncWebCrawler
except ImportError:
    AsyncWebCrawler = None

class SimpleHttpxCrawlerResult:
    def __init__(self, html: str, markdown: str = ""):
        self.html = html
        self.markdown = markdown
        self.cleaned_html = html
        self.media = {}
        self.links = {"internal": [], "external": []}

class SimpleHttpxCrawler:
    async def start(self):
        pass

    async def arun(self, url: str, **kwargs):
        import httpx
        from bs4 import BeautifulSoup
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            res = await client.get(url, headers=headers)
            html = res.text
            soup = BeautifulSoup(html, "html.parser")
            links = []
            for a in soup.find_all("a", href=True):
                href = a["href"]
                text = a.get_text(strip=True)
                if href and href.startswith("http"):
                    links.append({"href": href, "text": text})
            result = SimpleHttpxCrawlerResult(html, soup.get_text(separator="\n"))
            result.links = {"external": links, "internal": []}
            return result

    async def close(self):
        pass

_crawler_instance = None
_crawler_locks = {}

async def get_crawler():
    global _crawler_instance
    loop = asyncio.get_running_loop()
    loop_id = id(loop)
    
    if loop_id not in _crawler_locks:
        _crawler_locks[loop_id] = asyncio.Lock()
        
    async with _crawler_locks[loop_id]:
        if _crawler_instance is None:
            if AsyncWebCrawler is not None:
                try:
                    _crawler_instance = AsyncWebCrawler(verbose=False)
                    await _crawler_instance.start()
                    logger.info("Crawl4AI AsyncWebCrawler initialized successfully.")
                except Exception as e:
                    logger.warning(f"Crawl4AI AsyncWebCrawler start failed ({e}), using HTTPX fallback.")
                    _crawler_instance = SimpleHttpxCrawler()
            else:
                logger.info("Crawl4AI not installed, using HTTPX/BeautifulSoup crawler fallback.")
                _crawler_instance = SimpleHttpxCrawler()
    return _crawler_instance

async def close_crawler():
    global _crawler_instance
    global _crawler_locks
    if _crawler_instance is not None:
        try:
            await _crawler_instance.close()
        except Exception:
            pass
        _crawler_instance = None
    _crawler_locks.clear()
