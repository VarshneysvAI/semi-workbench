<p align="center">
  <img src="https://img.shields.io/badge/UniHack-2026-blueviolet?style=for-the-badge" alt="UniHack 2026"/>
  <img src="https://img.shields.io/badge/Python-3.13-blue?style=for-the-badge&logo=python" alt="Python"/>
  <img src="https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react" alt="React"/>
  <img src="https://img.shields.io/badge/Gemma_4--31B-Google_AI-4285F4?style=for-the-badge&logo=google" alt="Gemma"/>
  <img src="https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi" alt="FastAPI"/>
</p>

# 🧠 SEMI — Self-Evolving Manufacturer Intelligence

> **AI-Powered Autonomous Product Data Extraction Engine for Industrial Commerce**

SEMI is a production-grade, autonomous data extraction platform that transforms incomplete manufacturer catalogs into fully enriched, audit-traceable product datasets. Built for **UniHack 2026**, it targets the industrial commerce data gap — where 70%+ of product attributes are missing or scattered across PDFs, spec sheets, and manufacturer websites.

---

## 🎯 What Does SEMI Do?

Given a raw input catalog (CSV/Excel) with partial product data:

```
Manufacturer | Part Number | Description (maybe) | ... mostly empty columns ...
NIBCO        | BV-100      | 1" Ball Valve       |
WATTS        | WV-1011     |                     |
```

SEMI autonomously:

1. **Discovers** authoritative sources across the web (manufacturer sites, spec sheets, PDFs)
2. **Extracts** every available technical attribute using structured LLM calls (Gemma 4-31B)
3. **Audits** every extraction against physics rules, cross-source contradictions, and confidence thresholds
4. **Exports** a complete **252-column Unilog Delivery Format CSV** with full source provenance

```
PART_NUMBER | MANUFACTURER_NAME | Ref URL 1 | ... | ATTRIBUTE_LABEL 1 | ATTRIBUTE_VALUE 1 | ... | WEIGHT | WEIGHT_UOM
BV-100      | NIBCO             | nibco.com | ... | PRESSURE_RATING   | 600               | ... | 1.2    | lb
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     React Dashboard (Vite)                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────┐  │
│  │ Upload   │ │ Live     │ │ Conflict │ │ CSV Export     │  │
│  │ CSV/XLSX │ │ Sheet    │ │ Resolver │ │ (252-col)      │  │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └───────┬───────┘  │
│       │ REST        │ Poll       │ POST          │ GET      │
└───────┼─────────────┼────────────┼───────────────┼──────────┘
        ▼             ▼            ▼               ▼
┌─────────────────────────────────────────────────────────────┐
│                  FastAPI Backend (server.py)                 │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐  │
│  │ Ingest   │  │ Discover │  │ Extract  │  │ Audit      │  │
│  │ Parser   │──│ Search   │──│ LLM/RAG  │──│ Engine     │  │
│  └──────────┘  └──────────┘  └──────────┘  └────────────┘  │
│                                                             │
│  Search Chain:  agent-reach → DuckDuckGo → Exa → Firecrawl │
│  Fetch Chain:   Jina Reader → agent-reach → httpx+BS4      │
│  LLM:          Gemma 4-31B-IT (structured JSON extraction)  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              SQLite Persistent Store                  │   │
│  │  StateGraphs │ Conflicts │ Ledger │ Enrichments      │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Google AI Studio API key ([get one free](https://aistudio.google.com/apikey))

### 1. Backend Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac

pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env → set GOOGLE_API_KEY=your_key_here

# Start server
uvicorn backend.server:app --reload --port 8000
```

### 2. Dashboard Setup

```bash
cd dashboard
npm install
npm run dev
# → Opens at http://localhost:5173
```

### 3. Run the Pipeline

1. Open the dashboard at `http://localhost:5173`
2. Click **Upload Catalog** → select your CSV/XLSX input file
3. Watch the autonomous loop discover, extract, and audit each SKU
4. Click **Export CSV** → downloads the full 252-column Unilog Delivery Format

---

## 📊 Unilog Delivery Format (252 Columns)

SEMI produces output in the **exact** Unilog Delivery Format specification:

