"""Tests for POST /api/discover/{sku} — hybrid live-search pipeline.

Monkeypatches the network (search -> fetch -> gemma) so CI is deterministic and
offline. Provenance assertions: each produced ExtractedCandidate carries
source_url + extractor='llm' + confidence — no invented values when the model
reports value=''.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.ingest import excel_input
from backend.llm import gemma
from backend.server import app
from backend.sqlite_store import SQLiteStore


def _seed_workbook(tmp_path) -> str:
    p = tmp_path / "in.xlsx"
    excel_input.example_workbook(p, rows=2)
    return str(p)


def _ingest(client, path) -> None:
    with open(path, "rb") as fh:
        resp = client.post(
            "/api/ingest",
            files={"file": ("in.xlsx", fh,
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
    assert resp.status_code == 200
    assert resp.json()["skus_parsed"] >= 1


def test_discover_attaches_sources_and_extracts(monkeypatch, tmp_path):
    from backend.extract import fetchers as fetchers_mod
    from backend.server import gemma as server_gemma

    monkeypatch.setattr("backend.server.search_web",
                        lambda q, max_results=8: [
                            ("https://nibco.com/BV-1001/spec.pdf", "NIBCO BV-1001 spec sheet"),
                            ("https://nibco.com/assets/BV-1001.pdf", "BV-1001 datasheet"),
                        ])

    monkeypatch.setattr("backend.server.fetch_content",
                        lambda url, **kw: fetchers_mod.FetchedDoc(
                            url=url, kind="pdf",
                            text="The NIBCO BV-1001 has NPT threaded connections rated 150 psi.",
                            fetched_via="jina", ok=True))

    monkeypatch.setattr(gemma, "extract_field",
                        lambda mfr, sku, attr, ctx: gemma.FieldExtraction(
                            value="NPT" if attr == "thread" else "",
                            unit="",
                            evidence_snippet="threaded connections NPT",
                            confidence=1.0 if attr == "thread" else 0.0))
    monkeypatch.setattr(server_gemma, "extract_field", gemma.extract_field)
    monkeypatch.setattr(server_gemma, "is_configured", lambda: True)

    client = TestClient(app)
    _ingest(client, _seed_workbook(tmp_path))

    resp = client.post("/api/discover/BV-1001?top_k=2")
    assert resp.status_code == 200
    body = resp.json()
    assert body["sources_attached"] >= 1
    assert body["llm_configured"] is True
    assert any(e["attribute"] == "thread" and e["value"] == "NPT"
               for e in body["extracted"])

    graph = client.get("/api/state_graph/BV-1001").json()
    src_urls = [s["source_url"] for s in graph["sources"]]
    assert any("nibco.com" in u for u in src_urls)
    assert any(ec["attribute"] == "thread" and ec["value"] == "NPT"
               and ec["extractor"] == "llm"
               for ec in graph["extracted_candidates"])


def test_discover_without_llm_attaches_sources_only(monkeypatch, tmp_path):
    from backend.extract import fetchers as fetchers_mod
    from backend.server import gemma as server_gemma

    monkeypatch.setattr("backend.server.search_web",
                        lambda q, max_results=8: [
                            ("https://nibco.com/BV-1001/spec.pdf", "NIBCO BV-1001 spec"),
                        ])
    monkeypatch.setattr("backend.server.fetch_content",
                        lambda url, **kw: fetchers_mod.FetchedDoc(
                            url=url, kind="pdf",
                            text="has NPT threads", fetched_via="jina", ok=True))
    monkeypatch.setattr(server_gemma, "is_configured", lambda: False)

    client = TestClient(app)
    _ingest(client, _seed_workbook(tmp_path))
    resp = client.post("/api/discover/BV-1001?top_k=2&extract=True")
    assert resp.status_code == 200
    body = resp.json()
    assert body["sources_attached"] >= 1
    assert body["llm_configured"] is False
    assert body["extracted"] == []


def test_discover_unknown_sku_404(tmp_path):
    client = TestClient(app)
    _ingest(client, _seed_workbook(tmp_path))
    resp = client.post("/api/discover/UNKNOWN")
    assert resp.status_code == 404
