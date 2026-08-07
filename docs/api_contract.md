# API Contract — SEMI Backend &lt;-&gt; Dashboard

**Owner:** shared contract (locked Day 3, adjusts to official Unilog input.xlsx + output_schema.json when they drop ~Aug 11).

**Dev base URLs**
- Backend: `http://localhost:8000` (FastAPI/uvicorn)
- Frontend: `http://localhost:5173` (Vite)
- Dev proxy: Vite forwards `/api` and `/ws` to the backend (see `dashboard/vite.config.ts`).
- Production: frontend must read the API origin from `import.meta.env.VITE_API_URL` — no hard-coded `localhost` in frontend config.

---

## Endpoints

### `GET /api/health`

Response:

```json
{ "status": "ok", "app": "semi", "version": "0.1.0", "ts": 1234567890 }
```

### `POST /api/ingest`
Uploads the Unilog input workbook. Currently an acceptance stub; full parse pipeline lands Day 3.

Request: `multipart/form-data`, field `file` (.xlsx/.xls)

Response `200`:

```json
{ "ingest_id": "a1b2c3d4e5f6", "filename": "input.xlsx", "status": "accepted" }
```

### `GET /api/state_graph/{sku}?manufacturer={m}` →  `200`
Shared State Graph for one SKU.

```json
{
  "sku": "BV-3001",
  "manufacturer": "NIBCO",
  "sources": [
    { "type": "pdf", "path": "corpus/nibco/pdfs/spec.pdf", "page": 3, "source_url": "https://www.nibco.com/..." }
  ],
  "extracted_candidates": [
    { "attribute": "pressure_rating", "value": "150", "source_path": "...", "page": 3, "extractor": "regex", "confidence": 0.9 }
  ]
}
```

### `GET /api/conflicts/{sku}` → `200`
Open conflicts for the SKU, with the two or more rival candidates.

### `POST /api/resolve`
Admin resolution that writes a ledger row (`ledger_changed_outcome = true` on precedent hits).

```json
{ "sku": "BV-3001", "attribute": "thread_standard", "human_resolution": "NPT", "reason_tags": ["spec_sheet_authority"] }
```

### `WS /ws/ledger_events`
Streams ledger changes for the live counter / precedent pop-ups.

```json
{ "event": "ledger_upsert", "signature": "NPT-vs-BSPT", "ledger_count": 7, "changed_outcome": true }
```

### `GET /api/ab_compare/{sku}` → 200
A/B surface vs plain generalist output (deferred to finale).

### `GET /api/ontology/{manufacturer}` → 200
Per-manufacturer ontology (deferred to finale).

---

## Rules (transcript + checklist)
- Every ledger row writes `source_url`.
- No URL reaches the pipeline past `source_validator.py` (Amazon/eBay/Target blocked).
- Dev CORS is open; production CORS is locked to the deployed frontend domain.
- Dashboard uses `VITE_API_URL` for all cross-origin calls; `/api` + `/ws` proxied in dev only.