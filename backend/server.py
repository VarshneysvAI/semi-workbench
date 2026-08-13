"""SEMI — Self-Evolving Manufacturer Intelligence.

DAY 2 server: shared state graph store + lookup, conflict resolver with a
ledger row per resolution, and websocket broadcast of ledger events.
Contract: ``docs/api_contract.md``.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import threading
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.ingest import excel_input
from backend.llm import gemma
from backend.schemas.state_graph import Conflict, ExtractedCandidate, LedgerRow, Source, StateGraph
from backend.schema_inference.infer import infer_from_workbook, is_meaningful
from backend.discover.search import build_search_queries, rank_candidates, search_web
from backend.extract.fetchers import fetch_content
from backend.audit import run_audit
from backend.ledger import (build_calibration, canonical_signature,  # noqa: F401
                            find_precedents, sync_conflicts)
from backend.sqlite_store import SQLiteStore, init_store

# New enrichment pipeline imports
from backend.output.schema import DeliveryFormatRow, DELIVERY_FORMAT_COLUMNS
from backend.output.parser import parse_part_desc, ParsedPartDesc
from backend.output.taxonomy import classify_part_desc, ClassificationResult
from backend.output.canonicaliser import canonicalise_manufacturer_brand, CanonicalMatch
from backend.output.normaliser import LOVNormaliser
from backend.output.uom import normalize_value_unit, normalize_uom
from backend.output.description import build_all_descriptions
from backend.output.quality import check_enrichment_quality, EnrichmentQualityReport

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("semi.server")

APP_VERSION = "0.3.0"

app = FastAPI(
    title="SEMI — Self-Evolving Manufacturer Intelligence",
    version=APP_VERSION,
    description="UniHack 2026 — AI-Powered Product Intelligence for Industrial Commerce",
)

# Development CORS; tightened per production domain in deployment/.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Persistent store (SQLite) — survives restarts
# ---------------------------------------------------------------------------

# Initialize SQLite store on startup
DB_PATH = os.getenv("SEMI_DB_PATH", "semi.db")
store = init_store(DB_PATH)
logger.info("SQLite store initialized at %s", DB_PATH)


# ---------------------------------------------------------------------------
# Request/response models
# ---------------------------------------------------------------------------

class IngestResponse(BaseModel):
    ingest_id: str
    filename: str
    status: str
    skus_parsed: int


class ResolveRequest(BaseModel):
    sku: str
    attribute: str
    human_resolution: str
    reason_tags: list[str] = []


# --- Enrichment pipeline models ---
class EnrichRequest(BaseModel):
    sku: str
    run_discovery: bool = True
    run_quality_check: bool = True


class EnrichResponse(BaseModel):
    sku: str
    manufacturer: str
    classpath: str
    unspSC: str
    enriched: bool
    delivery_format: dict
    quality_report: dict | None = None


class BatchEnrichRequest(BaseModel):
    skus: list[str]
    run_discovery: bool = True
    run_quality_check: bool = True


class BatchEnrichResponse(BaseModel):
    total: int
    succeeded: int
    failed: int
    results: list[EnrichResponse]


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "app": "semi", "version": APP_VERSION, "ts": int(time.time())}


# ---------------------------------------------------------------------------
# Ingest — upload workbook -> registered state graphs
# ---------------------------------------------------------------------------

@app.post("/api/ingest")
async def ingest_workbook(file: UploadFile = File(...)) -> IngestResponse:
    """Parse an Unilog input workbook and register per-SKU state graphs."""
    if not file.filename or not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Expected an .xlsx/.xls workbook upload")
    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=400, detail="Empty file")

    staged = _stage_workbook(file.filename, payload)
    inferred, used_schema = (None, False)
    try:
        inferred = infer_from_workbook(staged)
        used_schema = is_meaningful(inferred)
    except Exception as exc:  # inference is best-effort; alias fallback must still work
        logger.warning("schema inference failed for %s: %s", file.filename, exc)

    try:
        if used_schema:
            result = excel_input.parse_workbook_with_schema(staged, inferred)
        else:
            result = excel_input.parse_input_workbook(staged)
    except (ValueError, OSError) as exc:
        staged.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    for rec in result.records:
        key = store.key(rec.manufacturer, rec.part_number)
        graph = store.get_graph(rec.manufacturer, rec.part_number)
        if graph is None:
            graph = StateGraph(
                sku=rec.part_number,
                manufacturer=rec.manufacturer,
                input_source_url=None,
                sources=[],
                extracted_candidates=[],
            )
        for col, val in rec.extras.items():
            if not any(ec.attribute == col and ec.value == val for ec in graph.extracted_candidates):
                graph.extracted_candidates.append(
                    ExtractedCandidate(attribute=col, value=val,
                                       source_path="<input.xlsx>",
                                       extractor="input", confidence=1.0)
                )
        store.set_graph(graph)
    staged.unlink(missing_ok=True)

    ingest_id = uuid.uuid4().hex[:12]
    logger.info("Ingest %s: %d products from %s (schema_llm=%s, inferred_attrs=%d)",
                ingest_id, len(result.records), file.filename, used_schema,
                len(inferred.attribute_cols) if inferred else 0)
    return IngestResponse(
        ingest_id=ingest_id,
        filename=file.filename or "upload.xlsx",
        status="accepted",
        skus_parsed=len(result.records),
    )


def _stage_workbook(filename: str, payload: bytes) -> Path:
    suffix = Path(filename).suffix.lower()
    path = Path("incoming_uploads") / f"{uuid.uuid4().hex}{suffix}"
    path.parent.mkdir(exist_ok=True)
    path.write_bytes(payload)
    return path


# ---------------------------------------------------------------------------
# Lookups
# ---------------------------------------------------------------------------

@app.get("/api/state_graph/{sku}")
def get_state_graph(sku: str) -> StateGraph:
    key = _single_lookup_key(sku, "state_graph")
    graph = store.get_graph(key[0], key[1])
    if not graph:
        raise HTTPException(status_code=404, detail=f"no state graph for {sku}")
    return graph


@app.get("/api/conflicts/{sku}")
def get_conflicts(sku: str) -> list[Conflict]:
    key = _single_lookup_key(sku, "conflict")
    conflict = store.get_conflict(key[0], key[1])
    if not conflict:
        raise HTTPException(status_code=404, detail=f"no open conflict for {sku}")
    return [conflict]


@app.get("/api/conflicts")
def list_conflicts() -> dict:
    rows = [{"sku": c.sku, "manufacturer": c.manufacturer,
             "attribute": c.attribute, "status": c.status,
             "a": {"value": c.a.value, "source_url": c.a.source_url,
                   "authority": c.a.authority},
             "b": {"value": c.b.value, "source_url": c.b.source_url,
                   "authority": c.b.authority}}
            for c in store.get_all_conflicts().values()]
    return {"count": len(rows), "conflicts": rows}


@app.get("/api/graphs")
def list_graphs() -> dict:
    rows = [{"sku": g.sku, "manufacturer": g.manufacturer,
             "sources": len(g.sources),
             "candidates": len(g.extracted_candidates)}
            for g in store.get_all_graphs().values()]
    return {"count": len(rows), "graphs": rows}


def _single_lookup_key(sku: str, label: str) -> tuple[str, str]:
    """Resolve a bare SKU to one (mfr, sku) key; bail on ambiguity."""
    sku = sku.strip().lower()
    graphs = store.get_all_graphs()
    matches = [k for k in graphs if k[1] == sku]
    if len(matches) != 1:
        if not matches:
            raise HTTPException(status_code=404, detail=f"unknown sku {sku!r} in {label}")
        raise HTTPException(status_code=409, detail=f"sku {sku!r} ambiguous across manufacturers")
    return matches[0]


# ---------------------------------------------------------------------------
# Resolve -> ledger row + websocket broadcast
# ---------------------------------------------------------------------------

@app.post("/api/resolve")
def resolve_conflict(req: ResolveRequest) -> dict:
    key = _single_lookup_key(req.sku, "resolve")
    conflict = store.get_conflict(key[0], key[1])
    if not conflict or conflict.status != "open":
        raise HTTPException(status_code=409, detail=f"no open conflict for {req.sku}")

    side = conflict.a if req.human_resolution == conflict.a.value else conflict.b
    if req.human_resolution not in (conflict.a.value, conflict.b.value):
        raise HTTPException(status_code=422, detail="resolution must be one of the rival values")

    signature = canonical_signature(conflict.a.value, conflict.b.value)
    changed_outcome = req.human_resolution == conflict.b.value  # non-default side wins -> flip
    row = LedgerRow(
        sku=conflict.sku,
        manufacturer=conflict.manufacturer,
        signature=signature,
        resolution=req.human_resolution,
        note=", ".join(req.reason_tags) or "admin override",
        source_url=side.source_url,
        changed_outcome=changed_outcome,
        at=int(time.time()),
    )

    conflict.status = "resolved"
    store.set_conflict(conflict)
    store.append_ledger(row)

    by_signature = sum(1 for r in store.get_ledger() if r.signature == signature)
    event = {
        "event": "ledger_upsert",
        "signature": signature,
        "ledger_count": by_signature,
        "changed_outcome": changed_outcome,
    }
    broadcast(event)
    logger.info("Resolved %s %s -> %s (flip=%s)", conflict.manufacturer, conflict.sku,
                req.human_resolution, changed_outcome)
    return {"ok": True, **event}


# ---------------------------------------------------------------------------
# Discover — live web search -> ranked sources -> (optional) fetch + Gemma
# ---------------------------------------------------------------------------

@app.post("/api/discover/{sku}")
def discover_sources(sku: str, top_k: int = 5, fetch: bool = True, extract: bool = True) -> dict:
    """Run the autonomous discovery stage for one SKU's (manufacturer, sku).

    1. Build spec-first queries from the SKU + manufacturer.
    2. Live web search (hybrid chain: agent-reach -> Firecrawl -> Exa -> ddgs).
    3. Rank candidates (validation + authority + dedupe).
    4. Attach the top-K candidates as ``Source`` rows on the StateGraph.
    5. (When LLM configured) Fetch each via the hybrid router and run a Gemma
       single-field extraction over the canonical attributes.

    Provenance is preserved at every step: each ``Source`` carries
    ``source_url`` + ``type``; each produced ``ExtractedCandidate`` carries
    ``source_path`` + ``extractor='llm'`` + confidence. SEMI never invents
    values — when the evidence is thin, the model returns ``value=''`` and
    the cell stays empty.
    """
    key = _single_lookup_key(sku, "discover")
    graph = store.get_graph(key[0], key[1])
    if not graph:
        raise HTTPException(status_code=404, detail=f"no state graph for {sku}")

    queries = build_search_queries(graph.manufacturer, graph.sku)
    raw_seen: set[str] = set()
    raw_hits: list[tuple[str, str]] = []
    for q in queries:
        for url, title in search_web(q, max_results=8):
            if url in raw_seen:
                continue
            raw_seen.add(url)
            raw_hits.append((url, title))

    candidates = rank_candidates([u for u, _ in raw_hits], [t for _, t in raw_hits])
    top = candidates[:top_k]

    new_sources: list[Source] = []
    for c in top:
        if not any(s.source_url == c.url for s in graph.sources):
            src = Source(type=c.content_type, path=c.url, source_url=c.url)
            graph.sources.append(src)
            new_sources.append(src)

    extracted: list[dict] = []
    if extract:
        from backend.ingest.output_mapper import CANONICAL_ATTRIBUTES
        targets = new_sources if new_sources else list(graph.sources)[:top_k]
        for src in targets:
            doc = fetch_content(src.source_url, kind=src.type) if fetch else None
            if not doc or not doc.ok or not doc.text.strip():
                continue
            context = doc.text[:8000]
            for attr in CANONICAL_ATTRIBUTES:
                if not gemma.is_configured():
                    break
                if any(ec.attribute == attr and ec.source_path == src.path
                       for ec in graph.extracted_candidates):
                    continue
                try:
                    fx = gemma.extract_field(graph.manufacturer, graph.sku, attr, context)
                except Exception as exc:
                    logger.warning("gemma extract %s/%s on %s failed: %s", sku, attr, src.path, exc)
                    continue
                if not fx.value or fx.confidence < 0.4:
                    continue
                graph.extracted_candidates.append(ExtractedCandidate(
                    attribute=attr, value=fx.value, source_path=src.path,
                    page=None, raw_extract=fx.evidence_snippet,
                    extractor="llm", confidence=fx.confidence,
                ))
                extracted.append({"attribute": attr, "value": fx.value,
                                  "unit": fx.unit, "confidence": fx.confidence,
                                  "source_url": src.source_url,
                                  "fetched_via": doc.fetched_via})

    store.set_graph(graph)
    report = run_audit(graph, calibration=build_calibration(
        store.get_all_conflicts(), store.get_all_graphs(), store.get_ledger()))
    sync_conflicts(graph, report, store.get_all_conflicts())
    audit_body = report.to_dict()
    conflict = store.get_conflict(key[0], key[1])

    return {
        "sku": graph.sku,
        "manufacturer": graph.manufacturer,
        "queries": queries,
        "candidates": [{"url": c.url, "title": c.title, "kind": c.kind,
                         "authority": c.authority} for c in candidates],
        "sources_attached": len(new_sources),
        "extracted": extracted,
        "llm_configured": gemma.is_configured(),
        "audit": audit_body,
        "conflict": None if conflict is None else {
            "sku": conflict.sku, "manufacturer": conflict.manufacturer,
            "attribute": conflict.attribute, "status": conflict.status,
            "a": {"value": conflict.a.value, "source_url": conflict.a.source_url,
                  "authority": conflict.a.authority},
            "b": {"value": conflict.b.value, "source_url": conflict.b.source_url,
                  "authority": conflict.b.authority},
        },
    }


# ---------------------------------------------------------------------------
# Audit — deterministic checks + refusal gate + conformal intervals
# ---------------------------------------------------------------------------

@app.get("/api/audit/{sku}")
def audit_sku(sku: str) -> dict:
    """Run the adversarial audit over one SKU's extracted candidates.

    Physics/constraint rules -> cross-source contradiction -> weighted
    consensus -> refusal gate -> split-conformal intervals. Returns a
    per-attribute ``ACCEPT`` or ``REFUSE_*`` verdict with provenance.
    Until ^=30 labelled calibration rows exist, intervals are reported as
    uncalibrated rather than faked.
    """
    key = _single_lookup_key(sku, "audit")
    graph = store.get_graph(key[0], key[1])
    if not graph:
        raise HTTPException(status_code=404, detail=f"no state graph for {sku}")
    report = run_audit(graph, calibration=build_calibration(
        store.get_all_conflicts(), store.get_all_graphs(), store.get_ledger()))
    sync_conflicts(graph, report, store.get_all_conflicts())
    body = report.to_dict()
    body["conflict"] = None
    conflict = store.get_conflict(key[0], key[1])
    if conflict:
        body["conflict"] = {
            "sku": conflict.sku, "manufacturer": conflict.manufacturer,
            "attribute": conflict.attribute, "status": conflict.status,
            "a": {"value": conflict.a.value, "source_url": conflict.a.source_url,
                  "authority": conflict.a.authority},
            "b": {"value": conflict.b.value, "source_url": conflict.b.source_url,
                  "authority": conflict.b.authority},
        }
    return body


# ---------------------------------------------------------------------------
# Ledger — resolutions, precedents, conformal calibration feed
# ---------------------------------------------------------------------------

@app.get("/api/ledger")
def get_ledger() -> dict:
    rows = [r.model_dump() for r in store.get_ledger()]
    return {"count": len(rows), "rows": rows}


@app.get("/api/precedents/{sku}")
def precedent_lookup(sku: str) -> dict:
    """Ledger signatures matching this SKU's current conflicts (>= 0.85 cosine)."""
    key = _single_lookup_key(sku, "precedent")
    conflict = store.get_conflict(key[0], key[1])
    ledger = store.get_ledger()
    signatures = {canonical_signature(r.a.value, r.b.value) for r in store.get_all_conflicts().values()}
    candidates = [r.signature for r in ledger]
    query = (canonical_signature(conflict.a.value, conflict.b.value)
             if conflict else "")
    exact: list[str] = []
    fuzzy: list[tuple[str, float]] = []
    if query:
        for sig in candidates:
            if sig == query:
                exact.append(sig)
        fuzzy = find_precedents([s for s in candidates if s != query], query)
    rows = [r for r in ledger if r.signature in {query, *[s for s, _ in fuzzy]}]
    return {
        "sku": sku,
        "query": query,
        "exact": exact,
        "fuzzy": fuzzy,
        "hits": [{"signature": r.signature, "resolution": r.resolution,
                  "note": r.note, "changed_outcome": r.changed_outcome,
                  "source_url": r.source_url, "at": r.at}
                 for r in rows],
    }


