"""Audit runner — turns a StateGraph's candidates into per-attribute verdicts."""

from __future__ import annotations

from dataclasses import dataclass, field

from backend.audit import conformal, physical
from backend.audit.contradiction import CandidateRow, Contradiction, detect
from backend.audit.refusal_gate import Verdict, decide

AUTHORITY_BY_SOURCE_TYPE = {"excel_input": 1.0, "pdf": 0.9, "web": 0.7, "image": 0.5}


@dataclass(slots=True)
class AuditReport:
    sku: str
    manufacturer: str
    verdicts: list[Verdict] = field(default_factory=list)
    findings: list[physical.AuditFinding] = field(default_factory=list)
    contradictions: list[Contradiction] = field(default_factory=list)
    calibrated: bool = False

    def to_dict(self) -> dict:
        return {
            "sku": self.sku,
            "manufacturer": self.manufacturer,
            "calibrated": self.calibrated,
            "findings": [{"attribute": f.attribute, "kind": f.kind, "rule": f.rule,
                          "detail": f.detail, "severity": f.severity}
                         for f in self.findings],
            "contradictions": [{"attribute": c.attribute, "detail": c.detail()}
                               for c in self.contradictions],
            "verdicts": [v.to_dict() for v in self.verdicts],
        }


def authority_of_source(source_type: str) -> float:
    return AUTHORITY_BY_SOURCE_TYPE.get(source_type, 0.5)


def run_audit(graph, calibration: list[tuple[float, bool]] | None = None) -> AuditReport:
    """Audit one SKU graph: physics + contradiction + consensus + conformal CI."""
    sources = {s.path: s for s in graph.sources}

    rows: list[CandidateRow] = []
    context: dict[str, str] = {}
    for ec in graph.extracted_candidates:
        src = sources.get(ec.source_path)
        authority = authority_of_source(src.type) if src else 0.5
        rows.append(CandidateRow(
            attribute=ec.attribute, value=ec.value, confidence=ec.confidence,
            source_url=src.source_url if src else ec.source_path,
            authority=authority, extractor=ec.extractor))
        if ec.value:
            context.setdefault(ec.attribute, ec.value)

    findings = physical.run(context)
    contradictions = detect(rows)
    qhat = conformal.calibrate(calibration or [])

    by_attr: dict[str, list[CandidateRow]] = {}
    for row in rows:
        by_attr.setdefault(row.attribute, []).append(row)

    attr_findings: dict[str, list] = {}
    for f in findings:
        attr_findings.setdefault(f.attribute, []).append(f)

    verdicts = [decide(attr, group, attr_findings.get(attr, []), qhat)
                for attr, group in sorted(by_attr.items())]

    return AuditReport(
        sku=graph.sku, manufacturer=graph.manufacturer,
        verdicts=verdicts, findings=findings, contradictions=contradictions,
        calibrated=qhat is not None)