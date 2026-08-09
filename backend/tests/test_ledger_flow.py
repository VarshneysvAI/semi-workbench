"""Day 8/9 — conflict sync, conformal calibration feed, precedent flywheel."""

from __future__ import annotations

from backend.ledger.flywheel import cosine, embed, find_precedents
from backend.ledger.calibration import build_calibration
from backend.ledger.sync import sync_conflicts
from backend.audit.runner import run_audit
from backend.schemas.state_graph import (Conflict, ConflictSide, ExtractedCandidate,
                                         LedgerRow, Source, StateGraph)


def _graph(manufacturer="NIBCO", sku="BV-1001", values=("NPT", "BSPT")) -> StateGraph:
    srcs = [Source(type="pdf", path="https://a.example/spec.pdf",
                   source_url="https://a.example/spec.pdf"),
            Source(type="web", path="https://b.example/page",
                   source_url="https://b.example/page")]
    graph = StateGraph(sku=sku, manufacturer=manufacturer, sources=srcs)
    graph.extracted_candidates = [
        ExtractedCandidate(attribute="thread_standard", value=values[0],
                           source_path=srcs[0].path, extractor="llm", confidence=0.92),
        ExtractedCandidate(attribute="thread_standard", value=values[1],
                           source_path=srcs[1].path, extractor="llm", confidence=0.8),
    ]
    return graph


def test_sync_creates_one_open_conflict():
    graph = _graph()
    report = run_audit(graph)
    conflicts = {}
    created = sync_conflicts(graph, report, conflicts)
    assert len(created) == 1
    conflict = conflicts[("nibco", "bv-1001")]
    assert conflict.status == "open"
    assert conflict.attribute == "thread_standard"
    assert {conflict.a.value, conflict.b.value} == {"NPT", "BSPT"}


def test_sync_keeps_existing_open_conflict():
    graph = _graph()
    report = run_audit(graph)
    conflicts = {}
    sync_conflicts(graph, report, conflicts)
    key = ("nibco", "bv-1001")
    existing = conflicts[key]
    existing.status = "open"
    assert sync_conflicts(graph, run_audit(graph), conflicts) == []
    assert conflicts[key] is existing


def test_sync_resolved_conflict_allows_recreation():
    graph = _graph()
    conflicts = {}
    key = ("nibco", "bv-1001")
    sync_conflicts(graph, run_audit(graph), conflicts)
    conflicts[key].status = "resolved"
    assert sync_conflicts(graph, run_audit(graph), conflicts) != []


def test_build_calibration_from_resolved_conflict():
    graph = _graph()
    key = ("nibco", "bv-1001")
    conflict = Conflict(sku="BV-1001", manufacturer="NIBCO",
                        attribute="thread_standard",
                        a=ConflictSide(value="NPT", source_path="a", authority=0.9),
                        b=ConflictSide(value="BSPT", source_path="b", authority=0.7),
                        status="resolved")
    ledger = [LedgerRow(sku="BV-1001", manufacturer="NIBCO", signature="BSPT vs NPT",
                        resolution="NPT", note="spec_sheet_authority",
                        source_url="https://a.example/spec.pdf", changed_outcome=False, at=1)]
    rows = build_calibration({key: conflict}, {key: graph}, ledger)
    assert (0.92, True) in rows
    assert (0.8, False) in rows


def test_build_calibration_ignores_open_conflicts():
    graph = _graph()
    key = ("nibco", "bv-1001")
    conflict = Conflict(sku="BV-1001", manufacturer="NIBCO",
                        attribute="thread_standard",
                        a=ConflictSide(value="NPT", source_path="a", authority=0.9),
                        b=ConflictSide(value="BSPT", source_path="b", authority=0.7),
                        status="open")
    rows = build_calibration({key: conflict}, {key: graph}, [])
    assert rows == []


def test_embed_cosine_exact_and_threshold():
    a = embed("NPT vs BSPT")
    b = embed("NPT vs BSPT")
    assert cosine(a, b) == pytest_approx(1.0)
    c = embed("NPT standard")
    assert 0.0 < cosine(a, c) < 0.85
    d = embed("pressure 150 psi")
    assert cosine(a, d) < 0.3


def test_find_precedents_exact_and_fuzzy():
    sigs = ["NPT vs BSPT", "pressure 150 psi"]
    hits = find_precedents(sigs, "NPT vs BSPT")
    assert any(s == "NPT vs BSPT" and sc == 1.0 for s, sc in hits)
    assert not any(s == "pressure 150 psi" for s, _ in hits)


def test_canonical_signature_order_insensitive():
    from backend.ledger.flywheel import canonical_signature
    assert canonical_signature("NPT", "BSPT") == canonical_signature("BSPT", "NPT")
    a = canonical_signature("NPT", "BSPT")
    hits = find_precedents([a], canonical_signature("BSPT", "NPT"))
    assert hits[0][1] == 1.0


def pytest_approx(x):
    from pytest import approx
    return approx(x)


def test_audit_uses_ledger_calibration(tmp_path):
    from backend.audit.runner import run_audit as ra
    graph = _graph(values=("NPT", "BSPT"))
    rows = [(0.95, True), (0.8, True), (0.7, False)] * 11
    report = ra(graph, calibration=rows)
    assert report.calibrated is True
    for v in report.verdicts:
        if v.status == "ACCEPT":
            assert v.interval is not None