"""Conformal calibration rows from the human-resolution ledger.

For every resolved conflict, the human's pick (stored in the ledger row) is
ground truth: each candidate row of that attribute contributes
``(confidence, correct)`` — correct when the candidate matches the resolution.
With >= 30 such labels the split-conformal intervals become real 95%
intervals instead of the uncalibrated band.
"""

from __future__ import annotations

from backend.ledger.flywheel import canonical_signature
from backend.schemas.state_graph import Conflict, LedgerRow, StateGraph


def _signature(conflict: Conflict) -> str:
    return canonical_signature(conflict.a.value, conflict.b.value)


def build_calibration(
    conflicts: dict[tuple[str, str], Conflict],
    graphs: dict[tuple[str, str], StateGraph],
    ledger: list[LedgerRow],
) -> list[tuple[float, bool]]:
    resolutions = {row.signature: row.resolution for row in ledger}
    rows: list[tuple[float, bool]] = []

    for conflict in conflicts.values():
        if conflict.status != "resolved":
            continue
        human = resolutions.get(_signature(conflict))
        if human is None:
            continue
        graph = graphs.get((conflict.manufacturer.lower(), conflict.sku.lower()))
        if not graph:
            continue
        source_types = {s.path: s.type for s in graph.sources}
        for ec in graph.extracted_candidates:
            if ec.attribute != conflict.attribute:
                continue
            source_type = source_types.get(ec.source_path, "web")
            if source_type == "excel_input":
                continue
            rows.append((ec.confidence, (ec.value or "").strip() == human.strip()))
    return rows