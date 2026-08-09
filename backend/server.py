"""SEMI — Self-Evolving Manufacturer Intelligence.

DAY 2 server: shared state graph store + lookup, conflict resolver with a
ledger row per resolution, and websocket broadcast of ledger events.
Contract: ``docs/api_contract.md``.
"""

from __future__ import annotations

import asyncio
import json
import logging
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

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("semi.server")

APP_VERSION = "0.2.0"

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
# In-memory store (Day 2; SQLite persistence lands with classifiers, Day 9)
# ---------------------------------------------------------------------------

class Store:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.graphs: dict[tuple[str, str], StateGraph] = {}
        self.conflicts: dict[tuple[str, str], Conflict] = {}
        self.ledger: list[LedgerRow] = []
        self.sockets: set[WebSocket] = set()

    @staticmethod
    def key(manufacturer: str, sku: str) -> tuple[str, str]:
        return manufacturer.strip().lower(), sku.strip().lower()


store = Store()


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

    with store._lock:
        for rec in result.records:
            key = store.key(rec.manufacturer, rec.part_number)
            graph = store.graphs.setdefault(
                key,
                StateGraph(
                    sku=rec.part_number,
                    manufacturer=rec.manufacturer,
                    input_source_url=None,
                    sources=[],
                    extracted_candidates=[],
                ),
            )
            for col, val in rec.extras.items():
                if not any(ec.attribute == col and ec.value == val for ec in graph.extracted_candidates):
                    graph.extracted_candidates.append(
                        ExtractedCandidate(attribute=col, value=val,
                                           source_path="<input.xlsx>",
                                           extractor="input", confidence=1.0)
                    )
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
    with store._lock:
        graph = store.graphs.get(key)
    if not graph:
        raise HTTPException(status_code=404, detail=f"no state graph for {sku}")
    return graph


@app.get("/api/conflicts/{sku}")
def get_conflicts(sku: str) -> list[Conflict]:
    key = _single_lookup_key(sku, "conflict")
    with store._lock:
        conflict = store.conflicts.get(key)
    if not conflict:
        raise HTTPException(status_code=404, detail=f"no open conflict for {sku}")
    return [conflict]


def _single_lookup_key(sku: str, label: str) -> tuple[str, str]:
    """Resolve a bare SKU to one (mfr, sku) key; bail on ambiguity."""
    sku = sku.strip().lower()
    with store._lock:
        matches = [k for k in store.graphs if k[1] == sku]
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
    with store._lock:
        conflict = store.conflicts.get(key)
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

    with store._lock:
        conflict.status = "resolved"
        store.ledger.append(row)

    by_signature = sum(1 for r in store.ledger if r.signature == signature)
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
    with store._lock:
        graph = store.graphs.get(key)
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
    with store._lock:
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
                with store._lock:
                    graph.extracted_candidates.append(ExtractedCandidate(
                        attribute=attr, value=fx.value, source_path=src.path,
                        page=None, raw_extract=fx.evidence_snippet,
                        extractor="llm", confidence=fx.confidence,
                    ))
                extracted.append({"attribute": attr, "value": fx.value,
                                  "unit": fx.unit, "confidence": fx.confidence,
                                  "source_url": src.source_url,
                                  "fetched_via": doc.fetched_via})

    with store._lock:
        report = run_audit(graph, calibration=build_calibration(
            store.conflicts, store.graphs, store.ledger))
        sync_conflicts(graph, report, store.conflicts)
        audit_body = report.to_dict()
        conflict = store.conflicts.get(key)

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
    with store._lock:
        graph = store.graphs.get(key)
    if not graph:
        raise HTTPException(status_code=404, detail=f"no state graph for {sku}")
    with store._lock:
        report = run_audit(graph, calibration=build_calibration(
            store.conflicts, store.graphs, store.ledger))
        sync_conflicts(graph, report, store.conflicts)
    body = report.to_dict()
    body["conflict"] = None
    with store._lock:
        conflict = store.conflicts.get(key)
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
    with store._lock:
        rows = [r.model_dump() for r in store.ledger]
    return {"count": len(rows), "rows": rows}


@app.get("/api/precedents/{sku}")
def precedent_lookup(sku: str) -> dict:
    """Ledger signatures matching this SKU's current conflicts (>= 0.85 cosine)."""
    key = _single_lookup_key(sku, "precedent")
    with store._lock:
        conflict = store.conflicts.get(key)
        ledger = list(store.ledger)
    signatures = {canonical_signature(r.a.value, r.b.value) for r in store.conflicts.values()}
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