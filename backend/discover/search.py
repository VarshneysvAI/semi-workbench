"""Stage 1 — autonomous manufacturer source discovery (hybrid, priority-ordered).

Per directive the discovery stage is a backend chain, strictly in priority:
    1. agent-reach (CLI, when installed)
    2. Firecrawl /search (FIRECRAWL_API_KEY)
    3. Exa search (EXA_API_KEY)
    4. ddgs (DuckDuckGo, no key) — the always-on last resort

Each backend returns [] on failure and the chain moves on; SEMI never invents
results. ``rank_candidates`` applies SourceValidator + authority ranking.

Authority ranking:
    1.0  spec sheet PDF       0.9  manual PDF
    0.7  structured page      0.6  unstructured page
    0.5  manufacturer video   0.3  third-party (only if primary missing)
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx

from backend.discover.agent_reach_agent import AgentReachAgent
from backend.ingest.source_validator import validate_source_url

logger = logging.getLogger(__name__)

_AGENT = AgentReachAgent()

CONTENT_TYPE_BY_KIND: dict[str, str] = {
    "spec_sheet": "pdf",
    "manual": "pdf",
    "product_page": "web",
    "video": "web",
    "image": "image",
}

AUTHORITY_BY_KIND: dict[str, float] = {
    "spec_sheet": 1.0,
    "manual": 0.9,
    "product_page": 0.7,
    "video": 0.5,
}

_search_backend_used = "none"


@dataclass(slots=True)
class SourceCandidate:
    url: str
    title: str = ""
    kind: str = "product_page"
    source: str = "web"

    @property
    def content_type(self) -> str:
        return CONTENT_TYPE_BY_KIND.get(self.kind, "web")

    @property
    def authority(self) -> float:
        return AUTHORITY_BY_KIND.get(self.kind, 0.5)


def _classify_kind(url: str, title: str = "") -> str:
    parsed = urlparse(url)
    path = parsed.path.lower()
    title = (title or "").lower()
    if path.endswith((".pdf", ".spec", ".doc", ".docx")):
        if "manual" in path or "manual" in title or "install" in title or "guide" in title:
            return "manual"
        return "spec_sheet"
    if "youtube" in parsed.netloc or "vimeo" in parsed.netloc or path.endswith(".mp4"):
        return "video"
    if path.endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")):
        return "image"
    return "product_page"


def rank_candidates(urls: list[str], titles: list[str] | None = None) -> list[SourceCandidate]:
    """Deduplicate, validate and rank raw URLs into SourceCandidates."""
    titles = titles or [""] * len(urls)
    seen: set[str] = set()
    ranked: list[SourceCandidate] = []
    for url, title in zip(urls, titles):
        host = urlparse(url if "//" in url else f"https://{url}").netloc.lower()
        if host in seen:
            continue
        seen.add(host)
        accepted, reason = validate_source_url(url)
        if not accepted:
            logger.info("Rejected source %s: %s", url, reason)
            continue
        kind = _classify_kind(url, title)
        ranked.append(SourceCandidate(url=url, title=title, kind=kind))
    ranked.sort(key=lambda c: c.authority, reverse=True)
    logger.info("Ranked %d valid candidates", len(ranked))
    return ranked


def build_search_queries(manufacturer: str, part_number: str) -> list[str]:
    """Deterministic queries for the discovery stage, ordered spec-first."""
    domain = _guess_domain(manufacturer)
    spec = f'site:{domain} "{part_number}" spec'
    manual = f'"{part_number}" "{manufacturer.lower()}" manual'
    return [spec, f'"{part_number}" {manufacturer.lower()} spec sheet pdf',
            f'site:{domain} "{part_number}"', manual]


def _guess_domain(manufacturer: str) -> str:
    """Best-effort manufacturer site domain; overridable per brand."""
    override = {
        "nibco": "nibco.com",
        "watts": "watts.com",
        "apollo": "apollovalves.com",
        "trane": "trane.com",
        "schneider": "se.com",
        "honeywell": "honeywell.com",
        "samsung": "samsung.com",
    }
    key = manufacturer.strip().lower()
    if key in override:
        return override[key]
    compact = "".join(ch for ch in key if ch.isalnum())
    return f"{compact}.com" if compact else ""


def search_web(query: str, max_results: int = 8) -> list[tuple[str, str]]:
    """Hybrid discovery: agent-reach -> Firecrawl -> Exa -> ddgs (priority)."""
    global _search_backend_used
    for name, backend in (
        ("agent-reach", lambda: _agent_reach_search(query, max_results)),
        ("firecrawl", lambda: _firecrawl_search(query, max_results)),
        ("exa", lambda: _exa_search(query, max_results)),
        ("ddgs", lambda: _ddgs_search(query, max_results)),
    ):
        hits = backend()
        if hits:
            _search_backend_used = name
            logger.info("Discovery search served by %s (%d hits)", name, len(hits))
            return hits
    _search_backend_used = "none"
    return []


def last_search_backend() -> str:
    """Provenance: which backend produced the current hits (for the audit trail)."""
    return _search_backend_used


def _agent_reach_search(query: str, max_results: int) -> list[tuple[str, str]]:
    if os.environ.get("AGENTREACH_ENABLED", "true").strip().lower() == "false":
        return []
    return _AGENT.search_web(query, max_results)


def _firecrawl_search(query: str, max_results: int) -> list[tuple[str, str]]:
    key = os.environ.get("FIRECRAWL_API_KEY", "")
    if not key:
        return []
    base = os.environ.get("FIRECRAWL_BASE_URL", "https://api.firecrawl.dev/v2").rstrip("/")
    body = {
        "query": query,
        "limit": max_results,
        "sources": [{"type": "web"}],
        "categories": [{"type": "pdf"}],
    }
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    try:
        r = httpx.post(f"{base}/search", json=body, headers=headers, timeout=35.0)
        if r.status_code >= 400:
            logger.info("firecrawl search %s: %s", r.status_code, r.text[:120])
            return []
        hits = [(u.get("url", ""), u.get("title", ""))
                for u in r.json().get("data", {}).get("web", [])
                if u.get("url")]
        return [hit for hit in hits if hit[0]][:max_results]
    except Exception as exc:
        logger.info("firecrawl search failed: %s", exc)
        return []


def _exa_search(query: str, max_results: int) -> list[tuple[str, str]]:
    key = os.environ.get("EXA_API_KEY", "")
    if not key:
        return []
    body = {"query": query, "numResults": max_results}
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    try:
        r = httpx.post("https://api.exa.ai/search", json=body, headers=headers, timeout=35.0)
        if r.status_code >= 400:
            logger.info("exa search %s: %s", r.status_code, r.text[:120])
            return []
        hits = [(x.get("url", ""), x.get("title", ""))
                for x in r.json().get("results", [])
                if x.get("url")]
        return hits[:max_results]
    except Exception as exc:
        logger.info("exa search failed: %s", exc)
        return []


def _ddgs_search(query: str, max_results: int) -> list[tuple[str, str]]:
    """DuckDuckGo via ddgs (no key) — the unconditional last resort."""
    ddgs_cls = None
    try:
        from ddgs import DDGS as _D
        ddgs_cls = _D
    except ImportError:
        try:
            from duckduckgo_search import DDGS as _D
            ddgs_cls = _D
        except ImportError:
            ddgs_cls = None
    if ddgs_cls is None:
        logger.warning("No ddgs backend installed — last-resort search unavailable")
        return []

    hits: list[tuple[str, str]] = []
    try:
        with ddgs_cls() as ddgs:
            for result in ddgs.text(query, max_results=max_results, region="wt-wt"):
                url = (result.get("href") or result.get("url") or "").strip()
                title = (result.get("title") or "").strip()
                if url:
                    hits.append((url, title))
    except Exception as exc:
        logger.warning("Web search failed for %r: %s", query, exc)
        return []
    return hits


def _run_search(query: str, max_results: int = 8) -> list[tuple[str, str]]:
    return search_web(query, max_results=max_results)