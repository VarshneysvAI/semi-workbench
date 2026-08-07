"""SEMI — Self-Evolving Manufacturer Intelligence.

DAY 0 scaffold endpoint surface. Full contract lives in
``docs/api_contract.md``; endpoints grow per-day from here.
"""

from __future__ import annotations

import logging
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("semi.server")

APP_VERSION = "0.1.0"

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


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "app": "semi", "version": APP_VERSION, "ts": int(time.time())}


@app.post("/api/ingest")
async def ingest_workbook(file: UploadFile = File(...)) -> dict:
    """Accept an Unilog input workbook (placeholder until Day 3 schema).

    Returns an ingest_id; the actual parse pipeline lands with the
    official input.xlsx + output_schema.json release (~Aug 11).
    """
    if not file.filename or not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Expected an .xlsx/.xls workbook upload")
    payload = await file.read()
    if len(payload) == 0:
        raise HTTPException(status_code=400, detail="Empty file")
    ingest_id = uuid.uuid4().hex[:12]
    logger.info("Received workbook %s (id=%s, %d bytes)", file.filename, ingest_id, len(payload))
    return {"ingest_id": ingest_id, "filename": file.filename, "status": "accepted"}