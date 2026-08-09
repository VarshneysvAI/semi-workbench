# UniHack 2026 — AGENT EXECUTION TODO LIST (SEMI v1.0)

**Project:** Self-Evolving Manufacturer Intelligence (SEMI)  
**Deadline:** 23 Aug 2026 (12:00 PM IST) — **16 days**  
**Streams:** A (Backend) | B (Frontend)  
**Shared Contract:** `docs/api_contract.md` (locked Day 2)

---

## 📋 MASTER TODO CHECKLIST (Agent Self-Audit Daily)

### 🔴 CRITICAL - Must Pass Daily
- [ ] Both servers boot without errors (`python -m uvicorn backend.server:app --reload` + `npm run dev`)
- [ ] Two-pass demo flow smoke-tested ≤ 2 hours ago
- [ ] At least one conflict has `ledger_changed_outcome = true`
- [ ] No `localhost` in frontend config (uses `VITE_API_URL`)
- [ ] No `.env` in git (`git status` clean)
- [ ] Live link works on fresh browser (no cache)

### 🟡 ARCHITECTURE DISCIPLINE - Must Pass Weekly
- [ ] Every ledger row writes `source_url` (transcript requirement)
- [ ] No source URL passes through `source_validator.py` matching forbidden domains
- [ ] Regex patterns tested on ALL manufacturers' data, not just one
- [ ] LLM fallback is single-field extraction, never "extract everything"
- [ ] Ledger retrieval cosine threshold ≥ 0.85 (not lowered)

### 🟢 SUBMISSION READINESS (Day 12+)
- [ ] Live link works on fresh browser
- [ ] GitHub repo is PUBLIC
- [ ] Demo video unlisted YouTube, link works
- [ ] Deck exported PDF, all 4 criteria addressed
- [ ] Workflow diagram renders in GitHub README
- [ ] Cost figures labeled "structural estimates"
- [ ] Classifier accuracy = cross-validated score

---

## 📅 DAY-BY-DAY EXECUTION TODO

---

### 📅 DAY 0 (Aug 8) — PROJECT SCAFFOLD [BLOCKING - Both Streams]

#### Stream A (Backend)
- [ ] Create `backend/requirements.txt` with pinned deps:
  ```
  fastapi==0.115.0
  uvicorn[standard]==0.30.6
  playwright==1.46.0
  marker-pdf==0.1.0
  easyocr==1.7.2
  beautifulsoup4==4.12.3
  lxml==5.3.0
  duckduckgo-search==6.3.0
  sentence-transformers==3.0.1
  torch==2.4.0
  numpy==1.26.4
  pandas==2.2.2
  openpyxl==3.1.5
  python-multipart==0.0.9
  websockets==12.0
  scipy==1.13.1
  scikit-learn==1.5.0
  ```
- [ ] Create `backend/ingest/excel_input.py` — Unilog Excel parser
- [ ] Create `backend/ingest/source_validator.py` — blocks Amazon/eBay/Target
- [ ] Create `backend/discover/search.py` — manufacturer site search
- [ ] Create `backend/server.py` — FastAPI + `/api/health`
- [ ] `uv pip install -r requirements.txt` — install deps
- [ ] Verify: `python -m uvicorn backend.server:app --reload` starts

#### Stream B (Frontend)
- [ ] `npm create vite@latest dashboard -- --template react-ts`
- [ ] `cd dashboard && npm install`
- [ ] Add Tailwind: `npm install -D tailwindcss postcss autoprefixer && npx tailwindcss init -p`
- [ ] Add deps: `npm install framer-motion socket.io-client axios react-router-dom lucide-react`
- [ ] Create `dashboard/src/App.tsx` — routing with 5 view placeholders
- [ ] Create `dashboard/vite.config.ts` — proxy to `http://localhost:8000`
- [ ] Verify: `npm run dev` serves at localhost:5173

#### Both Streams
- [ ] `git init` + `.gitignore` (exclude `venv/`, `node_modules/`, `corpus/`, `unilog_sample/`, `*.sqlite`, `.env`)
- [ ] First commit: "Initial scaffold"
- [ ] Document API contract in `docs/api_contract.md`

---

### 📅 DAY 1 (Aug 9) — CROSS-MANUFACTURER TRANSFER VERIFICATION [Stream A Only]

