import logging
from backend.discover.search import build_search_queries, search_web, rank_candidates

logger = logging.getLogger(__name__)

class Sources:
    def __init__(self):
        self.mfr_url = ""
        self.ref_urls = []
        self.selected_source = None
        self.candidate_sources = []

def discover_sources(row: dict, manufacturer: str) -> Sources:
    sources = Sources()
    part_num = row.get("Mfg_Part_Num", "")
    if not part_num or not manufacturer:
        return sources
        
    queries = build_search_queries(manufacturer, part_num)
    all_hits = []
    for q in queries[:2]:
        hits = search_web(q, max_results=3)
        all_hits.extend(hits)
        
    if not all_hits:
        return sources
        
    urls = [h[0] for h in all_hits]
    titles = [h[1] for h in all_hits]
    ranked = rank_candidates(urls, titles)
    
    if ranked:
        sources.selected_source = ranked[0]
        sources.candidate_sources = ranked
        sources.mfr_url = ranked[0].url if ranked[0].authority > 0.5 else ""
        sources.ref_urls = [r.url for r in ranked[1:6]]
        
    return sources