| Column Group | Examples | Count |
|---|---|---|
| **Identification** | `PART_NUMBER`, `Mfg_Part_Num`, `SKU - MY_PART_NUMBER` | 12 |
| **Manufacturer/Brand** | `MANUFACTURER_NAME`, `BRAND_NAME`, `E1_Brand` | 7 |
| **Descriptions** | `SHORT_DESC`, `LONG_DESC1`, `MARKETING_DESCRIPTION` | 8 |
| **Features** | `ITEM_FEATURES_1` through `ITEM_FEATURES_20` | 20 |
| **Attributes** | `ATTRIBUTE_LABEL/VALUE/UOM 1–50` (dynamic triplets) | 150 |
| **Dimensions** | `LENGTH`, `HEIGHT`, `WIDTH`, `WEIGHT`, `VOLUME` + UOMs | 10 |
| **Identifiers** | `UPC`, `EAN`, `GTIN`, `UNSPSC` | 6 |
| **Media/Docs** | `Product Image`, `Spec Sheet`, `Catalog`, `SDS` | 25 |
| **Source URLs** | `MFR URL`, `Ref URL 1–5` | 6 |
| **Misc** | `Country Of Origin`, `Discontinued`, `Warranty` | 8 |

---

## 🧬 Core Pipeline Stages

### Stage 1 — Ingestion
- Reads **CSV** or **Excel** (.xlsx/.xls) input files
- Column-name matching via alias tables (`manufacturer`, `brand`, `make`, `company` → `manufacturer`)
- LLM-assisted schema inference when column names are non-standard
- Stores each `(manufacturer, part_number)` as a `StateGraph` with all provided columns as `input` candidates

### Stage 2 — Discovery (Autonomous Web Search)
- Priority-ordered search chain: **agent-reach CLI** → **DuckDuckGo** → **Exa** → **Firecrawl**
- Generates spec-first search queries: `site:nibco.com "BV-100" spec`, `"BV-100" NIBCO spec sheet pdf`
- Source validation rejects e-commerce (Amazon, eBay, AliExpress) — only authoritative manufacturer sources
- Authority-ranked: spec sheets (1.0) > manuals (0.9) > product pages (0.7) > video (0.5)

### Stage 3 — Extraction (Smart Empty-Field Discovery)
- **One LLM call per source URL** — extracts ALL available attributes in a single structured JSON response
- Tells the LLM which fields are already known (from input) → avoids redundant extraction
- Fetches content via: **Jina Reader** → **agent-reach** → **httpx + BeautifulSoup** → **Firecrawl**
- Confidence threshold: only attributes with `≥ 0.4` confidence are accepted

### Stage 4 — Adversarial Audit
- **Physics constraint rules** — catches impossible values (e.g., pressure > 10000 psi)
- **Cross-source contradiction detection** — flags when two sources disagree
- **Weighted consensus** — higher-authority sources win conflicts
- **Refusal gate** — refuses to emit a value when evidence is insufficient
- **Split-conformal prediction intervals** — calibrated confidence bands (when ≥30 labeled rows exist)

### Stage 5 — Conflict Resolution
- Human-in-the-loop resolution UI for contradictions
- Resolution ledger with full provenance (`signature`, `changed_outcome`, `reason_tags`)
- Precedent KB: future conflicts matching past patterns auto-resolve via cosine similarity

### Stage 6 — Export
- Dynamic mapping to the exact 252-column Unilog Delivery Format
- Direct column routing: `weight` → `WEIGHT`/`WEIGHT_UOM`, `upc` → `UPC`, etc.
- Overflow attributes → `ATTRIBUTE_LABEL N` / `ATTRIBUTE_VALUE N` / `ATTRIBUTE_UOM N` (up to 50)
- Source URLs preserved as `Ref URL 1–5` for audit trail

---

## 🔒 Security & Data Integrity

| Concern | Mitigation |
|---|---|
| **API Key Exposure** | `.env` excluded via `.gitignore`; no hardcoded secrets |
| **DoS via Upload** | 10MB payload limit enforced server-side |
| **SQL Injection** | All queries use parameterized statements |
| **E-commerce Pollution** | `source_validator.py` blocks Amazon/eBay/AliExpress URLs |
| **LLM Hallucination** | Structured JSON schema enforces output format; confidence gating |
| **Data Provenance** | Every value carries `source_url`, `extractor`, `confidence` |

---

## 📁 Project Structure

