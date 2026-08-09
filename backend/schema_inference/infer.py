"""Schema-adaptive Excel ingestion.

Per project directive: do not hardcode Unilog's input schema. When a workbook
arrives (incl. the official ~Aug 11 input.xlsx), read its headers + a few sample
rows and ask the LLM to infer the column mapping. The result is an
``InferredSchema`` consumed by ``excel_input.parse_workbook_with_schema``.

When the LLM is not configured (``gemma.is_configured()`` is False), we fall
back to the deterministic alias table in ``excel_input`` — never fake.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from backend.llm import gemma

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class InferredSchema:
    manufacturer_col: str | None = None
    part_number_col: str | None = None
    attribute_cols: list[str] = field(default_factory=list)
    unit_col: str | None = None
    source_url_col: str | None = None
    confidence: float = 0.0
    notes: str = ""
    used_llm: bool = False


def _build_schema():
    from google.genai import types
    return types.Schema(
        type="OBJECT",
        properties={
            "manufacturer_col": types.Schema(type="STRING"),
            "part_number_col": types.Schema(type="STRING"),
            "attribute_cols": types.Schema(
                type="ARRAY", items=types.Schema(type="STRING")
            ),
            "unit_col": types.Schema(type="STRING"),
            "source_url_col": types.Schema(type="STRING"),
            "confidence": types.Schema(type="NUMBER"),
            "notes": types.Schema(type="STRING"),
        },
        required=["manufacturer_col", "part_number_col"],
    )


SYS_INFER = (
    "You inspect a spreadsheet's headers and sample rows to infer a column "
    "mapping for industrial product data. Return ONLY column names that appear "
    "in the provided 'columns' list. If you cannot identify a field, return an "
    "empty string for it. attribute_cols = columns that hold technical spec "
    "values (pressure, material, thread, size, ...). unit_col = a column that "
    "holds units, if any. confidence = your confidence 0..1 in the mapping."
)


def _sample_workbook(path: Path, n: int = 3) -> tuple[list[str], list[list[str]]]:
    frame = pd.read_excel(path, sheet_name=0, dtype=str).head(20)
    cols = [str(c) for c in list(frame.columns)]
    sample = frame.head(n).fillna("").astype(str).values.tolist()
    return cols, [[str(c) for c in row] for row in sample]


def infer_from_workbook(path: str | Path) -> InferredSchema:
    """Infer the column mapping from any uploaded workbook via the LLM."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Input workbook not found: {p}")

    cols, sample = _sample_workbook(p)
    if not gemma.is_configured():
        logger.info("LLM not configured — returning a schema with no mapping for %d cols", len(cols))
        return InferredSchema(notes="llm-unconfigured; caller should use alias fallback", used_llm=False)

    payload = json.dumps({"columns": cols, "sample_rows": sample, "n_rows_shown": len(sample)})
    raw = gemma.classify_json(payload, _build_schema(), system=SYS_INFER)
    schema = _coerce(raw, cols)
    schema.used_llm = True
    logger.info("Inferred schema (conf=%.2f, llm=%s): mfr=%r pn=%r attrs=%d",
                schema.confidence, schema.used_llm,
                schema.manufacturer_col, schema.part_number_col, len(schema.attribute_cols))
    return schema


def _coerce(raw: dict, cols: list[str]) -> InferredSchema:
    lowered = {str(c).lower(): c for c in cols}

    def pick(value):
        v = str(value or "").strip()
        if not v:
            return None
        if v in cols:
            return v
        if v.lower() in lowered:
            return lowered[v.lower()]
        return None

    raw_attrs = raw.get("attribute_cols") or []
    if not isinstance(raw_attrs, list):
        raw_attrs = [raw_attrs]
    attrs = [a for a in (pick(a) for a in raw_attrs) if a]

    return InferredSchema(
        manufacturer_col=pick(raw.get("manufacturer_col")),
        part_number_col=pick(raw.get("part_number_col")),
        attribute_cols=attrs,
        unit_col=pick(raw.get("unit_col")),
        source_url_col=pick(raw.get("source_url_col")),
        confidence=float(raw.get("confidence", 0.0) or 0.0),
        notes=str(raw.get("notes", "") or "").strip(),
    )


def is_meaningful(schema: InferredSchema) -> bool:
    """True if the inferred schema is usable (manufacturer+part_number both located)."""
    return bool(schema.manufacturer_col and schema.part_number_col)
