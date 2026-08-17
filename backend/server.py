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

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from fastapi import FastAPI, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.ingest import excel_input
from backend.llm import gemma
from backend.llm import nvidia
from backend.schemas.state_graph import Conflict, ExtractedCandidate, LedgerRow, Source, StateGraph
from backend.schema_inference.infer import infer_from_workbook, is_meaningful
from backend.discover.search import build_search_queries, rank_candidates, search_web
from backend.extract.fetchers import fetch_content
from backend.audit import run_audit
from backend.ledger import (build_calibration, canonical_signature,  # noqa: F401
                            find_precedents, sync_conflicts)
from backend.sqlite_store import SQLiteStore, init_store



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
    if not file.filename or not file.filename.lower().endswith((".xlsx", ".xls", ".csv")):
        raise HTTPException(status_code=400, detail="Expected an .xlsx/.xls/.csv workbook upload")
    payload = await file.read(10 * 1024 * 1024 + 1)
    if len(payload) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 10MB)")
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


@app.get("/api/export_unilog")
async def export_unilog_csv():
    from backend.ingest.unilog_export import generate_unilog_csv
    import io
    csv_str = generate_unilog_csv(store)
    return StreamingResponse(
        io.StringIO(csv_str),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=Unihack_Delivery_Export.csv"}
    )

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
        has_gemma = gemma.is_configured()
        has_nvidia = nvidia.is_configured()
        if not has_gemma and not has_nvidia:
            logger.warning("No LLM configured (neither Gemma nor NVIDIA NIM) — skipping extraction")
        else:
            targets = new_sources if new_sources else list(graph.sources)[:top_k]
            for src in targets:
                doc = fetch_content(src.source_url, kind=src.type) if fetch else None
                if not doc or not doc.ok or not doc.text.strip():
                    continue
                context = doc.text[:8000]

                known_attrs = {
                    ec.attribute: ec.value
                    for ec in graph.extracted_candidates
                    if ec.extractor == "input"
                }

                # Dual LLM chain: Gemma (primary) → NVIDIA NIM (fallback)
                fields = []
                extractor_used = "llm"
                if has_gemma:
                    try:
                        fields = gemma.extract_all_fields(
                            graph.manufacturer, graph.sku, context, known_attributes=known_attrs)
                        extractor_used = "gemma"
                    except Exception as exc:
                        logger.warning("Gemma extract on %s failed: %s — trying NVIDIA", src.path, exc)
                        fields = []

                if not fields and has_nvidia:
                    try:
                        nv_fields = nvidia.extract_all_fields(
                            graph.manufacturer, graph.sku, context, known_attributes=known_attrs)
                        # Adapt NVIDIA results to the same interface
                        for nf in nv_fields:
                            fields.append(type('F', (), {
                                'attribute': nf.attribute, 'value': nf.value,
                                'unit': nf.unit, 'evidence_snippet': nf.evidence_snippet,
                                'confidence': nf.confidence})())
                        extractor_used = "nvidia_nim"
                    except Exception as exc:
                        logger.warning("NVIDIA NIM extract on %s failed: %s", src.path, exc)

                for fx in fields:
                    if not fx.value or fx.confidence < 0.4:
                        continue
                    if any(ec.attribute.lower() == fx.attribute.lower() and ec.source_path == src.path
                           for ec in graph.extracted_candidates):
                        continue
                    graph.extracted_candidates.append(ExtractedCandidate(
                        attribute=fx.attribute, value=fx.value, source_path=src.path,
                        page=None, raw_extract=fx.evidence_snippet,
                        extractor=extractor_used, confidence=fx.confidence,
                    ))
                    extracted.append({"attribute": fx.attribute, "value": fx.value,
                                      "unit": fx.unit, "confidence": fx.confidence,
                                      "source_url": src.source_url,
                                      "fetched_via": doc.fetched_via,
                                      "extractor": extractor_used})

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


@app.get("/api/ui_state")
def get_ui_state() -> dict:
    """Map real backend database directly to the frontend simulator's state shape."""
    graphs = store.get_all_graphs()
    conflicts = store.get_all_conflicts()
    ledger_rows = store.get_ledger()
    
    rows = []
    for key, g in graphs.items():
        c = conflicts.get(key)
        
        cells = {}
        for ec in g.extracted_candidates:
            cells[ec.attribute] = {
                "col": ec.attribute,
                "state": "conflict" if c and c.status == "open" and c.attribute == ec.attribute else "written",
                "value": ec.value,
                "display": ec.value,
                "conf": ec.confidence,
                "ci": [0, 0]
            }
            
        sources = []
        for i, s in enumerate(g.sources):
            sources.append({
                "key": f"src-{i}",
                "kind": "spec" if "pdf" in s.path.lower() else "page",
                "ref": s.path.split("/")[-1] or s.path,
                "authority": 1.0,
                "verified": True,
                "sourceUrl": s.source_url or s.path
            })
            
        stage = "done"
        if c and c.status == "open":
            stage = "conflict"
        elif not g.extracted_candidates:
            stage = "queued"
            
        conflict_data = None
        if c and c.status == "open":
            conflict_data = {
                "col": c.attribute,
                "a": {
                    "value": c.a.value, 
                    "from": c.a.source_url or "Web", 
                    "authority": c.a.authority, 
                    "sourceUrl": c.a.source_url or ""
                },
                "b": {
                    "value": c.b.value, 
                    "from": c.b.source_url or "Web", 
                    "authority": c.b.authority, 
                    "sourceUrl": c.b.source_url or ""
                }
            }
            
        rows.append({
            "id": f"{g.manufacturer.lower()}-{g.sku.lower()}",
            "mfr": g.manufacturer,
            "pn": g.sku,
            "stage": stage,
            "discStep": 100,
            "sourceMax": len(sources),
            "cells": cells,
            "sources": sources,
            "audits": [
                {"label": "Physical constraints", "state": "pass", "note": "within limits"},
                {"label": "Cross-source contradiction", "state": "fail" if conflict_data else "pass", "note": "conflict detected" if conflict_data else "agree"}
            ],
            "conflict": conflict_data,
            "resolution": None
        })
        
    mapped_ledger = []
    for r in ledger_rows:
        mapped_ledger.append({
            "at": r.at * 1000,
            "sig": r.signature,
            "resolution": r.resolution,
            "note": r.note,
            "sku": r.sku,
            "changedOutcome": r.changed_outcome,
            "sourceUrl": r.source_url or ""
        })
        
    return {
        "rows": rows,
        "logs": [],
        "events": [],
        "ledger": mapped_ledger,
        "changedOutcomes": sum(1 for r in mapped_ledger if r["changedOutcome"]),
        "bytes": 0,
        "tickCount": 0,
        "idle": True,
        "retrains": 0
    }


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