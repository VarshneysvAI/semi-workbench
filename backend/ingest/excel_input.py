"""Unilog Excel parser.

Reads the Unilog input workbook and yields (manufacturer, part_number)
records. Column names are normalized against tolerant aliases so DAY 3
(Aug 11 — official input.xlsx release) only requires updating the alias
tables if the shipped headers differ.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

_COL_ALIASES: dict[str, tuple[str, ...]] = {
    "manufacturer": ("manufacturer", "brand", "make", "company", "vendor"),
    "part_number": (
        "part_number", "part no", "part no.", "partno", "mpn",
        "sku", "model", "model no", "catalog number", "catalog_number",
    ),
}


@dataclass(slots=True)
class ProductRecord:
    manufacturer: str
    part_number: str
    extras: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class ParseResult:
    records: list[ProductRecord]
    columns: list[str]
    skipped_rows: int
    source: Path


def parse_input_workbook(path: str | Path, sheet_name: str | int = 0) -> ParseResult:
    """Parse an Unilog-style workbook into ProductRecord row candidates.

    Raises:
        FileNotFoundError: workbook does not exist.
        ValueError: unsupported extension, or missing required column.
    """
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"Input workbook not found: {source}")
    if source.suffix.lower() not in (".xlsx", ".xls"):
        raise ValueError(f"Expected an .xlsx/.xls workbook, got {source.suffix!r}")

    frame = pd.read_excel(source, sheet_name=sheet_name, dtype=str)
    header_map = _match_columns(list(frame.columns))
    missing = {"manufacturer", "part_number"} - set(header_map)
    if missing:
        raise ValueError(
            f"Workbook missing required column(s) {sorted(missing)}; found: {list(frame.columns)}"
        )

    records: list[ProductRecord] = []
    skipped = 0
    for _, row in frame.iterrows():
        manufacturer = str(row.get(header_map["manufacturer"]) or "").strip()
        part_number = str(row.get(header_map["part_number"]) or "").strip()
        if not manufacturer or not part_number:
            skipped += 1
            continue
        extras = {
            str(col): str(value).strip()
            for col in frame.columns
            if col not in header_map.values() and value is not None and str(value).strip()
        }
        records.append(ProductRecord(manufacturer=manufacturer, part_number=part_number, extras=extras))

    # De-duplicate preserving first-seen order.
    seen: set[tuple[str, str]] = set()
    uniques: list[ProductRecord] = []
    for rec in records:
        key = (rec.manufacturer.lower(), rec.part_number.lower())
        if key not in seen:
            seen.add(key)
            uniques.append(rec)

    logger.info("Parsed %d unique products from %s (skipped %d empty rows)",
                len(uniques), source, skipped)
    return ParseResult(records=uniques, columns=list(frame.columns), skipped_rows=skipped, source=source)


def _match_columns(headers) -> dict[str, str]:
    lowered = {str(h): str(h).strip().lower() for h in headers}
    mapping: dict[str, str] = {}
    for canonical, aliases in _COL_ALIASES.items():
        for header, name in lowered.items():
            if name in aliases:
                mapping[canonical] = header
                break
    return mapping


def example_workbook(path: str | Path, rows: int = 5) -> Path:
    """Write a tiny placeholder workbook usable for smoke tests."""
    import pandas as pd
    target = Path(path)
    frame = pd.DataFrame({
        "manufacturer": ["NIBCO"] * rows,
        "part_number": [f"BV-{1000 + i}" for i in range(rows)],
    })
    frame.to_excel(target, index=False)
    logger.info("Wrote placeholder workbook %s (%d rows)", target, rows)
    return target