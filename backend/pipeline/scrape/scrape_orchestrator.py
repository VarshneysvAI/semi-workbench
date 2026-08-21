import requests
import tempfile
from bs4 import BeautifulSoup
from backend.pipeline.logger_setup import logger

try:
    import pypdf
except ImportError:
    pypdf = None

from backend.pipeline.shared_crawler import get_crawler

async def scrape_url(url):
    logger.info(f"SCRAPE_START: {url}")
    if url.lower().endswith(".pdf") or "pdf" in url.lower():
        text, method = await scrape_pdf(url)
        if text: return text, method
        
    return await scrape_html(url)

async def scrape_pdf(url):
    if pypdf is None:
        logger.warning("pypdf module not installed, falling back to HTML scraper")
        return await scrape_html(url)
    try:
        res = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        if res.status_code == 200:
            with tempfile.NamedTemporaryFile(delete=False) as f:
                f.write(res.content)
                f.flush()
                reader = pypdf.PdfReader(f.name)
                text_pages = []
                for i, page in enumerate(reader.pages):
                    if i >= 5: # Limit to first 5 pages for extreme speed
                        break
                    text_pages.append(page.extract_text())
                text = " ".join(text_pages)
            logger.info("PDF_PARSED (first 5 pages)")
            return clean_text(text[:30000]), "pdf_local"
    except Exception as e:
        logger.warning(f"Local PDF parse failed: {e}")
        
    return None, "none"


async def scrape_html(url):
    # 1. Try Crawl4AI primary
    try:
        crawler = await get_crawler()
        result = await crawler.arun(url=url, word_count_threshold=10, bypass_cache=True)
        markdown_text = result.markdown
            
        if markdown_text:
            if len(markdown_text.strip()) < 500:
                logger.warning(f"Blocked by anti-bot protection: Near-empty content ({len(markdown_text)} bytes) from crawl4ai")
                return await scrape_jina(url)
            logger.info("HTML_PARSED: crawl4ai")
            return clean_text(markdown_text[:100000]), "crawl4ai"
    except Exception as e:
        logger.warning(f"Crawl4AI failed or not installed: {e}")

    # 2. Try curl_cffi fallback
    try:
        from curl_cffi import requests as cffi_requests
        res = cffi_requests.get(url, impersonate="chrome110", timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")
        text = soup.get_text(separator=" ", strip=True)
        if len(text) < 500:
            logger.warning(f"Blocked by anti-bot protection: Near-empty content ({len(text)} bytes) from curl_cffi")
            return await scrape_jina(url)
        logger.info("HTML_PARSED: curl_cffi")
        return clean_text(text[:100000]), "curl_cffi"
    except Exception as e:
        logger.warning(f"curl_cffi failed: {e}")
        return await scrape_jina(url)

async def scrape_jina(url):
    try:
        res = requests.get(f"https://r.jina.ai/{url}", timeout=15)
        logger.info("HTML_PARSED: jina")
        return clean_text(res.text[:100000]), "jina"
    except Exception as e:
        logger.warning(f"Jina failed: {e}")
        logger.info("SCRAPE_FAILED")
        return "", "none"

def clean_text(text):
    import re
    text = re.sub(r'\s+', ' ', text)
    return text.strip()
