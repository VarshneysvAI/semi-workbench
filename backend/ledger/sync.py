"""Sync audit contradictions into open Conflict rows (the Review queue feed)."""

from __future__ import annotations

from backend.audit.runner import AuditReport
from backend.schemas.state_graph import Conflict, ConflictSide, StateGraph


def sync_conflicts(
    graph: StateGraph,
    report: AuditReport,
    conflicts: dict[tuple[str, str], Conflict],
) -> list[Conflict]:
    """One open Conflict per SKU, taken from the first live contradiction."""
    key = (graph.manufacturer.lower(), graph.sku.lower())
    current = conflicts.get(key)
    if current and current.status == "open":
        return []
    if not report.contradictions:
        return []

    contra = report.contradictions[0]
    conflict = Conflict(
        sku=graph.sku,
        manufacturer=graph.manufacturer,
        attribute=contra.attribute,
        a=ConflictSide(
            value=contra.a.value,
            source_path=contra.a.source_url or "web",
            authority=contra.a.authority,
            source_url=contra.a.source_url,
        ),
        b=ConflictSide(
            value=contra.b.value,
            source_path=contra.b.source_url or "web",
            authority=contra.b.authority,
            source_url=contra.b.source_url,
        ),
        status="open",
    )
    conflicts[key] = conflict
    return [conflict]