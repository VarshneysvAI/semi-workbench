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
from backend.schemas.state_graph import Conflict, LedgerRow, StateGraph

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
    try:
        result = excel_input.parse_input_workbook(staged)
    except (ValueError, OSError) as exc:
        staged.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    with store._lock:
        for rec in result.records:
            key = store.key(rec.manufacturer, rec.part_number)
            store.graphs.setdefault(
                key,
                StateGraph(
                    sku=rec.part_number,
                    manufacturer=rec.manufacturer,
                    input_source_url=None,
                    sources=[],
                    extracted_candidates=[],
                ),
            )
    staged.unlink(missing_ok=True)

    ingest_id = uuid.uuid4().hex[:12]
    logger.info("Ingest %s: %d products from %s", ingest_id, len(result.records), file.filename)
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

    signature = f"{conflict.a.value} vs {conflict.b.value}"
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