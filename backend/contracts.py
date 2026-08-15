"""SEMI — Core Contracts

Single source of truth for all agent I/O schemas.
Every model uses Pydantic v2 with extra='forbid' for strict validation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ──────────────────────────────────────────────
# UNIVERSAL ENVELOPE — every agent output uses this
# ──────────────────────────────────────────────
class AgentError(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    code: str
    message: str
    details: dict[str, Any] | None = None


class AgentOutput(BaseModel):
    """Universal envelope — validated at EVERY handoff.
    status='ok' ↔ data present. otherwise → error present.
    """
    model_config = ConfigDict(extra="forbid", strict=True)

    status: Literal["ok", "unknown", "error"]
    data: dict[str, Any] | None = None
    error: AgentError | None = None
    schema_version: str = "1.0.0"

    @model_validator(mode="after")
    def _xor(self) -> "AgentOutput":
        if self.status == "ok":
            if self.data is None:
                raise ValueError("ok requires data")
            if self.error is not None:
                raise ValueError("ok forbids error")
        else:
            if self.error is None:
                raise ValueError("error/unknown requires error")
        return self


# ──────────────────────────────────────────────
# SCHEMA INFERENCE — file → domain + attribute blueprint
# ──────────────────────────────────────────────
class SchemaInferInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    file_path: Path
    sample_rows: list[dict[str, Any]]  # first 20 rows
    column_stats: dict[str, dict[str, Any]]  # {col: {type, uniq, nulls, placeholder_pct, samples}}


class ColumnRole(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    name: str
    role: Literal["sku", "description", "manufacturer", "brand_candidate", "ignore"]
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str


class AttributeBlueprint(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    name: str
    type: Literal["string", "number", "enum", "quantity_uom"]
    required: bool
    enum_values: list[str] | None = None
    uom_candidates: list[str] | None = None
    source_hint: str  # e.g., "description", "web search manufacturer PN"


class SchemaPlan(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    domain: str
    product_kind: str
    columns: list[ColumnRole]
    attributes: list[AttributeBlueprint]
    needs_human: bool
    human_questions: list[str] = []

    @field_validator("columns")
    @classmethod
    def _has_sku(cls, v: list[ColumnRole]) -> list[ColumnRole]:
        skus = [c for c in v if c.role == "sku"]
        if len(skus) != 1:
            raise ValueError(f"must have exactly one sku column, got {len(skus)}")
        return v


class SchemaInferOutput(AgentOutput):
    data: SchemaPlan | None = None


# ──────────────────────────────────────────────
# WEB EXTRACTION — search → fetch → LLM extract + citations
# ──────────────────────────────────────────────
class ExtractInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    sku: str
    manufacturer: str
    part_number: str
    description: str = ""
    remaining_attributes: list[str]  # what we still need
    schema_plan: SchemaPlan


class CitedValue(BaseModel):
    """ONE extracted value with full provenance."""
    model_config = ConfigDict(extra="forbid", strict=True)

    attribute: str
    value: str
    unit: str | None
    confidence: float = Field(ge=0.0, le=1.0)
    source_url: str = Field(pattern=r"^https?://")
    evidence_snippet: str = Field(min_length=10, max_length=500)
    extractor: Literal[
        "crawl4ai",
        "pdf_reader_mcp",
        "firecrawl_parse",
        "firecrawl_scrape",
        "youtube_transcript",
        "kb_hit",
    ]
    schema_version: str = "1.0.0"

    @field_validator("evidence_snippet")
    @classmethod
    def _snippet_not_empty(cls, v: str) -> str:
        if len(v.strip()) < 10:
            raise ValueError("evidence snippet too short")
        return v.strip()


class WebExtractResult(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    cited_values: list[CitedValue]
    failed_attributes: list[str]


class WebExtractOutput(AgentOutput):
    data: WebExtractResult | None = None


# ──────────────────────────────────────────────
# TWO-PASS NORMALIZATION
# ──────────────────────────────────────────────
class RawExtraction(BaseModel):
    """Raw extraction before normalization."""
    model_config = ConfigDict(extra="forbid", strict=True)
    raw_label: str
    value: str
    unit: str | None
    confidence: float = Field(ge=0.0, le=1.0)
    source_url: str
    evidence_snippet: str
    extractor: str


class CanonicalAttribute(BaseModel):
    """Normalized attribute after two-pass normalization."""
    model_config = ConfigDict(extra="forbid", strict=True)
    canonical_key: str
    canonical_value: str
    canonical_unit: str
    confidence: float = Field(ge=0.0, le=1.0)
    source_url: str
    precedence_rank: int  # 1=spec sheet, 2=html, 3=manual, 4=distributor, 5=third-party
    raw_variants: list[RawExtraction]


class NormalizeInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    sku: str
    raw_extractions: list[RawExtraction]
    schema_plan: SchemaPlan


class NormalizeOutput(AgentOutput):
    data: list[CanonicalAttribute] | None = None


# ──────────────────────────────────────────────
# ADVERSARIAL AUDIT — 5 checks + conformal CI
# ──────────────────────────────────────────────
class AuditCheck(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    name: Literal[
        "physical_rules",
        "cross_source_contradiction",
        "compositional_curve",
        "disproof_search",
        "conformal_ci",
    ]
    passed: bool
    details: str
    lo: float | None = None
    hi: float | None = None


class AuditVerdict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    consensus_score: float = Field(ge=0.0, le=1.0)
    checks: list[AuditCheck]
    decision: Literal["pass", "insufficient_evidence"]
    insufficient_attributes: list[str] = []


class AuditInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    sku: str
    canonical_attributes: list[CanonicalAttribute]
    schema_plan: SchemaPlan


class AuditOutput(AgentOutput):
    data: AuditVerdict | None = None


# ──────────────────────────────────────────────
# ASSEMBLY → 252-COL DELIVERY ROW
# ──────────────────────────────────────────────
class AssembleInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    sku: str
    audit_verdict: AuditVerdict
    canonical_attributes: list[CanonicalAttribute]
    schema_plan: SchemaPlan


class DeliveryRow(BaseModel):
    """Matches Unilog Delivery Format exactly (252 columns)."""
    model_config = ConfigDict(extra="forbid", strict=True, populate_by_name=True)

    # Identification
    sku: str = Field(max_length=50)
    mfg_part_num: str = Field(max_length=100)
    part_desc: str = Field(max_length=500)

    # Classification
    dept: str = Field(max_length=100)
    class_: str = Field(max_length=100, alias="class")
    fine: str = Field(max_length=100)
    classpath: str = Field(max_length=300)
    unspSC: str = Field(max_length=20, default="")

    # Manufacturer / Brand
    manufacturer_name: str = Field(max_length=200)
    manufacturer_code: str = Field(max_length=50, default="")
    brand_name: str = Field(max_length=200)
    brand_code: str = Field(max_length=50, default="")
    e1_brand: str = Field(max_length=200, default="")
    unilog_brand: str = Field(max_length=200, default="")
    dib_brand: str = Field(max_length=200, default="")

    # 5 Description fields
    invoice_desc: str = Field(max_length=40)  # ALL CAPS
    mobile_desc: str = Field(min_length=60, max_length=80)
    product_title: str = Field(max_length=200)
    short_desc: str = Field(max_length=500)
    long_desc: str = Field(max_length=4000)

    # Additional
    marketing_copy: str = Field(default="")
    bullet_points: str = Field(default="")

    # 47 ATTRIBUTE_LABEL/VALUE/UOM triplets (dynamic keys)
    # These are populated dynamically from canonical_attributes
    # We store them as flat fields for the 252-col output
    attr_labels: dict[str, str] = Field(default_factory=dict)  # canonical_key → label
    attr_values: dict[str, str] = Field(default_factory=dict)  # canonical_key → value
    attr_uoms: dict[str, str] = Field(default_factory=dict)    # canonical_key → unit

    # Identifiers
    upc: str = Field(default="")
    ean: str = Field(default="")
    gtin: str = Field(default="")
    unspSC_code: str = Field(default="", alias="unspSC")
    warranty: str = Field(default="")
    list_price: str = Field(default="")
    selling_qty: str = Field(default="")
    selling_uom: str = Field(default="")
    std_packaging: str = Field(default="")

    # Dimensions
    length: str = Field(default="")
    length_uom: str = Field(default="")
    height: str = Field(default="")
    height_uom: str = Field(default="")
    width: str = Field(default="")
    width_uom: str = Field(default="")
    weight: str = Field(default="")
    weight_uom: str = Field(default="")
    volume: str = Field(default="")
    volume_uom: str = Field(default="")

    # Media / Docs
    product_image: str = Field(default="")
    alt_image_1: str = Field(default="")
    alt_image_2: str = Field(default="")
    alt_image_3: str = Field(default="")
    alt_image_4: str = Field(default="")
    sds: str = Field(default="")
    sds_1: str = Field(default="")
    warranty_info: str = Field(default="")
    catalog: str = Field(default="")
    spec_sheet: str = Field(default="")
    instruction_manual: str = Field(default="")
    service_manual: str = Field(default="")
    owners_manual: str = Field(default="")
    line_drawing: str = Field(default="")
    mtr: str = Field(default="")
    rohs: str = Field(default="")
    full_eng_drawing: str = Field(default="")
    energy_star: str = Field(default="")
    tech_bulletin: str = Field(default="")
    submittal: str = Field(default="")
    compat_chart: str = Field(default="")
    size_chart: str = Field(default="")
    product_label: str = Field(default="")
    video_link: str = Field(default="")
    video_link_1: str = Field(default="")
    country_of_origin: str = Field(default="")
    discontinued: str = Field(default="")
    actual_image: str = Field(default="")

    # Provenance (internal, not in 252-col output)
    mfr_url: str = Field(default="")
    ref_urls: list[str] = Field(default_factory=list)
    source_attributes: dict[str, dict[str, Any]] = Field(default_factory=dict)


class AssembleOutput(AgentOutput):
    data: DeliveryRow | None = None


# ──────────────────────────────────────────────
# LEDGER / FLYWHEEL
# ──────────────────────────────────────────────
class LedgerInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    sku: str
    canonical_attributes: list[CanonicalAttribute]
    audit_verdict: AuditVerdict
    delivery_row: DeliveryRow
    run_id: str


class LedgerOutput(AgentOutput):
    data: dict[str, Any] | None = None  # {canonical_id, ledger_rows_written}


class HumanResolutionInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    sku: str
    attribute: str
    old_value: str
    new_value: str
    source_url: str
    reason: str
    changed_outcome: bool = True


class HumanResolutionOutput(AgentOutput):
    data: dict[str, Any] | None = None


# ──────────────────────────────────────────────
# PRECEDENT KB
# ──────────────────────────────────────────────
class PrecedentQuery(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    manufacturer: str
    normalized_specs: dict[str, str]  # canonical_key → canonical_value
    mpn: str | None = None


class PrecedentHit(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    canonical_id: str
    sku: str
    similarity: float
    canonical_attributes: list[CanonicalAttribute]
    run_id: str
    timestamp: str