"""Output mapping to the Unilog output schema (Day 3 prep).

The official ``output_schema.json`` lands ~Aug 11; until then this module
carries the tolerant canonical-attribute table, unit normalisation hooks
and required-field validation so the pipeline shape does not change when
the schema arrives. Re-scope markers are tagged ``DAY3``.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from backend.schemas.state_graph import StateGraph

logger = logging.getLogger(__name__)

# DAY3: update from official output_schema.json when it drops.
CANONICAL_ATTRIBUTES: tuple[str, ...] = (
    "pressure", "temp", "material", "thread", "size", "flow",
    "voltage", "power", "weight", "certification",
)

_ATTR_ALIASES: dict[str, str] = {
    "pressure": ("pressure_rating", "pressure", "max pressure", "psig"),
    "temp": ("temperature", "temp", "temp_rating", "temperature_rating"),
    "material": ("body_material", "material", "body material"),
    "thread": ("thread_standard", "thread", "connection"),
    "size": ("size", "nominal_size", "port_size"),
    "flow": ("cv", "flow_coefficient", "flow"),
    "voltage": ("voltage", "volts"),
    "power": ("power", "watts", "horsepower", "hp"),
    "weight": ("weight", "mass"),
    "certification": ("certification", "approval", "listing"),
}

_UNIT_ALIASES: dict[str, str] = {
    '"': "in", "inch": "in", "inches": "in", "in.": "in",
    "mm": "mm", "psi": "psi", "bar": "bar", "mpa": "MPa",
    "f": "°F", "c": "°C", "gpm": "GPM", "lpm": "LPM", "lbm": "lb",
}


def canonical_attribute(raw: str) -> str:
    """Map an extractor column to the canonical attribute key."""
    lowered = (raw or "").strip().lower().replace("-", "_")
    for canonical, aliases in _ATTR_ALIASES.items():
        if lowered == canonical or lowered in aliases:
            return canonical
    logger.debug("Unmapped attribute %r — carrying raw", raw)
    return lowered or "unknown"


@dataclass(slots=True)
class OutputRow:
    sku: str
    manufacturer: str
    attribute: str
    value: str
    unit: str = ""
    source_url: str | None = None
    page: int | None = None
    extractor: str = "regex"
    confidence: float = 0.0

    def as_dict(self) -> dict:
        return {
            "sku": self.sku,
            "manufacturer": self.manufacturer,
            "attribute": self.attribute,
            "value": self.value,
            "unit": self.unit,
            "source_url": self.source_url,
            "page": self.page,
            "extractor": self.extractor,
            "confidence": round(self.confidence, 3),
        }


def _split_value_unit(raw: str) -> tuple[str, str]:
    """Split ``"150 psi"`` → ("150", "psi"); ``"2\\\""`` → ("2", "in")."""
    if not raw:
        return "", ""
    match = re.search(r"^\s*([+-]?[\d.,\s\-/°x×]+?)\s*([a-zA-Z°\"]+)?\s*$", raw)
    if not match:
        return raw.strip(), ""
    value, unit = match.group(1).strip(), (match.group(2) or "").strip()
    if unit == '"':
        unit = "in"
    return value, _UNIT_ALIASES.get(unit.lower(), unit)


def map_state_graph(graph: StateGraph, *, dedupe: bool = True) -> list[dict]:
    """Translate a StateGraph into output rows (one per candidate).

    Deduplication keeps the highest-confidence candidate per attribute
    unless ``dedupe=False`` (used by the conflict surface).
    """
    rows: list[OutputRow] = []
    for cand in graph.extracted_candidates:
        value, unit = _split_value_unit(cand.value)
        rows.append(
            OutputRow(
                sku=graph.sku,
                manufacturer=graph.manufacturer,
                attribute=canonical_attribute(cand.attribute),
                value=value,
                unit=unit,
                source_url=_source_url_for(graph, cand.source_path),
                page=cand.page,
                extractor=cand.extractor,
                confidence=cand.confidence,
            )
        )
    if not dedupe:
        return [r.as_dict() for r in rows]
    best: dict[str, OutputRow] = {}
    for row in rows:
        key = (row.sku, row.attribute)
        if key not in best or row.confidence > best[key].confidence:
            best[key] = row
    return [r.as_dict() for r in best.values()]


def _source_url_for(graph: StateGraph, path: str) -> str | None:
    for source in graph.sources:
        if source.path == path:
            return source.source_url
    return None


def validate_output(rows: list[dict]) -> list[str]:
    """Return human-readable validation errors (required fields per plan)."""
    errors: list[str] = []
    for idx, row in enumerate(rows):
        if not row.get("sku") or not row.get("manufacturer"):
            errors.append(f"row {idx}: sku/manufacturer required")
        if not row.get("attribute") or row.get("attribute") == "unknown":
            errors.append(f"row {idx}: attribute unmapped")
        if not str(row.get("value", "")).strip():
            errors.append(f"row {idx}: empty value")
        if not row.get("source_url"):
            errors.append(f"row {idx}: missing source_url (transcript rule)")
    return errors
