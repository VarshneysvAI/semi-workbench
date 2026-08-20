import requests
import logging

logger = logging.getLogger(__name__)

def extract_source_text(source) -> str:
    if not source or not source.url:
        return ""
    try:
        logger.info(f"Extracting text via Jina Reader for {source.url}")
        r = requests.get(f"https://r.jina.ai/{source.url}", timeout=30)
        r.raise_for_status()
        text = r.text
        # Limit to 80,000 chars to avoid blowing up the context window
        return text[:80000]
    except Exception as e:
        logger.error(f"Failed to extract text: {e}")
        return ""
