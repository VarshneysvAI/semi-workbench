"""SEMI discovery agent — agent-reach CLI adapter (first-priority backend).

agent-reach is an installable CLI that routes 15 platforms through OpenCLI /
per-platform CLIs / APIs. This adapter detects it at runtime and degrades
transparently when it is absent: ``available()`` is False, ``search_web``
returns [], and callers fall through to Firecrawl -> Exa -> ddgs.

Only documented agent-reach commands are used; nothing is guessed:
- ``agent-reach doctor --json``  (channel health)
- ``agent-reach --help``          (subcommand probing, per the skill's adapter-discovery rule)
- ``agent-reach search --json``   (only when the help probe proves the subcommand exists)
- ``agent-reach transcribe URL``  (audio transcription fallback for video)
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

_HELP_SEARCH_TOKENS = ("search", "web", "exa")


@dataclass(slots=True)
class AgentReachAgent:
    cmd: str | None = None
    _help_cache: str = ""
    _doctor_cache: dict = field(default_factory=dict)
    _probed: bool = False

    def resolve_cmd(self) -> str | None:
        if self.cmd is None:
            self.cmd = (
                os.environ.get("AGENTREACH_CMD")
                or shutil.which("agent-reach")
            )
        return self.cmd

    def available(self) -> bool:
        return self.resolve_cmd() is not None

    def run(self, *args: str, timeout: float = 30.0) -> subprocess.CompletedProcess:
        cmd = self.resolve_cmd()
        if cmd is None:
            raise FileNotFoundError("agent-reach CLI not installed")
        return subprocess.run(
            [cmd, *args], capture_output=True, text=True, timeout=timeout
        )

    def doctor(self) -> dict:
        if self._doctor_cache:
            return self._doctor_cache
        if not self.available():
            self._doctor_cache = {
                "available": False,
                "reason": "agent-reach CLI not found on PATH",
            }
            return self._doctor_cache
        try:
            proc = self.run("doctor", "--json", timeout=25.0)
            data = json.loads(proc.stdout or "{}")
            self._doctor_cache = {"available": True, **data}
        except Exception as exc:
            logger.warning("agent-reach doctor failed: %s", exc)
            self._doctor_cache = {"available": False, "reason": str(exc)}
        return self._doctor_cache

    def _probe_search_subcommand(self) -> bool:
        if self._probed:
            return bool(self._help_cache)
        self._probed = True
        if not self.available():
            return False
        try:
            proc = self.run("--help", timeout=15.0)
            self._help_cache = f"{proc.stdout}\n{proc.stderr}".lower()
        except Exception as exc:
            logger.warning("agent-reach --help failed: %s", exc)
            self._help_cache = ""
        return bool(self._help_cache)

    def search_web(self, query: str, max_results: int = 8) -> list[tuple[str, str]]:
        """agent-reach search; [] when the CLI or its search subcommand is absent."""
        if not self._probe_search_subcommand():
            return []
        if not any(tok in self._help_cache for tok in _HELP_SEARCH_TOKENS):
            logger.info("agent-reach has no discoverable search subcommand — skipping")
            return []
        try:
            proc = self.run("search", "--json", query, timeout=30.0)
            payload = json.loads(proc.stdout or proc.stderr or "{}")
        except Exception as exc:
            logger.warning("agent-reach search failed: %s", exc)
            return []
        return _extract_hits(payload, max_results)

    def transcribe(self, url: str, timeout: float = 120.0) -> str:
        """agent-reach transcribe <url> -> plain text ('' when unavailable/failed)."""
        if not self.available():
            return ""
        try:
            proc = self.run("transcribe", url, timeout=timeout)
            return (proc.stdout or proc.stderr or "").strip()
        except Exception as exc:
            logger.warning("agent-reach transcribe failed: %s", exc)
            return ""

    def extract_web(self, url: str, timeout: float = 60.0) -> str:
        """agent-reach extract <url> -> plain text ('' when unavailable/failed)."""
        if not self.available():
            return ""
        try:
            proc = self.run("extract", url, timeout=timeout)
            return (proc.stdout or proc.stderr or "").strip()
        except Exception as exc:
            logger.warning("agent-reach extract failed: %s", exc)
            return ""


def _extract_hits(payload, max_results: int) -> list[tuple[str, str]]:
    """Tolerate the shapes agent-reach backends return: lists or result dicts."""
    hits: list[tuple[str, str]] = []
    if isinstance(payload, list):
        sources = payload
    elif isinstance(payload, dict):
        sources = payload.get("results") or payload.get("web") or payload.get("data", {}).get("web", []) if isinstance(payload.get("data"), dict) else payload.get("results") or payload.get("web") or []
    else:
        sources = []
    if not isinstance(sources, list):
        sources = []
    for item in sources:
        if not isinstance(item, dict):
            continue
        url = str(item.get("url") or item.get("href") or "").strip()
        title = str(item.get("title") or "").strip()
        if url:
            hits.append((url, title))
        if len(hits) >= max_results:
            break
    return hits