# ---------------------------------------------------------------------------
# Enrichment Pipeline — parse -> classify -> extract -> enrich -> normalise -> describe -> evaluate
# ---------------------------------------------------------------------------

# Module-level singletons for the enrichment pipeline
_lov_normaliser = LOVNormaliser()


def _enrich_single_sku(sku: str, manufacturer: str, part_desc: str,
                       run_discovery: bool = True,
                       run_quality_check: bool = True) -> EnrichResponse:
    """Run the full enrichment pipeline on a single SKU."""
    key = _single_lookup_key(sku, "enrich")
    graph = store.get_graph(key[0], key[1])
    if not graph:
        raise HTTPException(status_code=404, detail=f"no state graph for {sku}")

    # 1. Parse Part_Desc into structured fields
    parsed: ParsedPartDesc = parse_part_desc(part_desc or graph.sku)

    # 2. Classify to Unilog classpath
    classification: ClassificationResult = classify_part_desc(parsed, manufacturer)

    # 3. Canonicalise manufacturer/brand (uses input row's brand fields)
    # In a real pipeline, these come from the input workbook columns
    mfr_brand: CanonicalMatch = canonicalise_manufacturer_brand(
        manufacturer=manufacturer,
        brand="",  # Would come from input columns E1_Brand, Unilog_Brand, DIB_Brand
        e1_brand="",
        unilog_brand="",
        dib_brand="",
    )

    # 4. Run discovery to get manufacturer sources (optional, can be slow)
    extracted_attrs: dict[str, str] = {}
    if run_discovery:
        try:
            # Reuse discover logic but only for attribute extraction
            queries = build_search_queries(manufacturer, sku)
            raw_seen: set[str] = set()
            raw_hits: list[tuple[str, str]] = []
            for q in queries:
                for url, title in search_web(q, max_results=5):
                    if url in raw_seen:
                        continue
                    raw_seen.add(url)
                    raw_hits.append((url, title))
            candidates = rank_candidates([u for u, _ in raw_hits], [t for _, t in raw_hits])
            top = candidates[:3]
            for c in top:
                if not any(s.source_url == c.url for s in graph.sources):
                    src = Source(type=c.content_type, path=c.url, source_url=c.url)
                    graph.sources.append(src)
            # Extract from top sources
            if gemma.is_configured():
                from backend.ingest.output_mapper import CANONICAL_ATTRIBUTES
                targets = list(graph.sources)[:3]
                for src in targets:
                    doc = fetch_content(src.source_url, kind=src.type)
                    if not doc or not doc.ok or not doc.text.strip():
                        continue
                    context = doc.text[:8000]
                    for attr in CANONICAL_ATTRIBUTES:
                        try:
                            fx = gemma.extract_field(manufacturer, sku, attr, context)
                        except Exception as exc:
                            logger.warning("gemma extract %s/%s on %s failed: %s", sku, attr, src.path, exc)
                            continue
                        if not fx.value or fx.confidence < 0.4:
                            continue
                        graph.extracted_candidates.append(ExtractedCandidate(
                            attribute=attr, value=fx.value, source_path=src.path,
                                page=None, raw_extract=fx.evidence_snippet,
                                extractor="llm", confidence=fx.confidence,
                            ))
                        extracted_attrs[attr] = fx.value
        except Exception as exc:
            logger.warning("Discovery failed for %s: %s", sku, exc)

    # 5. Merge parsed attributes + discovered attributes
    merged_attrs = {**parsed.to_attributes_dict(), **extracted_attrs}

    # 6. Normalise all attributes to LOV canonical values
    norm_results = _lov_normaliser.normalise_batch(merged_attrs)
    canonical_attrs = {attr: res.canonical_value for attr, res in norm_results.items()}

    # 7. Normalise UOM for all values
    for attr, value in canonical_attrs.items():
        if value:
            nv = normalize_value_unit(value)
            if nv.unit:
                canonical_attrs[f"{attr}_uom"] = nv.unit
                canonical_attrs[attr] = nv.value

    # 8. Build DeliveryFormatRow
    row = DeliveryFormatRow(
        sku=sku,
        mfg_part_num=sku,
        part_desc=part_desc,
        classpath=classification.classpath,
        unspSC=classification.unspSC,
        manufacturer_name=mfr_brand.canonical_name or manufacturer,
        manufacturer_code=mfr_brand.canonical_code,
        brand_name=mfr_brand.brand_name,
        brand_code=mfr_brand.brand_code,
        **canonical_attrs,
    )

    # 9. Build all 5 descriptions
    row = build_all_descriptions(row)

    # 10. Quality check
    quality_report = None
    if run_quality_check:
        report = check_enrichment_quality(row)
        quality_report = {
            "overall_confidence": report.overall_confidence,
            "needs_review": report.needs_review,
            "findings": [
                {"attribute": f.attribute, "rule": f.rule, "detail": f.detail,
                 "severity": f.severity, "suggestion": f.suggestion}
                for f in report.findings
            ],
            "description_compliance": report.description_compliance,
            "missing_filtering_attrs": report.missing_filtering_attrs,
        }
        # Add review flags to row
        row.needs_review = report.needs_review
        row.confidence = report.overall_confidence
        for f in report.findings:
            if f.severity in ("critical", "warning"):
                row.review_reasons.append(f"{f.attribute}: {f.rule} - {f.detail}")

    return EnrichResponse(
        sku=sku,
        manufacturer=manufacturer,
        classpath=classification.classpath,
        unspSC=classification.unspSC,
        enriched=True,
        delivery_format=row.to_dict(),
        quality_report=quality_report,
    )