```
hackproject new/
├── backend/
│   ├── server.py                 # FastAPI application (all REST + WebSocket endpoints)
│   ├── sqlite_store.py           # SQLite persistent store (StateGraphs, Conflicts, Ledger)
│   ├── contracts.py              # Pydantic v2 schemas (strict validation for all agents)
│   ├── graph.py                  # Async pipeline orchestrator
│   ├── extraction_orchestrator.py # Parallel web extraction coordinator
│   ├── normalizer_agent.py       # Two-pass unit normalization (deterministic + LLM)
│   ├── assembler.py              # Delivery row assembly
│   ├── audit/
│   │   ├── runner.py             # Audit engine (physics + contradiction + consensus)
│   │   ├── physical.py           # Physics constraint rules
│   │   ├── contradiction.py      # Cross-source contradiction detection
│   │   ├── conformal.py          # Split-conformal prediction intervals
│   │   └── refusal_gate.py       # Confidence refusal gate
│   ├── discover/
│   │   ├── search.py             # Hybrid web search (agent-reach → ddgs → exa → firecrawl)
│   │   └── agent_reach_agent.py  # agent-reach CLI adapter
│   ├── extract/
│   │   └── fetchers.py           # Content fetch router (Jina → agent-reach → httpx → Firecrawl)
│   ├── ingest/
│   │   ├── excel_input.py        # CSV/Excel parser with alias tables
│   │   ├── output_mapper.py      # Canonical attribute mapping + unit normalization
│   │   ├── unilog_export.py      # 252-column Unilog Delivery Format CSV generator
│   │   └── source_validator.py   # URL validation (blocks e-commerce)
│   ├── ledger/
│   │   ├── calibration.py        # Conformal calibration from ledger
│   │   ├── flywheel.py           # Precedent KB (cosine similarity matching)
│   │   └── sync.py               # Conflict synchronization
│   ├── llm/
│   │   └── gemma.py              # Google AI Studio client (Gemma 4-31B / Gemini)
│   ├── schemas/
│   │   └── state_graph.py        # StateGraph, Conflict, LedgerRow Pydantic models
│   └── schema_inference/
│       └── infer.py              # LLM-assisted column role inference
├── dashboard/
│   └── src/
│       ├── engine/
│       │   └── SemiContext.tsx    # React context (autonomous polling + discovery loop)
│       ├── components/
│       │   └── Header.tsx        # Upload/Export controls
│       ├── views/
│       │   ├── SheetView.tsx     # Live extraction spreadsheet (horizontal scroll)
│       │   └── Overview.tsx      # Dashboard metrics
│       └── data/
│           └── seed.ts           # TypeScript type definitions
├── unilog_sample/                # Reference input/output datasets
│   ├── Unihack_ Sample Dataset - Input.csv
│   └── Unihack_ Expected Output - Delivery Format.csv
├── docs/
│   └── api_contract.md           # REST API contract specification
└── deployment/                   # Production deployment configs
```

---

## 🔌 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check + version |
| `POST` | `/api/ingest` | Upload CSV/XLSX catalog |
| `POST` | `/api/discover/{sku}` | Trigger autonomous discovery + extraction |
| `GET` | `/api/export_unilog` | Download 252-column Unilog CSV |
| `GET` | `/api/ui_state` | Full dashboard state (polled at 1Hz) |
| `GET` | `/api/state_graph/{sku}` | Single SKU's state graph |
| `GET` | `/api/audit/{sku}` | Run adversarial audit on one SKU |
| `POST` | `/api/resolve` | Human conflict resolution |
| `GET` | `/api/conflicts` | List all open conflicts |
| `GET` | `/api/graphs` | List all state graphs |
| `GET` | `/api/ledger` | Full resolution ledger |
| `GET` | `/api/precedents/{sku}` | Precedent KB lookup |
| `WS` | `/ws/ledger_events` | Real-time ledger event stream |

---

## ⚙️ Configuration

All configuration is via `.env` (see `.env.example`):

```env
# Required
GOOGLE_API_KEY=your_google_ai_studio_key

# Optional
GOOGLE_GENAI_MODEL=gemma-4-31b-it    # or gemini-2.5-flash
LLM_TEMPERATURE=0.0                   # Deterministic extraction
LLM_DELAY_SECONDS=4.2                 # Rate limit throttle (free tier)
FIRECRAWL_API_KEY=                     # Optional: premium web scraping
EXA_API_KEY=                           # Optional: neural web search
AGENTREACH_ENABLED=true                # Enable agent-reach CLI
SEMI_DB_PATH=semi.db                   # SQLite database path
```

---

## 🏆 UniHack 2026

**Team:** VarshneysvAI  
**Track:** AI-Powered Product Intelligence for Industrial Commerce  
**Challenge:** Transform incomplete manufacturer catalogs into enriched, audit-traceable product datasets in the Unilog Delivery Format  

### Key Differentiators

1. **Zero-Hardcode Extraction** — No fixed attribute list. The LLM discovers ALL attributes in a single call per document.
2. **Adversarial Audit** — Math-based physics checks + cross-source contradiction detection. SEMI refuses rather than guesses.
3. **Full Provenance** — Every single value carries its `source_url`, `extractor`, and `confidence`. No black boxes.
4. **Cost Efficiency** — One LLM call per document (not per attribute). Ready for self-hosted Gemma 31B via vLLM.
5. **Production Security** — 10MB upload limits, parameterized SQL, e-commerce URL blocking, no hardcoded secrets.

---

## 📄 License

MIT License — see [LICENSE](LICENSE)