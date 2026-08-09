"""Physics / engineering constraint rules (deterministic, no LLM)."""

from __future__ import annotations

import re
from dataclasses import dataclass

_NUMBER = re.compile(r"(-?\d+(?:\.\d+)?)")
_PSI = {"psi": 1.0, "bar": 14.5038, "mpa": 145.038, "kpa": 0.145038}
_TEMP_C = {"c": 0.0, "f": -32.0}


@dataclass(slots=True)
class AuditFinding:
    attribute: str
    kind: str
    rule: str
    detail: str
    severity: str = "warning"


def _first_number(value: str) -> float | None:
    m = _NUMBER.search(value)
    return float(m.group(1)) if m else None


def _unit(value: str) -> str | None:
    low = value.lower()
    for unit in ("mpa", "kpa", "psi", "bar", "°c", "c", "°f", "f", '"', "in", "mm"):
        if unit in low:
            return unit
    return None


def _pressure_psi(value: str) -> float | None:
    n = _first_number(value)
    if n is None:
        return None
    unit = _unit(value) or "psi"
    if unit in _PSI:
        return n * _PSI[unit]
    if unit in ('"', "in", "mm"):
        return None
    return n


def _temp_c(value: str) -> float | None:
    n = _first_number(value)
    if n is None:
        return None
    unit = _unit(value) or "c"
    if unit == "f":
        return (n + _TEMP_C["f"]) * 5 / 9
    return n


def run(context: dict[str, str]) -> list[AuditFinding]:
    """Evaluate constraint rules over a {attribute: value} context map."""
    findings: list[AuditFinding] = []
    material = (context.get("material") or "").upper()
    pressure = _pressure_psi(context.get("pressure_rating") or context.get("pressure") or "")
    temp = _temp_c(context.get("temperature_rating") or context.get("temperature") or "")
    size_in = _first_number(context["size"]) if context.get("size") else None
    unit = _unit(context["size"]) if context.get("size") else ""
    thread = (context.get("thread_standard") or "").upper()

    if material == "PVC" and temp is not None and temp > 60:
        findings.append(AuditFinding(
            attribute="temperature_rating", kind="physical", rule="material=PVC ∧ temp>60°C",
            detail=f"PVC rated to {temp:.0f}°C — exceeds the 60°C ceiling",
            severity="critical"))
    if material == "PVC" and pressure is not None and pressure > 150:
        findings.append(AuditFinding(
            attribute="pressure_rating", kind="physical", rule="material=PVC ∧ pressure>150psi",
            detail=f"PVC rated to {pressure:.0f} psi — exceeds the 150 psi ceiling",
            severity="critical"))
    if material == "BRASS" and pressure is not None and pressure > 3000:
        findings.append(AuditFinding(
            attribute="pressure_rating", kind="physical", rule="material=Brass ∧ pressure>3000psi",
            detail=f"Brass rated to {pressure:.0f} psi — exceeds the 3000 psi ceiling",
            severity="warning"))
    if size_in is not None and unit in ('"', "in") and size_in < 0.5 and pressure is not None and pressure > 10000:
        findings.append(AuditFinding(
            attribute="pressure_rating", kind="physical", rule="size<0.5\" ∧ pressure>10000psi",
            detail=f"Half-inch-or-smaller rated to {pressure:.0f} psi — implausible",
            severity="critical"))
    if thread == "BSPP" and pressure is not None and pressure > 5000:
        findings.append(AuditFinding(
            attribute="thread_standard", kind="physical", rule="thread=BSPP ∧ pressure>5000psi",
            detail="BSPP seal ratings do not reach this range for standard plumbing",
            severity="warning"))
    return findings