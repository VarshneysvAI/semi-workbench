"""Shared State Graph schema (api_contract.md, Day 2).

One graph per SKU: input provenance + ranked sources + extracted
candidates, plus the conflict/resolution ledger primitives shared by
``server.py``.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class Source(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str  # pdf | image | web | excel_input
    path: str
    page: int | None = None
    raw_text: str = ""
    source_url: str | None = None


class ExtractedCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    attribute: str
    value: str
    source_path: str
    page: int | None = None
    bbox: list[float] | None = None
    raw_extract: str = ""
    extractor: str = "regex"  # regex | llm | ocr | manual
    confidence: float = 0.0


class StateGraph(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sku: str
    manufacturer: str
    input_source_url: str | None = None
    sources: list[Source] = []
    extracted_candidates: list[ExtractedCandidate] = []


class ConflictSide(BaseModel):
    value: str
    source_path: str
    authority: float
    source_url: str | None = None


class Conflict(BaseModel):
    sku: str
    manufacturer: str
    attribute: str
    a: ConflictSide
    b: ConflictSide
    status: str = "open"  # open | resolved | refused


class LedgerRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sku: str
    manufacturer: str
    signature: str
    resolution: str
    note: str
    source_url: str | None
    changed_outcome: bool
    at: int
