# SEMI — Technical Guide

Architecture, setup, tests, and the API contract. This is the "can I run it?" page a technical
judge opens first; copy-paste runnable, no guessing.

## Architecture (data flow)

```mermaid
flowchart LR
    A[Unilog input.xlsx<br/>(manufacturer, part_number)] --> B[Excel parser]
    B --> C[Source validator]
    C --> D[Autonomous discovery<br/>site: search + ranking]
    D --> E[Multi-format extraction<br/>PDF · web · nameplate · video]
    E --> F[Adversarial audit engine<br/>5 checks + conformal CI]
    F --> G{Consensus ≥ 0.85?}
    G -- yes --> H[Unilog output schema<br/>output_mapper]
    G -- no --> I[REJECT · INSUFFICIENT_EVIDENCE]
    I --> J[Conflict queue → human resolution]
    J --> K[Ledger row · source_url · changed_outcome]
    K --> L[(Precedent store · cosine 0.85)]
    L --> F
```

**Source authority ranking** used by `D`: `1.0` spec sheet · `0.9` manual · `0.7` page · `0.5`
video. Missing both spec and marketplace (Amazon/eBay/Target) is a hard blocker, not a guess.

## Repository layout

```
.
├── backend/                   # FastAPI · Python 3.13
│   ├── server.py              # app + WS ledger + /api/* routes
│   ├── schemas/state_graph.py # StateGraph · Conflict · ConflictSide · LedgerRow
│   ├── ingest/                # excel_input · source_validator · output_mapper (DAY3)
│   ├── discover/              # source-ranking + query builder (skeleton)
│   ├── tests/                 # pytest suite (5 passing)
│   └── .env.example
├── dashboard/                 # React 19 · Vite · Tailwind 3 · Framer Motion
│   ├── src/engine/            # in-browser enrichment simulation engine
│   ├── src/views/            # Overview · Sheet · Discovery · Audit ·
│   │                         # Conflicts · Evidence · Ledger (+ Inspector)
│   └── public/               # brand assets (logo, boot.mp4)
├── docs/
│   ├── api_contract.md       # locked FastAPI ↔ dashboard contract
│   ├── PROJECT.md            # brief + judging-rubric mapping
│   ├── TECHNICAL.md          # this file
│   ├── EXTRAS.md             # demo video + deck placeholders
│   ├── COMPETITIVE_LANDSCAPE.md  # field survey
│   ├── DIFFERENTIATION.md    # SEMI vs the published repos
│   └── notes/                # internal planning + research log
├── TODO.md                   # running day-by-day checklist
├── .github/workflows/ci.yml  # tsc + oxlint + build + pytest
└── README.md
```

## Run it

### Prerequisites
- Node 22+ (`dashboard`)
- Python 3.13 (`backend`)
- The dashboard proxies `/api` to `:8000`; run both.

### Backend
```bash
cd backend
python -m venv .venv && .venv\Scripts\activate      # Windows:
# source .venv/bin/activate                          # macOS/Linux
pip install -r requirements.txt                      # slim: fastapi uvicorn pandas openpyxl python-multipart
cp .env.example .env                                  # fill in LLM_* when you have them
uvicorn backend.server:app --reload --port 8000      # docs at /docs
```

### Dashboard
```bash
cd dashboard
npm install
npm run dev                   # http://localhost:5173
```

### Tests
```bash
backend\.venv\Scripts\python -m pytest backend\tests -q      # 5 tests, green
cd dashboard && npx tsc --noEmit && npm run lint && npm run build
```

## API contract (locked — full text in [`api_contract.md`](api_contract.md))

| Method | Endpoint | Purpose | Status |
|---|---|---|---|
| `GET`  | `/api/health` | liveness + version | ✅ |
| `POST` | `/api/ingest` | upload Unilog workbook → parse → state graphs | ✅ |
| `GET`  | `/api/state_graph/{sku}` | provenance chain + candidates | ✅ |
| `GET`  | `/api/conflicts/{sku}` | open conflict (NPT vs BSPT …) | ✅ |
| `POST` | `/api/resolve` | human resolution → ledger row + `changed_outcome` | ✅ |
| `WS`   | `/ws/ledger_events` | live counterstream | ✅ |
| `GET`  | `/api/ab_compare/{sku}` | finale: A/B + screen-of-truth surface | ⛳ |
| `GET`  | `/api/ontology/{mfr}` | finale: conflict-precedent overlay | ⛳ |

## Tech choices and *why*

| Layer | Choice | Why |
|---|---|---|
| Frontend | React 19 · Vite · Tailwind 3 · Framer Motion | fast dev loop; small bundle; spring-soft motion; real inspector vs a Streamlit grid |
| Backend | FastAPI · uvicorn | typed contract with the dashboard, WS-native, async-first |
| Extraction | Playwright · BeautifulSoup · Marker · EasyOCR (staged) | formats: pdf / web / nameplate / video — multi-format is the brief |
| LLM fallback | Gemma, OpenAI-compatible (`LLM_BASE_URL`) | single-field extraction only, temperature 0.0, never bulk generate |
| Retrieval | BGE-M3, cosine ≥ 0.85 | multilingual; tied to the same threshold the audit uses |
