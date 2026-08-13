"""Smoke tests for the Day-2 pipeline (ingest -> graph -> resolve)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.ingest import excel_input
from backend.ingest.source_validator import validate_source_url
from backend.schemas.state_graph import Conflict, ConflictSide, StateGraph
from backend.server import app
from backend.sqlite_store import SQLiteStore

client = TestClient(app)


def test_health() -> None:
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_ingest_and_state_graph_lookup(tmp_path) -> None:
    workbook = excel_input.example_workbook(tmp_path / "input.xlsx", rows=4)
    with workbook.open("rb") as fh:
        resp = client.post(
            "/api/ingest",
            files={"file": ("input.xlsx", fh, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["skus_parsed"] == 4
    assert body["status"] == "accepted"

    graph = client.get("/api/state_graph/BV-1001").json()
    assert graph["sku"] == "BV-1001"
    assert graph["manufacturer"] == "NIBCO"

    assert client.get("/api/state_graph/UNKNOWN").status_code == 404


def test_resolve_writes_ledger_and_flips() -> None:
    # Use the server's store directly
    from backend.server import store
    store.set_graph(StateGraph(sku="BV-1001", manufacturer="NIBCO"))
    store.set_conflict(Conflict(
        sku="BV-1001",
        manufacturer="NIBCO",
        attribute="thread",
        a=ConflictSide(value="NPT", source_path="spec.pdf", authority=1.0,
                       source_url="https://www.nibco.com/spec"),
        b=ConflictSide(value="BSPT", source_path="nameplate.jpg", authority=0.6,
                       source_url="https://www.nibco.com/img/plate"),
    ))

    resp = client.post(
        "/api/resolve",
        json={"sku": "BV-1001", "attribute": "thread", "human_resolution": "BSPT",
              "reason_tags": ["admin override"]},
    )
    assert resp.status_code == 200
    assert resp.json()["changed_outcome"] is True
    assert resp.json()["ledger_count"] == 1

    ledger = store.get_ledger()
    assert len(ledger) == 1
    assert ledger[0].source_url == "https://www.nibco.com/img/plate"
    conflict = store.get_conflict("nibco", "bv-1001")
    assert conflict.status == "resolved"

    second = client.post(
        "/api/resolve",
        json={"sku": "BV-1001", "attribute": "thread", "human_resolution": "NPT"},
    )
    assert second.status_code == 409  # conflict already resolved


def test_resolve_rejects_unlisted_value() -> None:
    from backend.server import store
    from backend.schemas.state_graph import ConflictSide
    store.set_graph(StateGraph(sku="BV-1001", manufacturer="NIBCO"))
    store.set_conflict(Conflict(
        sku="BV-1001",
        manufacturer="NIBCO",
        attribute="thread",
        a=ConflictSide(value="NPT", source_path="spec.pdf", authority=1.0),
        b=ConflictSide(value="BSPT", source_path="plate.jpg", authority=0.6),
    ))
    resp = client.post(
        "/api/resolve",
        json={"sku": "BV-1001", "attribute": "thread", "human_resolution": "METRIC"},
    )
    assert resp.status_code == 422


def test_rejects_forbidden_source_urls() -> None:
    ok, _ = validate_source_url("https://www.nibco.com/spec/bv-1001.pdf")
    assert ok
    bad, reason = validate_source_url("https://www.amazon.com/dp/B0ABC123XYZ")
    assert not bad
    assert "forbidden" in reason
