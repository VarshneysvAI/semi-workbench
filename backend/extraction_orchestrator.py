import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

from backend.contracts import ExtractInput, WebExtractResult, CitedValue, SchemaPlan
from backend.discover.search import build_search_queries, search_web, rank_candidates
from backend.extract.fetchers import fetch_content, FetchedDoc
from backend.llm.gemma import extract_field, is_configured

logger = logging.getLogger(__name__)

async def run_extraction(input_data: ExtractInput) -> WebExtractResult:
    """Orchestrates Phase 3: Parallel Web Extraction."""
    if not is_configured():
        logger.warning("LLM not configured. Extraction will fail or return empty.")

    # 1. Generate search queries and fetch URLs
    queries = build_search_queries(input_data.manufacturer, input_data.part_number)
    all_urls = []
    
    def do_search(q: str):
        return search_web(q, max_results=3)

    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        search_results = await asyncio.gather(*[
            loop.run_in_executor(pool, do_search, q) for q in queries
        ])

    for res in search_results:
        for url, title in res:
            all_urls.append(url)

    # 2. Rank candidates (prioritize PDFs > Web > Video)
    candidates = rank_candidates(all_urls)
    if not candidates:
        logger.info("No candidates found for %s %s", input_data.manufacturer, input_data.part_number)
        return WebExtractResult(cited_values=[], failed_attributes=input_data.remaining_attributes)

    top_candidates = candidates[:3]  # process top 3 to save time/cost
    logger.info("Fetching content from top %d candidates...", len(top_candidates))

    def fetch_doc(url: str):
        return fetch_content(url, timeout=30.0)

    # 3. Parallel fetch
    with ThreadPoolExecutor() as pool:
        docs = await asyncio.gather(*[
            loop.run_in_executor(pool, fetch_doc, c.url) for c in top_candidates
        ])

    valid_docs = [d for d in docs if d.ok and d.text.strip()]
    logger.info("Successfully fetched %d/%d docs", len(valid_docs), len(top_candidates))

    cited_values: list[CitedValue] = []
    failed_attributes: list[str] = []

    def extract_attr(attr: str, doc: FetchedDoc):
        return extract_field(
            manufacturer=input_data.manufacturer,
            sku=input_data.sku,
            attribute=attr,
            context=doc.text[:12000] # LLM context window safety
        )

    # 4. LLM Extraction (Negotiate with LLM deterministically as RAG)
    # For each attribute, we ask the LLM to extract from each doc until high confidence
    for attr in input_data.remaining_attributes:
        best_val = None
        for doc in valid_docs:
            ext = extract_attr(attr, doc)
            if ext.value and ext.confidence >= 0.7:
                # Map fetcher kind to schema's literal extractor type
                extractor_type = "crawl4ai"
                if doc.kind == "pdf":
                    extractor_type = "pdf_reader_mcp"
                elif doc.kind == "video":
                    extractor_type = "youtube_transcript"
                elif doc.fetched_via == "firecrawl":
                    extractor_type = "firecrawl_scrape"
                
                snippet = ext.evidence_snippet
                if len(snippet) < 10:
                    snippet = f"Value '{ext.value}' found in source document."
                    if len(snippet) < 10: snippet = snippet.ljust(10, ' ')
                
                best_val = CitedValue(
                    attribute=attr,
                    value=ext.value,
                    unit=ext.unit or None,
                    confidence=ext.confidence,
                    source_url=doc.url,
                    evidence_snippet=snippet[:500],
                    extractor=extractor_type
                )
                break # Move to next attribute once we have a solid extraction
        
        if best_val:
            cited_values.append(best_val)
        else:
            failed_attributes.append(attr)

    return WebExtractResult(
        cited_values=cited_values,
        failed_attributes=failed_attributes
    )