**⚠️ LOAD-BEARING GATE — DO NOT SKIP**

- [ ] Pick 3 manufacturers: NIBCO (pressure), Watts (material), Apollo (food-grade)
- [ ] Download 5-10 spec sheet PDFs each → `corpus/{mfr}/pdfs/`
- [ ] Download nameplate images → `corpus/{mfr}/images/`
- [ ] Save product page HTML → `corpus/{mfr}/web/`
- [ ] Run rapidfuzz pass over candidate noun-phrases (quick-and-dirty)
- [ ] Create `tests/test_cross_manufacturer_transfer.ipynb`:
  - Extract `(attribute, value_A, value_B, source_types)` tuples
  - Count recurring conflict signatures across all three
  - Output frequency table
- [ ] **GATE G-LEDDER**: At least 2 conflict signatures recur across ≥3 SKUs in each of two manufacturers
  - If FAIL: swap one manufacturer, retry once
  - If still FAIL: escalate immediately — architecture redesign needed

---

### 📅 DAY 2 (Aug 10) — SHARED STATE GRAPH + EXCEL INPUT [A+B Parallel]

**⚠️ Watch for Unilog dataset email (~Aug 11)**

#### Stream A
- [ ] Define Shared State Graph schema in `backend/schemas/state_graph.py`:
  ```python
  class StateGraph(BaseModel):
      sku: str
      manufacturer: str
      input_source_url: Optional[HttpUrl]
      sources: list[Source]
      extracted_candidates: list[ExtractedCandidate]
  class Source(BaseModel):
      type: Literal["pdf", "image", "web", "excel_input"]
      path: str
      page: Optional[int]
      raw_text: str
      source_url: Optional[str]
  class ExtractedCandidate(BaseModel):
      attribute: str
      value: str
      source_path: str
      page: Optional[int]
      bbox: Optional[list[float]]
      raw_extract: str
      extractor: Literal["regex", "llm", "ocr", "manual"]
      confidence: float
  ```
- [ ] Build `backend/ingest/excel_input.py` — reads Unilog input.xlsx format
- [ ] Build `backend/ingest/source_validator.py` — rejects Amazon/eBay/Target URLs
- [ ] Test with placeholder Excel file

#### Stream B (Parallel)
- [ ] React dashboard routes scaffold:
  - Install React Router, Tailwind
  - Create stub components for Views 0,1,2,3,4
  - Create `App.tsx` with two-pane layout: sidebar + main content
  - Top-bar persistent placeholder for View 1 (ledger counter)

---

### 📅 DAY 3 (Aug 11) — DATASET PIVOT DAY [Both Streams]

**⚠️ DATASET DROPS TODAY — PIVOT DAY**

- [ ] Download sample `input.xlsx` + `output_schema.json` from Resources tab
- [ ] Inspect:
  - Input columns: `manufacturer`, `part_number`, others?
  - Output schema: JSON schema, table schema?
  - Dataset category: HVAC / plumbing / electrical / mixed?
- [ ] Update `backend/ingest/excel_input.py` for actual input columns
- [ ] Build `backend/ingest/output_mapper.py` — translates to Unilog schema
- [ ] Re-scope demo:
  - If ball valves: keep plan
  - If different category: re-scope regex library (Day 4)
  - If multi-category: pick smallest category for demo
- [ ] Update `docs/architecture.md` for scope adjustments
- [ ] **Create `docs/api_contract.md`** — finalize FastAPI ↔ React contract:
  - `GET /api/health`
  - `POST /api/ingest` — accepts Excel upload, returns ingest_id
  - `GET /api/state_graph/{sku}?manufacturer={m}`
  - `GET /api/conflicts/{sku}`
  - `POST /api/resolve` — admin's resolution
  - `WS /ws/ledger_events` — websocket streaming
  - `GET /api/ab_compare/{sku}` — A/B vs GPT-4o
  - `GET /api/ontology/{manufacturer}` — deferred to finale

---

### 📅 DAY 4 (Aug 12) — AUTONOMOUS DISCOVERY: HYBRID BACKEND CHAIN [Stream A]

✅ **BUILT AHEAD (Aug 9) — live search verified with zero keys (ddgs served real hits).**

