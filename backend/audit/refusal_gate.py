"""Refusal gate — ACCEPT only on weighted consensus, otherwise REFUSE.

The opposite of "flag low confidence but still ship a value": a cell with thin
evidence stays empty (``INSUFFICIENT_EVIDENCE``) — SEMI never guesses.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from backend.audit.conformal import predict_interval
from backend.audit.contradiction import CandidateRow
from backend.audit.physical import AuditFinding

MIN_CONSENSUS = 0.7
THIN_AUTHORITY = 0.9
THIN_CONFIDENCE = 0.8


@dataclass(slots=True)
class Verdict:
    attribute: str
    status: str
    value: str
    confidence: float = 0.0
    interval: tuple[float, float] | None = None
    calibrated: bool = False
    reason: str = ""
    findings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "attribute": self.attribute,
            "status": self.status,
            "value": self.value,
            "confidence": round(self.confidence, 3),
            "interval": [round(self.interval[0], 3), round(self.interval[1], 3)]
                        if self.interval else None,
            "calibrated": self.calibrated,
            "reason": self.reason,
            "findings": self.findings,
        }


def _weight(row: CandidateRow) -> float:
    return row.authority * row.confidence


def _best(rows: list[CandidateRow]) -> CandidateRow:
    return max(rows, key=_weight)


def decide(
    attribute: str,
    rows: list[CandidateRow],
    findings: list[AuditFinding],
    qhat: float | None,
) -> Verdict:
    if not rows:
        return Verdict(attribute=attribute, status="REFUSE_INSUFFICIENT_EVIDENCE",
                       value="", confidence=0.0,
                       reason="no source produced a value for this attribute")

    critical = [f for f in findings if f.severity == "critical"]
    if critical:
        rules = ", ".join(f.rule for f in critical)
        return Verdict(attribute=attribute, status="REFUSE_PHYSICAL_VIOLATION",
                       value="", confidence=0.0,
                       reason=f"constraint rule fired: {rules}",
                       findings=[f.detail for f in critical])

    if len(rows) == 1:
        row = rows[0]
        if row.authority < THIN_AUTHORITY and row.confidence < THIN_CONFIDENCE:
            return Verdict(attribute=attribute, status="REFUSE_THIN_EVIDENCE",
                           value="", confidence=0.0,
                           reason=(f"single low-authority source "
                                   f"{row.source_url or row.extractor} at conf "
                                   f"{row.confidence:.2f} — not enough to ship"))

    score = _weight(_best(rows))
    if score < MIN_CONSENSUS:
        return Verdict(attribute=attribute, status="REFUSE_LOW_CONSENSUS",
                       value="", confidence=score,
                       reason=f"weighted consensus {score:.2f} < {MIN_CONSENSUS}")

    winner = _best(rows)
    lo, hi, calibrated = predict_interval(score, qhat)
    return Verdict(attribute=attribute, status="ACCEPT",
                   value=winner.value, confidence=score,
                   interval=(lo, hi), calibrated=calibrated,
                   reason=f"max-weight source {winner.source_url or winner.extractor}")