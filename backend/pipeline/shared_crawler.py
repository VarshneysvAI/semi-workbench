import asyncio
from crawl4ai import AsyncWebCrawler

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
            _crawler_instance = AsyncWebCrawler(verbose=False)
            await _crawler_instance.start()
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