- [x] `backend/discover/agent_reach_agent.py` — **agent-reach CLI adapter**
  (runtime probe: `doctor --json` / `--help`; search + `transcribe`; honest
  degradation when the CLI is absent — no guessing).
- [x] `backend/discover/search.py` — **priority chain** (first backend with hits wins):
  1. **agent-reach** (CLI, when installed)
  2. **Firecrawl `/search`** (FIRECRAWL_API_KEY; web + pdf categories)
  3. **Exa** (EXA_API_KEY, `POST api.exa.ai/search`)
  4. **ddgs** (DuckDuckGo, no key) — always-on last resort
- [x] Authority ranking (spec=1.0, manual=0.9, page=0.7, video=0.5) +
  forbidden-domain filter (SourceValidator) — carried over.
- [x] Provenance: `last_search_backend()` records which backend served (audit trail).
- [x] Deterministic routing tests (network monkeypatched) — order + fallback verified.
- [ ] (dropped) Playwright stealth browser — replaced by the cheaper multi-backend
      API chain; browser rendering only if/when a page needs JS (Firecrawl covers it).

---

### 📅 DAY 5 (Aug 13) — MULTI-FORMAT EXTRACTION ROUTER [Stream A]

✅ **BUILT AHEAD (Aug 9) — content-type router with provenance.**

- [x] `backend/extract/fetchers.py` — routes each source by kind, records `fetched_via`:
  - **PDF** → Firecrawl `parsePDF` (key) → Jina Reader (free)
  - **WEB** → Firecrawl → Jina Reader → httpx + BeautifulSoup
  - **VIDEO** → **yt-dlp subtitles** (auto-subs, en) → **agent-reach transcribe**
    → Jina Reader
- [x] `backend/llm/gemma.py` — **Gemma single-field extraction via Gemini free tier**
  (google.genai, strict-JSON schema, temperature 0.0, ~3s; verified live on
  `gemma-4-31b-it`; raises `LLMNotConfigured` when key absent — no silent fake).
- [x] Deterministic tests: routing order + provenance verified; 23 tests green.
- [ ] deferred (not blocking): Marker/OCR for scanned PDFs, `unit_normalizer`
      (unit conversions land with the Day-3 output_mapper/schema pass).

---

### 📅 DAY 6 (Aug 14) — ADVERSARIAL AUDIT ENGINE (CORE) [Stream A]

**⚠️ CORE INNOVATION — NO COMPROMISE**

- [ ] `backend/audit/physical.py`:
  ```python
  RULES = [
      ("material=PVC ∧ temperature>60°C", lambda m,t: m=="PVC" and t>60),
      ("material=PVC ∧ pressure>150psi", lambda m,p: m=="PVC" and p>150),
      ("material=Brass ∧ pressure>3000psi", lambda m,p: m=="Brass" and p>3000),
      ("thread=NPT ∧ standard=BSPP", lambda t,s: t=="NPT" and s=="BSPP"),
      ("size<0.5\" ∧ pressure>10000psi", lambda s,p: s<0.5 and p>10000),
  ]
  ```
- [ ] `backend/audit/contradiction.py`:
  - BGE-M3 embeddings on value strings
  - cosine < 0.3 + both confidence > 0.5 → flag
- [ ] `backend/audit/compositional.py`:
  ```python
  CONSTRAINTS = {
      "pressure_rating": lambda m,t,s: p <= max_pressure(m, t, s),
      "flow_coefficient": lambda s,p: fc ∝ s² × √p,
      "torque": lambda p,s: t ∝ p × s³,
  }
  ```
- [ ] `backend/audit/adversarial.py`:
  - Generate disproof queries: "MAX pressure for [material] [size]?"
  - Search manufacturer site for disproof
- [ ] `backend/audit/conformal.py`:
  - Split Conformal Prediction (split CP)
  - Calibration: 200 seeded human-verified rows
  - Nonconformity: 1 - raw_confidence
  - Output: [lower, upper] with 95% coverage

---

### 📅 DAY 7 (Aug 15) — CONFORMAL CALIBRATION + CONSENSUS [Stream A]

- [ ] Build `backend/audit/conformal.py`:
  - Split CP on 200 seeded rows
  - Nonconformity score: 1 - raw_confidence
  - Verify 95% coverage on calibration set