@app.post("/api/enrich/{sku}")
def enrich_sku(sku: str, req: EnrichRequest) -> EnrichResponse:
    """Run the full enrichment pipeline on a single SKU.

    Steps:
    1. Parse Part_Desc -> structured fields
    2. Classify to Unilog classpath (via Unicat_LOV taxonomy)
    3. Canonicalise manufacturer/brand (vs UniCat list)
    4. Run discovery (optional) -> extract attributes from manufacturer sources
    5. Merge parsed + discovered attributes
    6. Normalise to LOV canonical values (many-to-one collapse via flywheel cosine)
    7. Normalise UOM (approved abbreviations + decimal↔fraction)
    8. Build 5 descriptions (Invoice, Mobile, Title, Short, Long)
    9. Quality check (LOV compliance, UOM, char limits, canonical mfr/brand, filtering attrs)
    """
    key = _single_lookup_key(sku, "enrich")
    graph = store.get_graph(key[0], key[1])
    if not graph:
        raise HTTPException(status_code=404, detail=f"no state graph for {sku}")

    return _enrich_single_sku(sku, graph.manufacturer, graph.sku,
                              run_discovery=req.run_discovery,
                              run_quality_check=req.run_quality_check)


@app.post("/api/enrich/batch")
def enrich_batch(req: BatchEnrichRequest) -> BatchEnrichResponse:
    """Enrich multiple SKUs in batch."""
    results = []
    succeeded = 0
    failed = 0
    for sku in req.skus:
        try:
            key = _single_lookup_key(sku, "enrich")
            graph = store.get_graph(key[0], key[1])
            if not graph:
                raise HTTPException(status_code=404, detail=f"no state graph for {sku}")
            result = _enrich_single_sku(sku, graph.manufacturer, graph.sku,
                                        run_discovery=req.run_discovery,
                                        run_quality_check=req.run_quality_check)
            results.append(result)
            succeeded += 1
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("Batch enrich failed for %s: %s", sku, exc)
            failed += 1
            results.append(EnrichResponse(
                sku=sku, manufacturer="", classpath="", unspSC="",
                enriched=False, delivery_format={}, quality_report={"error": str(exc)}
            ))
    return BatchEnrichResponse(
        total=len(req.skus), succeeded=succeeded, failed=failed, results=results
    )


