"""Stage 1 skeleton — autonomous manufacturer source discovery.

DAY 1/4 fills the Playwright + targeted-search implementation. Today we
ship the ranking vocabulary, query builder and the validated result type
so the pipeline (excel -> discover -> state_graph) has a stable contract.

Authority ranking (plan):
    1.0  spec sheet PDF       0.9  manual PDF
    0.7  structured page      0.6  unstructured page
    0.5  manufacturer video   0.3  third-party (only if primary missing)

Every returned candidate has passed SourceValidator (no marketplaces).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from urllib.parse import urlparse

from backend.ingest.source_validator import validate_source_url

logger = logging.getLogger(__name__)

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


def _run_search(query: str, max_results: int = 8) -> list[tuple[str, str]]:
    """Wrapper around duckduckgo-search; safe no-network fallback to []."""
    return search_web(query, max_results=max_results)


def search_web(query: str, max_results: int = 8) -> list[tuple[str, str]]:
    """Live, non-static web search via DuckDuckGo (free, no key).

    Priority: ``ddgs`` (current package) -> ``duckduckgo_search`` (legacy).
    Returns ``[(url, title)]``. Degrades to ``[]`` if no backend is importable
    or the network/rate-limit fails (the caller keeps running; SEMI must never
    invent results).
    """
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
        logger.warning("No ddgs backend installed — search stays empty")
        return []

    hits: list[tuple[str, str]] = []
    try:
        with ddgs_cls() as ddgs:
            for result in ddgs.text(query, max_results=max_results, region="wt-wt"):
                url = (result.get("href") or result.get("url") or "").strip()
                title = (result.get("title") or "").strip()
                if url:
                    hits.append((url, title))
    except Exception as exc:  # network / rate-limit failures degrade gracefully
        logger.warning("Web search failed for %r: %s", query, exc)
        return []
    return hits