- [ ] Build `backend/consensus/resolve.py`:
  - Source weights: spec=1.0, manual=0.9, page=0.8, video=0.6
  - Family boost: +0.3 if 8+/10 siblings agree
  - Weighted consensus → winner
  - If winner.weight ≥ 0.85 → ACCEPT, else REFUSE
- [ ] Build `backend/consensus/refusal_gate.py`:
  - If confidence < 0.7 AND no precedent → REFUSE
  - Output `INSUFFICIENT_EVIDENCE` with reason

---

### 📅 DAY 8 (Aug 16) — TWO-PASS LIVE LEARNING FLOW [Both Streams]

**⚠️ THE WOW MOMENT — MUST WORK END-TO-END**

- [ ] Pre-seed demo flow:
  - SKU 1 (NIBCO): `thread_standard` conflict (NPT vs BSPT)
  - SKU 2 (Watts): same signature, same conflict
- [ ] Wire React side:
  - Step 1: Conflict A alone (counterfactual, ledger empty, counter=0)
  - Step 2: Admin resolves → ledger row written → counter ticks to 1
  - Step 3: Conflict B → spinner → precedent match → View 3 pop-up → counter ticks to 2
- [ ] Run 5× end-to-end — if falters, debug 4hrs max
- [ ] **FALLBACK**: If cross-mfr fails, swap to cross-family within NIBCO

---

### 📅 DAY 9 (Aug 17) — SEEDED LEDGER DATA + CLASSIFIER OVERLAY [Both Streams]

#### Stream A
- [ ] `backend/classifier/seed_data.py`:
  - Hand-author 150 plausible `(conflict_signature, human_resolution)` rows
  - Based on real patterns from scraped NIBCO+Watts
  - Mix rationale tags: spec_sheet_authority (40%), family_pattern (25%), physical_check (15%), external_knowledge (10%), ambiguous (10%)
- [ ] Insert seeded rows into SQLite ledger
- [ ] `backend/classifier/train.py`:
  - Features: embedding + source-authority + family-pattern vote
  - Target: `human_resolution`
  - Model: Logistic Regression (or XGBoost)
  - Train/test 80/20 on seeded data
- [ ] `backend/classifier/predict.py`:
  - Endpoint: `POST /api/classifier/predict`
  - Returns predicted resolution + confidence
  - Wire as 5th pass: when ledger has no precedent, classifier predicts

#### Stream B
- [ ] Build View 6 (Classifier Overlay):
  - Side-by-side: "Precedent retrieval says: NPT (citing #007)" vs "Classifier says: NPT (0.81)"
  - Color agreement/disagreement differently
  - Notification: "Classifier retrained on N+1 rows"

---

### 📅 DAY 10 (Aug 18) — UNILOG SCHEMA MAPPER + DASHBOARD [Both Streams]

#### Stream A
- [ ] Build `backend/output/map_unilog.py`:
  - Load Unilog schema (released Aug 11)
  - Map discovered features via BGE-M3 semantic similarity
  - Validate: permitted values, units, required fields
  - Auto-convert units (in→mm, psi→bar)
- [ ] Build `backend/output/evidence.py`:
  - Format audit report per field
  - Evidence chain with source_url, page, bbox

#### Stream B (Parallel)
- [ ] Build View 0 (Ontology Discovery) — emphasis bars
- [ ] Build View 1 (Live Ledger Counter) — top bar, persistent
- [ ] Build View 2 (Conflict Workspace) — 3 columns
- [ ] Build View 3 (Precedent Pop-up) — counterfactual diff
- [ ] Build View 4 (Source Viewer) — PDF/image/web side-by-side
- [ ] Build View 5 (Tier Comparison) — 4 columns
- [ ] Build View 6 (Classifier Overlay) — side-by-side predictions
- [ ] Wire websocket to `/ws/ledger_events` for live counter

---

### 📅 DAY 11 (Aug 19) — DEPLOY + LIVE LINK [Stream B]

- [ ] Frontend → Vercel (`npm run build` → drag-and-drop or `vercel` CLI)
- [ ] Backend → Railway (FastAPI uvicorn) with persistent SQLite volume
- [ ] Configure CORS for production frontend domain
- [ ] Switch websocket from localhost to Railway URL
- [ ] Smoke test deployed version end-to-end
- [ ] Share link with friend for external test