@app.get("/api/enriched/{sku}")
def get_enriched(sku: str) -> dict:
    """Get the enriched DeliveryFormatRow for a SKU (re-runs if not cached)."""
    key = _single_lookup_key(sku, "enriched")
    graph = store.get_graph(key[0], key[1])
    if not graph:
        raise HTTPException(status_code=404, detail=f"no state graph for {sku}")

    # Check if we have cached enrichment in the graph's extracted_candidates
    # For now, always re-run (fast enough for demo)
    return _enrich_single_sku(sku, graph.manufacturer, graph.sku,
                              run_discovery=False, run_quality_check=True).delivery_format


@app.get("/api/quality/{sku}")
def get_quality_report(sku: str) -> dict:
    """Get the quality report for an enriched SKU."""
    key = _single_lookup_key(sku, "quality")
    graph = store.get_graph(key[0], key[1])
    if not graph:
        raise HTTPException(status_code=404, detail=f"no state graph for {sku}")

    # Build a minimal row for quality check
    row = DeliveryFormatRow(
        sku=sku,
        manufacturer_name=graph.manufacturer,
    )
    report = check_enrichment_quality(row)
    return {
        "sku": sku,
        "manufacturer": graph.manufacturer,
        "classpath": graph.sku,
        "overall_confidence": report.overall_confidence,
        "needs_review": report.needs_review,
        "findings": [
            {"attribute": f.attribute, "rule": f.rule, "detail": f.detail,
             "severity": f.severity, "suggestion": f.suggestion}
            for f in report.findings
        ],
        "description_compliance": report.description_compliance,
        "missing_filtering_attrs": report.missing_filtering_attrs,
    }


