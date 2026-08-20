import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv("backend/.env")

PRIMARY_PROVIDER = os.getenv("PRIMARY_PROVIDER", "nim").lower()
FALLBACK_PROVIDERS = os.getenv("FALLBACK_PROVIDERS", "gemini").lower()

NIM_API_KEY = os.getenv("NIM_API_KEY") or os.getenv("LLM_API_KEY_NIM")
NIM_BASE_URL = os.getenv("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
NIM_MODEL = os.getenv("NIM_MODEL", "nvidia/nemotron-3.5-lightning-30b-a3b")
NIM_TIMEOUT = int(os.getenv("NIM_TIMEOUT", "120"))
NIM_MAX_RPM = int(os.getenv("NIM_MAX_RPM", "35"))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_TIMEOUT = int(os.getenv("GEMINI_TIMEOUT", "120"))
GEMINI_MAX_RPM = int(os.getenv("GEMINI_MAX_RPM", "10"))

MOCK_PROVIDER = os.getenv("MOCK_PROVIDER", "false").lower() == "true"

SEARCH_TIMEOUT = int(os.getenv("SEARCH_TIMEOUT", "20"))
SEARCH_MAX_RESULTS = int(os.getenv("SEARCH_MAX_RESULTS", "10"))

SEARXNG_BASE_URLS = os.getenv("SEARXNG_BASE_URLS", "https://searx.be,https://search.bus-hit.me,https://searx.tiekoetter.com")
EXA_API_KEY = os.getenv("EXA_API_KEY")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
ENABLE_DUCKDUCKGO_FALLBACK = os.getenv("ENABLE_DUCKDUCKGO_FALLBACK", "true").lower() == "true"

CONCURRENCY = int(os.getenv("CONCURRENCY", "3"))
MAX_ROWS_PER_RUN = int(os.getenv("MAX_ROWS_PER_RUN", "500"))
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"
CACHE_FILE = Path(os.getenv("CACHE_FILE", ".cache/semi_cache.json"))
STATE_FILE = Path(os.getenv("STATE_FILE", ".cache/semi_state.json"))
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "output"))
LOG_DIR = Path(os.getenv("LOG_DIR", "logs"))
JOBS_DIR = Path(os.getenv("JOBS_DIR", "jobs"))