---

### 📅 DAY 12 (Aug 20) — FULL INTEGRATION TEST + DOCS [Both Streams]

- [ ] Run 10 PNs end-to-end → all produce valid output
- [ ] Build workflow diagram (mermaid) in `docs/workflow_diagram.md`
- [ ] Build `docs/architecture.md` — one-page overview
- [ ] Build `docs/demo_script.md` — verbatim 3-min script
- [ ] Download Hack2skill deck template → populate

---

### 📅 DAY 13 (Aug 21) — DEMO VIDEO + SUBMISSION [Both Streams]

- [ ] **Record 3-min video** (OBS/Loom, 1080p, mic):
  - Take 3 → pick best
  - Upload to YouTube UNLISTED
- [ ] Fill presentation deck:
  - Cover: team, project title
  - Problem: one sentence from PS
  - Approach: mermaid workflow diagram
  - Tech stack: justified per choice
  - Demo video embed
  - GitHub + live link
  - Innovations: 4 bullets (adversarial audit, conformal CI, MED, data flywheel)
  - Accuracy safeguards
  - Scalability: cost curve
  - Limitations (honest)
  - Future scope (Phase 2)
- [ ] **SUBMIT BY 12:00 PM** (not midnight!):
  - Presentation PDF
  - Live link
  - GitHub repo (PUBLIC)
  - Demo video link
  - Brief description (~500 chars)

---

### 📅 DAY 14-15 (Aug 22-23) — BUFFER

- [ ] Re-test live link from fresh browser
- [ ] Test on friend's laptop (different browser, screen size)
- [ ] Final commit, final push
- [ ] Screenshot submission confirmation

---

## 🗂️ WORK LOG

### Aug 9 — Day 4/5 built ahead of schedule + CI restored
- **Discovery is now a hybrid backend chain, strict priority:**
  1. **agent-reach** (CLI adapter — runtime probe, search + transcribe)
  2. **Firecrawl `/search`** (key) → 3. **Exa** (key) → 4. **ddgs** (no key, always-on)
- Live smoke (zero keys): real DuckDuckGo hits for `NIBCO BV-1001 spec sheet pdf`;
  provenance via `last_search_backend()` → "ddgs".
- **Fetch router** (`fetchers.py`): PDF → Firecrawl/Jina; WEB → Firecrawl/Jina/bs4;
  **VIDEO → yt-dlp subtitles → agent-reach transcribe → Jina** (transcript extraction
  per directive: "if we find a YT link we use search to extract what the YT says").
- **LLM channel decided: Gemini free tier serves the Gemma model** (`gemma-4-31b-it`,
  google.genai, strict-JSON, temp 0.0) — NVIDIA NIM dropped (too slow).
- Tests: `test_search_hybrid.py` added (routing order + fallback + provenance);
  **23/23 pytest green**, offline-deterministic; deps unified via `backend/requirements.txt`
  (fixes the pandas cp313 CI break) — **CI green on both jobs**.
- Docs: `.env.example` now documents the full priority chain.

### Aug 8 (Day 0 + early rollout)
- **Frontend (Stream B) — COMPLETE & verified** (`dashboard/`): all 7 views
  (Overview, Sheet, Discovery, Audit, Review, Evidence, Ledger) + Inspector,
  resizable mobile-sidebar, boot screen (logo + updated final mp4), Obsidian
  theme locked, 60fps at 8× speed (copy-on-write rows + memoized sheet).
  Checks: `tsc --noEmit` clean, `oxlint` 0 errors, `vite build` passes.
  Bug fixes: Inspector transcript pid-filtering, cell-write animation replay.
- **Backend (Stream A) — Day 2 mostly done** (`backend/`):
  - `schemas/state_graph.py` — StateGraph / Source / Candidate / Conflict /
    LedgerRow models (matches `docs/api_contract.md`).
  - `server.py` v0.2.0 — `/api/health`, `/api/ingest` (real Excel parse),
    `/api/state_graph/{sku}`, `/api/conflicts/{sku}`, `/api/resolve`
    (ledger row + changed_outcome + WS broadcast), `/ws/ledger_events`,
    deferred stubs for `ab_compare` / `ontology`. In-memory Store.
  - `ingest/output_mapper.py` — Day-3 prep: canonical attributes, unit
    splitting, required-field validation, `DAY3` re-scope markers.
  - `tests/` — 5 pytest smoke tests passing (ingest→graph→resolve→flips→
    forbidden URLs). Server boots: `health 200`.