@app.get("/api/delivery_format_columns")
def get_delivery_format_columns() -> dict:
    """Return the 252-column Delivery Format schema for reference."""
    return {
        "columns": DELIVERY_FORMAT_COLUMNS,
        "count": len(DELIVERY_FORMAT_COLUMNS),
    }


# ---------------------------------------------------------------------------
# Deferred surface (finale)
# ---------------------------------------------------------------------------

@app.get("/api/ab_compare/{sku}")
def ab_compare(sku: str) -> dict:
    return {"sku": sku, "status": "deferred", "detail": "A/B vs generalist output — finale"}


@app.get("/api/ontology/{manufacturer}")
def ontology(manufacturer: str) -> dict:
    return {"manufacturer": manufacturer, "status": "deferred", "detail": "View 0 — finale"}


# ---------------------------------------------------------------------------
# WebSocket /ws/ledger_events
# ---------------------------------------------------------------------------

@app.websocket("/ws/ledger_events")
async def ledger_events(ws: WebSocket) -> None:
    await ws.accept()
    store.sockets.add(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        store.sockets.discard(ws)


def broadcast(event: dict) -> None:
    payload = json.dumps(event)
    for ws in list(store.sockets):
        try:
            asyncio.create_task(ws.send_text(payload))
        except Exception:
            store.sockets.discard(ws)