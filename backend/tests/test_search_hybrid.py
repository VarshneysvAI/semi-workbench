"""Hybrid discovery routing tests — priority chain agent-reach -> firecrawl -> exa -> ddgs.

All network/subrecess layers are monkeypatched; CI stays deterministic and
offline. The point is *routing order and provenance*, not HTTP details.
"""

from __future__ import annotations

import pytest


class FakeResponse:
    def __init__(self, status_code: int = 200, payload: object = None):
        self.status_code = status_code
        self._payload = payload
        self.text = "" if status_code < 400 else "nope"

    def json(self):
        return self._payload


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for var in ("AGENTREACH_ENABLED", "AGENTREACH_CMD", "FIRECRAWL_API_KEY",
                "EXA_API_KEY"):
        monkeypatch.delenv(var, raising=False)


@pytest.fixture
def no_agent_reach(monkeypatch):
    from backend.discover import search as search_mod

    class EmptyAgent:
        def search_web(self, query, max_results=8):
            return []

    monkeypatch.setattr(search_mod, "_AGENT", EmptyAgent())


def test_agent_reach_serves_first(monkeypatch):
    from backend.discover import search as search_mod

    class AgentWithHits:
        def __init__(self):
            self.calls = []

        def search_web(self, query, max_results=8):
            self.calls.append(query)
            return [("https://ar.example/BV-1001.pdf", "via agent-reach")]

    fake = AgentWithHits()
    monkeypatch.setattr(search_mod, "_AGENT", fake)

    def boom(*a, **k):
        raise AssertionError("ddgs must not be reached when agent-reach hits")

    monkeypatch.setattr(search_mod, "_ddgs_search", boom)

    hits = search_mod.search_web("BV-1001 spec", max_results=4)
    assert hits[0][0] == "https://ar.example/BV-1001.pdf"
    assert search_mod.last_search_backend() == "agent-reach"
    assert fake.calls == ["BV-1001 spec"]


def test_agent_reach_disabled_skips_to_next(monkeypatch):
    from backend.discover import search as search_mod
    monkeypatch.setenv("AGENTREACH_ENABLED", "false")
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fc-test")

    def called_agent(query, max_results=8):
        raise AssertionError("agent-reach must be skipped when disabled")

    class BannedAgent:
        def search_web(self, query, max_results=8):
            return called_agent(query, max_results)

    monkeypatch.setattr(search_mod, "_AGENT", BannedAgent())
    monkeypatch.setattr(search_mod, "_ddgs_search", lambda q, n: [])

    fake_post = lambda url, **kw: FakeResponse(200, {
        "data": {"web": [{"url": "https://fc.example/spec.pdf", "title": "FC spec"}]}})
    monkeypatch.setattr(search_mod.httpx, "post", fake_post)

    hits = search_mod.search_web("BV-1001", max_results=4)
    assert hits[0][0] == "https://fc.example/spec.pdf"
    assert search_mod.last_search_backend() == "firecrawl"


def test_firecrawl_then_exa_then_ddgs(monkeypatch, no_agent_reach):
    from backend.discover import search as search_mod
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fc-test")
    monkeypatch.setenv("EXA_API_KEY", "exa-test")

    calls: list[str] = []

    def fake_post(url, **kw):
        calls.append(url)
        if "firecrawl" in url:
            return FakeResponse(500)
        if "exa" in url:
            return FakeResponse(200, {"results": [{"url": "https://exa.example/p.pdf",
                                                   "title": "Exa hit"}]})
        raise AssertionError(f"unexpected url {url}")

    monkeypatch.setattr(search_mod.httpx, "post", fake_post)
    monkeypatch.setattr(search_mod, "_ddgs_search", lambda q, n: [])

    hits = search_mod.search_web("BV-1001", max_results=4)
    assert hits[0][0] == "https://exa.example/p.pdf"
    assert search_mod.last_search_backend() == "exa"
    assert len(calls) == 2


def test_ddgs_is_last_resort(monkeypatch, no_agent_reach):
    from backend.discover import search as search_mod
    monkeypatch.setattr(search_mod, "_ddgs_search",
                        lambda q, n: [("https://ddg.example/x.pdf", "DDG hit")])

    hits = search_mod.search_web("BV-1001", max_results=4)
    assert hits[0][0] == "https://ddg.example/x.pdf"
    assert search_mod.last_search_backend() == "ddgs"


def test_no_backends_returns_empty_and_none(monkeypatch, no_agent_reach):
    from backend.discover import search as search_mod
    monkeypatch.setattr(search_mod, "_ddgs_search", lambda q, n: [])

    assert search_mod.search_web("BV-1001") == []
    assert search_mod.last_search_backend() == "none"


def test_agent_reach_agent_unavailable_without_cmd(monkeypatch):
    from backend.discover.agent_reach_agent import AgentReachAgent
    monkeypatch.setattr("backend.discover.agent_reach_agent.shutil.which",
                        lambda name: None)
    agent = AgentReachAgent(cmd=None)
    assert agent.available() is False
    assert agent.search_web("BV-1001") == []
    assert agent.transcribe("https://youtu.be/abc") == ""
    assert agent.doctor()["available"] is False


def test_video_fetch_prefers_ytdlp_then_agent_reach_then_jina(monkeypatch):
    from backend.extract import fetchers as fetchers_mod

    def fake_yt(url, timeout):
        return fetchers_mod.FetchedDoc(url=url, kind="video",
                                       text="threaded connections rated 150 psi",
                                       fetched_via="yt-dlp", ok=True)

    monkeypatch.setattr(fetchers_mod, "_yt_subtitles", fake_yt)
    monkeypatch.setattr("backend.extract.fetchers._jina_reader",
                        lambda url, t: (_ for _ in ()).throw(AssertionError("jina skipped")))

    doc = fetchers_mod.fetch_content("https://youtube.com/watch?v=abc")
    assert doc.fetched_via == "yt-dlp"
    assert "150 psi" in doc.text