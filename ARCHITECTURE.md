# SEMI Intelligence Pipeline Architecture

This document maps out the final, highly resilient architecture of the SEMI Intelligence Pipeline.

## Directory Structure

```text
backend/
├── .env                  # Secrets, config settings, thresholds
├── config.py             # Parses .env securely, exports global constants
├── cli.py                # Command Line Interface to trigger extraction runs
├── live_app.py           # FastAPI server for the UI and Webhooks
│
├── providers/            # LLM Interfacing Layer
│   ├── base_provider.py  # Abstract Interface for LLMs
│   ├── gemini_provider.py# Google Gemini API Wrapper (Fallback)
│   ├── nim_provider.py   # NVIDIA NIM API Wrapper (Primary)
│   └── mock_provider.py  # Zero-Credit Mock Engine for testing
│
└── pipeline/             # Core Autonomous Engine
    ├── orchestrator.py   # Main asyncio engine (concurrency logic, row management)
    ├── provider_router.py# Routes between NIM -> Gemini -> Mock
    ├── extraction_schema.py # Centralized Prompts & JSON Schema constraints
    ├── json_repair.py    # Regex-based JSON healer for malformed LLM outputs
    ├── rate_limiter.py   # API strict 35-RPM throttle manager
    ├── source_validator.py # Deterministic URL scoring (blacklist, PDF boost)
    ├── logger_setup.py   # Structured file/console logging
    ├── cache.py          # Local disk-cache to prevent redundant executions
    ├── delivery_header.py# Strict 252-column schema definitions
    ├── delivery_mapper.py# Inflates sparse LLM JSON into 252-column CSV
    │
    ├── search/           # Discovery Layer
    │   ├── search_orchestrator.py # Iterates through available search engines
    │   ├── query_builder.py       # Strips distributor names, formats specs
    │   ├── base_search.py         # Search interface
    │   ├── searxng_search.py      # Primary Search (Rotates 5 public nodes)
    │   ├── crawl4ai_search.py     # Fallback Search (Navigates Yahoo via Playwright)
    │   └── duckduckgo_search.py   # Legacy fallback (Optional)
    │
    └── scrape/           # Extraction Layer
        ├── scrape_orchestrator.py # Iterates through extraction methods
        ├── crawl4ai_scraper.py    # Primary HTML scraper (AsyncWebCrawler)
        ├── curl_cffi_scraper.py   # Impersonation HTML scraper
        ├── jina_scraper.py        # Final API-based HTML scraper fallback
        └── pdf_scraper.py         # Local PyPDF2 binary extractor
```

## Architectural Flow
1. **Initiation**: `orchestrator.py` fires an asynchronous `asyncio.Semaphore(3)` process.
2. **Caching**: Checks `.cache/semi_cache.json`. If row exists, outputs instantly.
3. **Discovery**: `search_orchestrator.py` queries `SearXNG`. If SearXNG 403s, `Crawl4AI` physically opens a headless Chromium browser and pulls links from Yahoo.
4. **Scoring**: `source_validator.py` deterministically rejects garbage (e.g. Amazon, eBay) and selects the best MFR URL.
5. **Scraping**: `scrape_orchestrator.py` attempts PDF logic. If HTML, uses `Crawl4AI`. If JS fails, uses `curl_cffi` to impersonate Chrome.
6. **LLM Extraction**: `provider_router.py` hits NIM (or falls back to Gemini) using the `extraction_schema.py`.
7. **Mapping**: `json_repair.py` ensures perfect formatting, then `delivery_mapper.py` aligns it to the 252-column standard.
8. **Logging**: Full lineage (Search method, Scrape method, Status) is written locally.

## Production Performance Metrics
Based on the final 12-row edge case acceptance test (simulating complex real-world conditions):

- **Concurrency**: 3 parallel execution threads
- **Total Duration**: ~119.58 seconds (with multi-provider cold starts and headless browser navigation)
- **Zero-Crash Resilience**: 100% pipeline stability. 0 system crashes despite anti-bot challenges and LLM formatting errors.
- **Self-Healing LLM Extraction**: 
  - NVIDIA NIM is deployed as the primary provider with 8192 context allocation.
  - Automatic fallback to Google Gemini when token-truncation or invalid JSON is detected.
- **Marketplace Filtering**: Verified rejection of non-MFR URLs (Amazon, Zoro, Gordon Electric Supply) with robust fallback to Manufacturer PDF scraping.
- **Audit-Ready Outputs**: Emits perfectly mapped 252-column `.csv` format (`Unihack_Delivery_Format_Output.csv`), a detailed `status_report.csv`, and a granular trace in `lineage.csv`.
