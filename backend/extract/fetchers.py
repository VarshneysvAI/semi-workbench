"""Content-fetch router — turns a discovered source URL into clean markdown.

Per directive: the architecture is hybrid and content-type aware.
- PDF  -> Firecrawl parsePDF (when key) -> Jina Reader -> none
- WEB  -> Firecrawl (when key) -> Jina Reader -> httpx + BeautifulSoup
- VIDEO (YouTube etc.) -> Jina Reader (returns transcript when present) -> none

No faking: every backend failure degrades transparently; the returned
``FetchedDoc`` carries ``fetched_via`` and ``error`` so the StateGraph source
chain is honest about where text came from (or did not).
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from backend.discover.agent_reach_agent import AgentReachAgent
from backend.env import ensure_env

ensure_env()
logger = logging.getLogger(__name__)

_AGENT = AgentReachAgent()


@dataclass(slots=True)
class FetchedDoc:
    url: str
    kind: str
    text: str = ""
    fetched_via: str = "none"
    ok: bool = False
    error: str = ""


def classify_kind(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.lower()
    host = parsed.netloc.lower()
    if path.endswith(".pdf"):
        return "pdf"
    if "youtube.com" in host or "youtu.be" in host or "vimeo.com" in host:
        return "video"
    if path.endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")):
        return "image"
    return "web"


def fetch_content(url: str, *, kind: str | None = None, timeout: float = 30.0) -> FetchedDoc:
    k = kind or classify_kind(url)

    if os.environ.get("FIRECRAWL_API_KEY"):
        d = _firecrawl(url, k, timeout)
        if d.ok and d.text.strip():
            return d
        logger.info("firecrawl miss for %s (%s) -> falling back: %s", url, k, d.error or "empty")

    if k == "video":
        d = _yt_subtitles(url, timeout)
        if d.ok and d.text.strip():
            return d
        d = _agentreach_transcript(url, timeout)
        if d.ok and d.text.strip():
            return d

    d = _jina_reader(url, timeout)
    if d.ok and d.text.strip():
        return d

    if k == "web":
        d = _httpx_html(url, timeout)
        if d.ok and d.text.strip():
            return d

    return FetchedDoc(url=url, kind=k, fetched_via="none", ok=False,
                      error="no backend returned content")


def _firecrawl(url: str, kind: str, timeout: float) -> FetchedDoc:
    base = os.environ.get("FIRECRAWL_BASE_URL", "https://api.firecrawl.dev/v2").rstrip("/")
    key = os.environ.get("FIRECRAWL_API_KEY", "")
    body = {
        "url": url,
        "formats": ["markdown"],
        "onlyMainContent": True,
        "parsePDF": kind == "pdf",
        "timeout": int(timeout * 1000),
    }
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    try:
        with httpx.Client(timeout=timeout + 5) as cli:
            r = cli.post(f"{base}/scrape", json=body, headers=headers)
        if r.status_code >= 400:
            return FetchedDoc(url=url, kind=kind, fetched_via="firecrawl", ok=False,
                              error=f"{r.status_code}: {r.text[:120]}")
        data = r.json().get("data", {})
        text = (data.get("markdown") or "").strip()
        return FetchedDoc(url=url, kind=kind, text=text, fetched_via="firecrawl",
                          ok=bool(text), error="" if text else "empty markdown")
    except Exception as exc:
        return FetchedDoc(url=url, kind=kind, fetched_via="firecrawl", ok=False,
                          error=f"{type(exc).__name__}: {str(exc)[:120]}")


def _jina_reader(url: str, timeout: float) -> FetchedDoc:
    base = os.environ.get("JINA_READER_BASE_URL", "https://r.jina.ai").rstrip("/")
    try:
        with httpx.Client(timeout=timeout + 5, follow_redirects=True) as cli:
            r = cli.get(f"{base}/{url}")
        ok = r.status_code < 400 and bool(r.text.strip())
        return FetchedDoc(url=url, kind=classify_kind(url), text=r.text or "",
                          fetched_via="jina", ok=ok,
                          error="" if ok else f"{r.status_code}")
    except Exception as exc:
        return FetchedDoc(url=url, kind=classify_kind(url), fetched_via="jina",
                          ok=False, error=f"{type(exc).__name__}: {str(exc)[:120]}")


def _httpx_html(url: str, timeout: float) -> FetchedDoc:
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as cli:
            r = cli.get(url, headers={"User-Agent": "SEMI/0.2 (+product-intelligence research)"})
        if r.status_code >= 400:
            return FetchedDoc(url=url, kind="web", fetched_via="httpx", ok=False,
                              error=f"{r.status_code}")
        soup = BeautifulSoup(r.text, "lxml")
        for sel in ("script", "style", "noscript"):
            for node in soup.select(sel):
                node.decompose()
        text = "\n".join(t for t in (soup.get_text("\n", strip=True)).splitlines() if t)
        return FetchedDoc(url=url, kind="web", text=text, fetched_via="httpx",
                          ok=bool(text), error="" if text else "empty text")
    except Exception as exc:
        return FetchedDoc(url=url, kind="web", fetched_via="httpx", ok=False,
                          error=f"{type(exc).__name__}: {str(exc)[:120]}")


def _yt_subtitles(url: str, timeout: float) -> FetchedDoc:
    """YouTube transcript via yt-dlp subtitles (documented agent-reach tool)."""
    exe = os.environ.get("YTDLP_CMD")
    if not exe:
        import shutil as _sh
        exe = _sh.which("yt-dlp")
    if not exe:
        return FetchedDoc(url=url, kind="video", fetched_via="yt-dlp", ok=False,
                          error="yt-dlp not found")
    import subprocess
    import tempfile
    tmp = tempfile.mkdtemp(prefix="semi_yt_")
    try:
        cmd = [exe, "--write-sub", "--write-auto-sub", "--sub-lang", "en",
               "--skip-download", "-o", f"{tmp}/%(id)s", url]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 60)
        if proc.returncode != 0:
            return FetchedDoc(url=url, kind="video", fetched_via="yt-dlp", ok=False,
                              error=(proc.stderr or proc.stdout or "yt-dlp failed")[:120])
        lines: list[str] = []
        for name in sorted(__import__("os").listdir(tmp)):
            if name.endswith((".vtt", ".srt")):
                with open(f"{tmp}/{name}", encoding="utf-8", errors="ignore") as fh:
                    text = fh.read()
                if text.strip():
                    lines.append(text)
        joined = "\n".join(lines).strip()
        return FetchedDoc(url=url, kind="video", text=joined, fetched_via="yt-dlp",
                          ok=bool(joined),
                          error="" if joined else "no subtitle files produced")
    except Exception as exc:
        return FetchedDoc(url=url, kind="video", fetched_via="yt-dlp", ok=False,
                          error=f"{type(exc).__name__}: {str(exc)[:120]}")
    finally:
        import shutil as _sh
        _sh.rmtree(tmp, ignore_errors=True)


def _agentreach_transcript(url: str, timeout: float) -> FetchedDoc:
    text = _AGENT.transcribe(url, timeout=timeout + 60)
    if not text:
        return FetchedDoc(url=url, kind="video", fetched_via="agent-reach", ok=False,
                          error="agent-reach transcribe unavailable/empty")
    return FetchedDoc(url=url, kind="video", text=text, fetched_via="agent-reach", ok=True)
