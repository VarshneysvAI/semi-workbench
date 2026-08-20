import asyncio
import inspect
from .searxng_search import SearxngSearch
from .duckduckgo_provider import DuckDuckGoSearch
from .tavily_provider import TavilySearch
from .crawl4ai_search import Crawl4AISearch
from backend.pipeline.logger_setup import logger

class SearchOrchestrator:
    def __init__(self):
        self.providers = [
            SearxngSearch(),
            DuckDuckGoSearch(),
            TavilySearch(),
            Crawl4AISearch(),
        ]

    async def search(self, query: str, max_results: int = 10):
        logger.info(f"SEARCH_START: {query}")
        for provider in self.providers:
            try:
                if inspect.iscoroutinefunction(provider.search):
                    results = await provider.search(query, max_results)
                else:
                    results = await asyncio.to_thread(provider.search, query, max_results)

                if results:
                    logger.info(f"SEARCH_PROVIDER_USED: {provider.name}")
                    return results, provider.name
            except Exception as e:
                logger.warning(f"Search provider {provider.name} failed: {e}")
        
        logger.error("SEARCH_FAILED: All search providers failed")
        return [], "none"

search_orchestrator = SearchOrchestrator()

