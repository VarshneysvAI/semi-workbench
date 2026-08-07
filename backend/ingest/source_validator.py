"""Source URL validation.

Transcript requirement — forbidden sources: Amazon, eBay, Target and any
e-commerce / marketplace listing must never enter the pipeline. Every
discovered URL is checked here before it is persisted as a ``source_url``.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Explicit marketplace/e-commerce eTLD+1 that must never be accepted.
FORBIDDEN_DOMAINS: frozenset[str] = frozenset({
    "amazon.com", "amazon.in", "amazon.co.uk", "amazon.de", "amazon.ca",
    "ebay.com", "ebay.in", "ebay.co.uk", "ebay.com.au",
    "target.com",
    "walmart.com", "walmart.ca",
    "aliexpress.com", "alibaba.com",
    "etsy.com", "wish.com", "temu.com",
    "flipkart.com",
})

FORBIDDEN_URL_MARKERS: tuple[str, ...] = (
    "/dp/", "/gp/product/", "marketplace", "/shop/listing",
)


@lru_cache(maxsize=4096)
def parse_host(url: str) -> str | None:
    """Normalize the ``netloc`` of a URL or None./pparsed failure."""
    if not url or not str(url).strip():
        return None
    parsed = urlparse(str(url) if "//" in url else f"https://{url}")
    return parsed.netloc.lower()


def is_forbidden_url(url: str) -> bool:
    """True when the URL names a forbidden e-commerce domain."""
    host = parse_host(url)
    if not host:
        return True
    for forbidden in FORBIDDEN_DOMAINS:
        if host == forbidden or host.endswith(f".{forbidden}"):
            return True
    return False


def matches_marketplace_path(url: str) -> bool:
    """Heuristic path-level marketplace signals (amazon/ebay mirror sites)."""
    host = parse_host(url) or ""
    path = urlparse(url if "//" in url else f"https://{url}").path.lower()
    if "eba" in host or "amazo" in host:
        return True
    return any(marker in path for marker in FORBIDDEN_URL_MARKERS)


def validate_source_url(url: str) -> tuple[bool, str]:
    """Validate one candidate source URL.

    Returns (accepted: bool, reason: str). Reason documents either the
    rejection cause or that the URL passed validation.
    """
    if not url or not url.strip():
        return False, "empty URL"
    if is_forbidden_url(url):
        return False, f"forbidden e-commerce domain: {parse_host(url)}"
    if matches_marketplace_path(url):
        return False, "marketplace listing path pattern"
    return True, "passed source validation"