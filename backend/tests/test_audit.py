"""Adversarial audit tests — physics rules, contradiction, refusal gate, conformal.

Pure module tests (no network) + one endpoint test on a seeded store.
"""

from __future__ import annotations

import pytest

from backend.audit import physical
from backend.audit.contradiction import CandidateRow, detect
from backend.audit.refusal_gate import decide
from backend.audit.conformal import calibrate, predict_interval
from backend.audit.runner import run_audit
from backend.schemas.state_graph import ExtractedCandidate, Source, StateGraph


def _row(attribute, value, confidence, url="https://x.example/spec.pdf",
         authority=0.9, extractor="llm"):
    return CandidateRow(attribute=attribute, value=value, confidence=confidence,
                        source_url=url, authority=authority, extractor=extractor)


def test_physical_pvc_temp_rule_fires():
    findings = physical.run({"material": "PVC", "temperature_rating": "85 C"})
    assert any(f.rule == "material=PVC ∧ temp>60°C" and f.severity == "critical"
               for f in findings)


def test_physical_pressure_unit_conversion():
    findings = physical.run({"material": "BRASS", "pressure_rating": "250 bar"})
    assert any("pressure>3000psi" in f.rule for f in findings)


def test_physical_clean_values_pass():
    assert physical.run({"material": "BRASS", "pressure_rating": "600 psi"}) == []


def test_contradiction_detects_high_confidence_conflict():
    rows = [_row("thread_standard", "NPT", 0.9, "a.pdf"),
            _row("thread_standard", "BSPT", 0.85, "b.pdf")]
    found = detect(rows)
    assert len(found) == 1
    assert found[0].attribute == "thread_standard"


def test_contradiction_ignores_weak_values():
    rows = [_row("thread_standard", "NPT", 0.9),
            _row("thread_standard", "NPT", 0.4)]
    assert detect(rows) == []


def test_refusal_on_empty_evidence():
    v = decide("pressure_rating", [], [], None)
    assert v.status == "REFUSE_INSUFFICIENT_EVIDENCE"
    assert v.value == ""


def test_refusal_on_thin_lone_source():
    rows = [_row("pressure_rating", "150 psi", 0.6, url="https://blog.example/x",
                 authority=0.7)]
    v = decide("pressure_rating", rows, [], None)
    assert v.status == "REFUSE_THIN_EVIDENCE"


def test_refusal_on_low_consensus():
    rows = [_row("pressure_rating", "120 psi", 0.55),
            _row("pressure_rating", "150 psi", 0.6)]
    v = decide("pressure_rating", rows, [], None)
    assert v.status == "REFUSE_LOW_CONSENSUS"


def test_accept_pdf_backed_consensus():
    rows = [_row("pressure_rating", "150 psi", 0.95),
            _row("pressure_rating", "150 psi", 0.9, url="b.pdf")]
    v = decide("pressure_rating", rows, [], None)
    assert v.status == "ACCEPT"
    assert v.value == "150 psi"
    assert v.interval is not None
    assert v.calibrated is False


def test_refusal_physical_violation_beats_consensus():
    rows = [_row("pressure_rating", "300 psi", 0.95),
            _row("pressure_rating", "300 psi", 0.9)]
    findings = physical.run({"material": "PVC", "pressure_rating": "300 psi"})
    v = decide("pressure_rating", rows, findings, None)
    assert v.status == "REFUSE_PHYSICAL_VIOLATION"


def test_conformal_calibrate_requires_30_rows():
    assert calibrate([(0.9, True)] * 5) is None
    rows = [(0.9, True)] * 25 + [(0.5, False), (0.7, True), (0.8, True),
                                 (0.6, False), (0.75, True)] * 2
    assert calibrate(rows) is not None


def test_conformal_interval_uncalibrated_when_no_data():
    lo, hi, calibrated = predict_interval(0.9, None)
    assert calibrated is False
    assert lo == pytest.approx(0.7)
    assert hi == pytest.approx(1.0)


def test_conformal_interval_calibrated():
    rows = [(0.95, True), (0.8, True), (0.7, False), (0.6, False),
            (0.85, True), (0.75, True), (0.65, False), (0.9, True)] * 4
    qhat = calibrate(rows)
    assert qhat is not None
    lo, hi, calibrated = predict_interval(0.9, qhat)
    assert calibrated is True
    assert lo <= 0.9 <= hi


def _graph(*, with_candidates=True) -> StateGraph:
    src = Source(type="pdf", path="https://nibco.com/BV-1001/spec.pdf",
                 source_url="https://nibco.com/BV-1001/spec.pdf")
    graph = StateGraph(sku="BV-1001", manufacturer="NIBCO", sources=[src])
    if with_candidates:
        graph.extracted_candidates = [
            ExtractedCandidate(attribute="pressure_rating", value="150 psi",
                               source_path=src.path, extractor="llm", confidence=0.95),
            ExtractedCandidate(attribute="pressure_rating", value="150 psi",
                               source_path=src.path, extractor="llm", confidence=0.9),
            ExtractedCandidate(attribute="material", value="Brass",
                               source_path=src.path, extractor="llm", confidence=0.9),
        ]
    return graph


def test_run_audit_accepts_and_refuses(tmp_path):
    report = run_audit(_graph())
    verdicts = {v.attribute: v for v in report.verdicts}
    assert verdicts["pressure_rating"].status == "ACCEPT"
    assert verdicts["material"].status == "ACCEPT"
    assert report.calibrated is False
    body = report.to_dict()
    assert any(v["attribute"] == "pressure_rating" and v["status"] == "ACCEPT"
               for v in body["verdicts"])


def test_run_audit_empty_graph_refuses(tmp_path):
    report = run_audit(_graph(with_candidates=False))
    assert report.verdicts == []


def test_audit_endpoint(tmp_path):
    from fastapi.testclient import TestClient
    from backend.ingest import excel_input
    from backend.server import app
    from backend.sqlite_store import SQLiteStore

    p = tmp_path / "in.xlsx"
    excel_input.example_workbook(p, rows=1)
    client = TestClient(app)
    with open(p, "rb") as fh:
        resp = client.post("/api/ingest",
                           files={"file": ("in.xlsx", fh,
                                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    assert resp.status_code == 200
    # Get the SKU from the ingested graph
    resp2 = client.get("/api/graphs")
    assert resp2.status_code == 200
    graphs = resp2.json()["graphs"]
    assert len(graphs) >= 1
    sku = graphs[0]["sku"]
    resp2 = client.get(f"/api/audit/{sku}")
    assert resp2.status_code == 200
    body = resp2.json()
    assert body["sku"] == sku
    assert "verdicts" in body and "findings" in body