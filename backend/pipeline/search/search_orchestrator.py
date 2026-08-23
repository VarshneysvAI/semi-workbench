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
        
        async def fetch_provider(provider):
            try:
                if inspect.iscoroutinefunction(provider.search):
                    return await provider.search(query, max_results), provider.name
                else:
                    return await asyncio.to_thread(provider.search, query, max_results), provider.name
            except Exception as e:
                logger.warning(f"Search provider {provider.name} failed: {e}")
                return [], provider.name

        # 1. Run free/primary engines concurrently (SearxNG + DuckDuckGo)
        primary_providers = [p for p in self.providers if p.name in ('searxng', 'duckduckgo')]
        completed = await asyncio.gather(*(fetch_provider(p) for p in primary_providers))
        
        all_results = []
        used_providers = []
        for results, prov_name in completed:
            if results:
                all_results.extend(results)
                used_providers.append(prov_name)
                
        # 2. If primary fails, fallback to Tavily etc sequentially
        if not all_results:
            fallback_providers = [p for p in self.providers if p.name not in ('searxng', 'duckduckgo')]
            for provider in fallback_providers:
                results, prov_name = await fetch_provider(provider)
                if results:
                    all_results.extend(results)
                    used_providers.append(prov_name)
                    break
                    
        if all_results:
            prov_str = "+".join(used_providers)
            
            # Deduplicate by URL
            seen_urls = set()
            unique_results = []
            for r in all_results:
                if r.url not in seen_urls:
                    seen_urls.add(r.url)
                    unique_results.append(r)
                    
            logger.info(f"SEARCH_PROVIDER_USED: {prov_str} (aggregated {len(unique_results)} unique results)")
            return unique_results, prov_str
            
        logger.error("SEARCH_FAILED: All search providers failed")
        return [], "none"

search_orchestrator = SearchOrchestrator()