- **Pending:** Day 1 GATE (corpus downloads + cross-manufacturer notebook —
  Stream A manual step), Day 3 scoping against official input.xlsx (~Aug 11).

---

## 🏁 PHASE 2 PREVIEW (If Shortlisted — Sep 4 Finale)

**Aug 24 → Sep 4 (11 days):**
1. Change 2 — Live Adversarial Judge Mode (View 7)
2. Change 4 — Ontology Discovery as Proven Substrate (View 0)
3. Change 7 — 3D Provenance Viewer (View 8)
4. Change 9 — Live HyperScale Downstream Simulation (View 10)
5. Updated workflow diagram
6. Live-demo script for Sep 4 stage finale

---

## 🚨 GLOBAL ERROR CHECKLIST (Agent Self-Audit Every Day)

### Code Quality
- [ ] All new functions have type hints (Python) or TypeScript types (frontend)
- [ ] No `print()` in production code; only `logging.info()` / `console.info()`
- [ ] All external API calls wrapped in try/except with fallback
- [ ] No hard-coded credentials — all secrets in environment variables
- [ ] No `.env` in git (`git status` clean)
- [ ] No `localhost` URLs in frontend config — use `import.meta.env.VITE_API_URL`

### Architecture Discipline
- [ ] Every ledger row writes `source_url` (transcript requirement)
- [ ] No source URL passes through `source_validator.py` matching forbidden domains
- [ ] Regex patterns tested on ALL manufacturers' data, not just one
- [ ] LLM fallback is single-field extraction, never "extract everything"
- [ ] Ledger retrieval cosine threshold ≥ 0.85 (not silently lowered)

### Demo Reliability
- [ ] Two-pass demo flow smoke-tested ≤ 2 hours ago
- [ ] At least one conflict has `ledger_changed_outcome = true`

### Submission Readiness (Day 12+)
- [ ] Live link works on fresh browser
- [ ] GitHub repo is PUBLIC
- [ ] Demo video unlisted YouTube, link works
- [ ] Deck exported PDF, all 4 criteria addressed
- [ ] Workflow diagram renders in GitHub README

### Anti-Defensive Patterns
- [ ] No `// TODO` in demo code paths
- [ ] No "future enhancement" comments in demo code — move to README Phase 2
- [ ] No CSV/Excel hard-coded paths in demo — use `/api/ingest`
- [ ] No LLM mocking in tests without `@pytest.mark.mock_llm` decorator

### Honesty Discipline
- [ ] Cost figures labeled "structural estimates, not audited financials"
- [ ] Classifier accuracy = cross-validated score, not training score
- [ ] "System builds its own training data" paired with disclaimer footnote

---

## 📦 DELIVERABLES CHECKLIST (Submission Day)

- [ ] **Live Link** — `https://{your-dashboard}.vercel.app` (works on phone)
- [ ] **GitHub Repo** — public, no `.env`, no `node_modules`, no secrets
- [ ] **Demo Video** — YouTube unlisted, 3-4 min, clear audio
- [ ] **Presentation Deck** — PDF, Hack2skill template, all sections filled
- [ ] **Brief Description** — ~500 chars on dashboard

---

## ⚠️ FINAL REMINDERS

1. **Submit by 12:00 PM Aug 21** — not midnight, not Aug 23. Buffer = life.
2. **Dataset arrives ~Aug 11** — Days 1-3 are prep; real work starts Aug 11.
3. **Gemma via Gemini free tier (`gemma-4-31b-it`)** — free, fast, no GPU; NIM dropped.
3. **G-Ledger gate (Day 1) is non-negotiable** — if cross-mfr transfer fails, architecture changes.
4. **Adversarial Audit is the headline** — 5 audits + conformal CI = formal verification.
5. **Cost story = downward curve** — not "cheap", but "gets cheaper over time".

---

**READY TO BUILD. Day 1 starts tomorrow. Good luck.**

---

*Last updated: 2026-08-09 | Plan version: SEMI v1.0 | Next review: Daily standup*