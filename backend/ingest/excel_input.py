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
    "manufacturer": ("manufacturer", "brand", "make", "company", "vendor", "part_manuf", "part manuf", "mfr", "e1_brand", "unilog_brand", "dib_brand"),
    "part_number": (
        "part_number", "part no", "part no.", "partno", "mpn",
        "sku", "model", "model no", "catalog number", "catalog_number",
        "mfg_part_num", "mfg part num", "mfg part no", "manufacturer_part_number",
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


def convert_to_csv(input_path: str | Path, output_csv_path: str | Path) -> Path:
    """Convert an .xlsx, .xls, or binary Excel/CSV file to standard CSV format.
    If the file is already a valid CSV, copies or returns it.
    """
    src = Path(input_path)
    dst = Path(output_csv_path)
    dst.parent.mkdir(parents=True, exist_ok=True)

    is_excel = src.suffix.lower() in (".xlsx", ".xls")
    if not is_excel and src.exists():
        try:
            with open(src, "rb") as f:
                header = f.read(4)
                if header.startswith(b"PK\x03\x04") or header.startswith(b"\xd0\xcf\x11\xe0"):
                    is_excel = True
        except Exception:
            pass

    if is_excel:
        logger.info("Converting Excel file %s to CSV at %s", src, dst)
        frame = pd.read_excel(src, dtype=str, keep_default_na=False)
        frame.to_csv(dst, index=False, encoding="utf-8")
    else:
        if src.resolve() != dst.resolve():
            import shutil
            shutil.copyfile(src, dst)
    return dst


def parse_input_workbook(path: str | Path, sheet_name: str | int = 0) -> ParseResult:
    """Parse an Unilog-style workbook into ProductRecord row candidates.

    Raises:
        FileNotFoundError: workbook does not exist.
        ValueError: unsupported extension, or missing required column.
    """
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"Input workbook not found: {source}")
    if source.suffix.lower() not in (".xlsx", ".xls", ".csv"):
        raise ValueError(f"Expected an .xlsx/.xls/.csv workbook, got {source.suffix!r}")

    if source.suffix.lower() == ".csv":
        frame = pd.read_csv(source, dtype=str, keep_default_na=False)
    else:
        frame = pd.read_excel(source, sheet_name=sheet_name, dtype=str, keep_default_na=False)
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
            if col not in header_map.values()
            for value in [row.get(col)]
            if value is not None and str(value).strip()
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


def parse_workbook_with_schema(path: str | Path, schema) -> ParseResult:
    """Parse a workbook using an ``InferredSchema`` (no hardcoded column names).

    ``schema`` is ``backend.schema_inference.infer.InferredSchema``. When it is
    missing manufacturer/part_number, we raise so the caller can fall back to
    the alias table.
    """
    from backend.schema_inference.infer import InferredSchema  # local to avoid cycles
    if not isinstance(schema, InferredSchema) or not (schema.manufacturer_col and schema.part_number_col):
        raise ValueError("inferred schema is missing manufacturer/part_number columns")

    source = Path(path)
    if source.suffix.lower() not in (".xlsx", ".xls", ".csv"):
        raise ValueError(f"Expected an .xlsx/.xls/.csv workbook, got {source.suffix!r}")
        
    if source.suffix.lower() == ".csv":
        frame = pd.read_csv(source, dtype=str)
    else:
        frame = pd.read_excel(source, sheet_name=0, dtype=str)

    mfr_col, pn_col = schema.manufacturer_col, schema.part_number_col
    attr_cols = [c for c in schema.attribute_cols if c in frame.columns]
    other_cols = [c for c in frame.columns if c not in (mfr_col, pn_col)]

    records: list[ProductRecord] = []
    skipped = 0
    seen: set[tuple[str, str]] = set()
    for _, row in frame.iterrows():
        manufacturer = str(row.get(mfr_col) or "").strip()
        part_number = str(row.get(pn_col) or "").strip()
        if not manufacturer or not part_number:
            skipped += 1
            continue
        key = (manufacturer.lower(), part_number.lower())
        if key in seen:
            continue
        seen.add(key)
        extras: dict[str, str] = {}
        for col in other_cols:
            value = row.get(col)
            if value is None:
                continue
            sval = str(value).strip()
            if sval:
                extras[str(col)] = sval
        records.append(ProductRecord(
            manufacturer=manufacturer, part_number=part_number, extras=extras,
        ))

    logger.info("Parsed %d unique products from %s via inferred schema (skip %d, attrs=%d)",
                len(records), source, skipped, sum(1 for _ in attr_cols) * 0 + len(attr_cols))
    return ParseResult(records=records, columns=list(frame.columns),
                       skipped_rows=skipped, source=source)


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