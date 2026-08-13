# SEMI — Implementation TODO

## Phase 0: Repo Cleanup (Do First)

### Remove Deleted Files (already staged as deleted)
- [ ] `docs/COMPETITIVE_LANDSCAPE.md`
- [ ] `docs/DIFFERENTIATION.md`
- [ ] `docs/EXTRAS.md`
- [ ] `docs/notes/PLAN.md`
- [ ] `docs/notes/UniHack_Final_Plan.md`
- [ ] `docs/notes/UniHack_PS_Understanding.md`
- [ ] `docs/notes/unihack_complete_research_architecture.md`
- [ ] `TODO.md` (this file will be recreated)

### Remove Untracked Junk
- [ ] `backend/env.py` (unused)
- [ ] `backend/semi.db` (local DB, not for repo)
- [ ] `backend/output/` (empty/duplicate dir)
- [ ] `backend/schema/` (empty/duplicate dir)

### Clean Modified Files (review & commit or revert)
- [ ] `backend/extract/fetchers.py` — keep only Jina + Firecrawl fetchers
- [ ] `backend/llm/gemma.py` — Gemma client (OpenAI-compatible, temp=0)
- [ ] `backend/server.py` — FastAPI routes (health, ingest, discover, state_graph, conflicts, resolve, WS)
- [ ] `backend/tests/conftest.py` — test fixtures
- [ ] `backend/tests/test_audit.py` — audit tests
- [ ] `backend/tests/test_day2_pipeline.py` — pipeline tests
- [ ] `backend/tests/test_discover_hybrid.py` — discover tests

---

## Phase 1: Core Contracts & Schemas (Foundation)

### `backend/contracts.py` — Single Source of Truth
- [ ] Universal `AgentOutput` envelope: `status` (ok/unknown/error) + `data` + `error` + `schema_version`
- [ ] `SchemaInferInput` / `SchemaPlan` / `ColumnRole` / `AttributeBlueprint`
- [ ] `ExtractInput` / `CitedValue` / `WebExtractResult`
- [ ] `AuditInput` / `AuditCheck` / `AuditVerdict`
- [ ] `NormalizeInput` / `DeliveryRow` (252 columns, strict)
- [ ] All models: `ConfigDict(extra="forbid", strict=True)`

### `backend/sqlite_store.py` — Persistence Layer
- [ ] `schema_plans` table (file_hash, domain, product_kind, columns_json, attributes_json, needs_human, questions_json)
- [ ] `extracted_values` table (sku, attribute, value, unit, source_url, snippet, confidence, extractor, run_id, timestamp)
- [ ] `canonical_truth` table (sku, canonical_key, canonical_value, canonical_unit, confidence, source_urls_json, precedence_json)
- [ ] `audit_verdicts` table (sku, consensus_score, checks_json, decision, insufficient_attrs_json)
- [ ] `ledger_rows` table (sku, attribute, old_value, new_value, source_url, changed_outcome, run_id, timestamp)
- [ ] `identity_resolution` table (canonical_id, mfr, normalized_specs_hash, mpn_fuzzy_group)

---

## Phase 2: Schema Inference Agent (Gate 1)

### `backend/schema_infer_agent.py`
- [ ] Input: file_path, sample_rows (20), column_stats (types, nulls, uniques, placeholder_%, samples)
- [ ] Gemma call: temperature=0, structured output → `SchemaPlan`
- [ ] Output: domain, product_kind, column_roles, attribute_blueprint, needs_human, human_questions
- [ ] Persist to `schema_plans` keyed by file_hash
- [ ] Gate 1 logic: if `needs_human` → raise `HumanRequired` with questions

---

## Phase 3: Parallel Web Extraction (Core)

### `backend/crawl4ai_extractor.py` — HTML Deep Crawl
- [ ] `Crawl4AI` setup: `AsyncWebCrawler`, `BrowserConfig`, `CrawlerRunConfig`
- [ ] Deep crawl strategy: seed `site:manufacturer.com "MPN"`, max_depth=3, include_patterns=["*product*", "*spec*", "*catalog*"]
- [ ] `LLMExtractionStrategy` with Pydantic schema `AttributeBatch` (list of raw attributes)
- [ ] Chunking for large pages, `input_format="markdown"`, temperature=0
- [ ] Source validator: block marketplace domains (amazon, ebay, target, walmart, etc.)
- [ ] Output: list of `CitedValue` with `extractor="crawl4ai"`

### `backend/pdf_extractor.py` — PDF/DOCX Catalogs
- [ ] `pdf-reader-mcp` (Citra) MCP client via `stdio` or HTTP
- [ ] `read_pdf` with `include_tables=true`, `include_ocr_text_layer=true`, `include_document_map=true`
- [ ] `pdf_evidence` for `extract_regions` on table bounding boxes
- [ ] Firecrawl `/parse` fallback for DOCX / remote PDFs
- [ ] LLM extraction from markdown+tables → `AttributeBatch`
- [ ] Output: list of `CitedValue` with `extractor="pdf_reader_mcp"` or `"firecrawl_parse"`

### `backend/youtube_extractor.py` — YouTube Transcripts
- [ ] `agent-reach get youtube.transcript "URL" --max-tokens 4000` (primary)
- [ ] `yt-dlp --write-sub --skip-download` fallback
- [ ] Transcript → LLM extract specs → `AttributeBatch`
- [ ] Output: list of `CitedValue` with `extractor="youtube_transcript"`

### `backend/extraction_orchestrator.py` — Parallel Coordinator
- [ ] Input: `sku`, `manufacturer`, `part_number`, `description`, `remaining_attributes`, `schema_plan`
- [ ] KB check first (fuzzy match cosine ≥ 0.85) → return cached if hit
- [ ] Fire all 3 extractors in parallel (asyncio.gather)
- [ ] Merge by `(attribute, source_url)` → deduplicate
- [ ] Return combined `list[CitedValue]`

---

## Phase 4: Two-Pass Normalization (Key Innovation)

### `backend/normalizer_agent.py`
- [ ] **Pass A — Label → Canonical Key**
  - Input: list of raw extractions with varied labels
  - Domain-specific synonym dictionary (loaded from config or learned)
  - LLM prompt: map each label to canonical key using synonym dict
  - Output: grouped by `canonical_key` with all source variants
- [ ] **Pass B — Unit → Canonical Unit + Conflict Resolution**
  - Canonical storage units per attribute family: width→in, weight→lb, temp→C, voltage→V, etc.
  - LLM prompt: convert all values, resolve conflicts via precedence:
    1. Manufacturer spec sheet (authority=1.0)
    2. Manufacturer HTML page (0.9)
    3. Manual (0.7)
    4. Distributor sheet (0.5)
    5. Third-party verified (0.3)
  - Output: `CanonicalAttribute` — canonical_key, canonical_value, canonical_unit, confidence, source_url, precedence_rank
- [ ] Persist to `canonical_truth` table

---

## Phase 5: Adversarial Audit (5 Checks + Conformal CI)

### `backend/audit_agent.py`
- [ ] **Check 1: Physical Rules** — LLM-validated rules per domain (width>0, PVC→pressure≤150psi, etc.)
- [ ] **Check 2: Cross-Source Contradiction** — Compare canonical values across sources for same key
- [ ] **Check 3: Compositional Curve** — Physics-based fit (e.g., belt tension vs width, power vs current)
- [ ] **Check 4: Disproof Search** — Active query via agent-reach: "find evidence [value] is wrong for [MPN]"
- [ ] **Check 5: Split-Conformal 95% CI** — Calibrated on ledger history per numeric attribute → `[lo, hi]`
- [ ] Consensus score = weighted aggregate (weights configurable)
- [ ] Decision: `pass` (consensus ≥ 0.85) | `insufficient_evidence`
- [ ] Persist to `audit_verdicts` table
- [ ] Gate 2: if fail → raise `HumanRequired` with attribute, value, source_url, snippet, why_low, where_found

---

## Phase 6: Assembly → 252-Col Delivery Row

### `backend/assembler.py`
- [ ] Map canonical attributes → 47 `ATTRIBUTE_LABEL/VALUE/UOM` triplets (dynamic)
- [ ] Generate 5 descriptions from cited slots only:
  - `INVOICE_DESC` ≤40 chars, ALL CAPS
  - `MOBILE_DESC` 60-80 chars, Title Case
  - `SHORT_DESC` (Product Title)
  - `LONG_DESC1` (Long Description)
  - `MARKETING_DESCRIPTION`
- [ ] Taxonomy: `Dept/Class/Fine/Classpath` from SchemaPlan + precedent
- [ ] `MFR_URL` = highest-authority source_url; `Ref URL 1-5` = next best
- [ ] Images: download first 5 from manufacturer pages
- [ ] Docs: spec sheet PDF URLs, manual URLs, SDS, drawings
- [ ] Output: `DeliveryRow` (validated against 252-col contract)
- [ ] Persist to `extracted_values` + `canonical_truth` + `audit_verdicts`

---

## Phase 7: Ledger / Flywheel (Self-Evolving)

### `backend/ledger.py`
- [ ] `write_source_truth()` — every extraction with full provenance
- [ ] `write_canonical_truth()` — merged view per (sku, canonical_key)
- [ ] `resolve_identity()` — same mfr + normalized specs + fuzzy MPN → canonical_id
- [ ] `record_human_resolution()` — ledger row with `changed_outcome=true`
- [ ] `get_precedent()` — cosine ≥ 0.85 (BGE-M3 later, exact-string v1)
- [ ] `calibration_data()` — for conformal CI

---

## Phase 8: LangGraph Orchestration

### `backend/graph.py`
- [ ] State schema: `OverallState` with all phase data
- [ ] Nodes: `schema_infer`, `gate1_human`, `precedent_check`, `parallel_extract`, `normalize`, `audit`, `gate2_human`, `assemble`, `ledger_write`
- [ ] Conditional edges: Gate 1 → human / continue; Gate 2 → human / continue
- [ ] Checkpointing: SQLite (LangGraph built-in)
- [ ] Human interrupts: `interrupt()` at Gate 1 and Gate 2
- [ ] Entry points: `/api/ingest` (file → schema_plan), `/api/discover/{sku}` (full loop)

---

## Phase 9: FastAPI Endpoints (Locked Contract)

### `backend/server.py`
- [ ] `GET /api/health` — liveness + version
- [ ] `POST /api/ingest` — upload workbook → schema inference → returns file_id + schema_plan (or needs_human questions)
- [ ] `POST /api/discover/{sku}` — run extraction+audit for one SKU → verdict + cited values
- [ ] `GET /api/state_graph/{sku}` — provenance chain (source_url → evidence → value)
- [ ] `GET /api/conflicts/{sku}` — open Gate 2 items awaiting human
- [ ] `POST /api/resolve` — human resolution → ledger row + `changed_outcome`
- [ ] `WS /ws/ledger_events` — live counter stream
- [ ] `GET /api/ab_compare/{sku}` — finale: A/B + screen-of-truth (stub)
- [ ] `GET /api/ontology/{mfr}` — finale: conflict-precedent overlay (stub)

---

## Phase 10: Tests (48+ Passing)

### Unit Tests
- [ ] `contracts_test.py` — all Pydantic models validate/reject correctly
- [ ] `sqlite_store_test.py` — CRUD for all tables
- [ ] `schema_infer_test.py` — Gemma output parses to SchemaPlan
- [ ] `normalizer_test.py` — Pass A + Pass B with known synonyms/units
- [ ] `audit_test.py` — 5 checks return expected pass/fail
- [ ] `assembler_test.py` — 252-col row matches expected format

### Integration Tests
- [ ] `pipeline_test.py` — full SKU loop with mocked extractors
- [ ] `gate1_test.py` — human interrupt works
- [ ] `gate2_test.py` — human interrupt works
- [ ] `ledger_flywheel_test.py` — precedent hit skips extraction
- [ ] `api_test.py` — all endpoints return correct shapes

---

## Phase 11: Dashboard Integration (Existing UI)

- [ ] Verify `/api/ingest` returns schema_plan + needs_human questions → UI shows Gate 1
- [ ] Verify `/api/discover/{sku}` streams progress → UI shows extraction phases
- [ ] Verify `/api/conflicts/{sku}` returns Gate 2 items → UI shows review queue
- [ ] Verify `/api/resolve` accepts correction → UI updates ledger
- [ ] Verify `WS /ws/ledger_events` streams counters → UI live updates

---

## Phase 12: Configuration & Deployment

- [ ] `.env.example` with all keys: `GEMINI_API_KEY`, `EXA_API_KEY`, `FIRECRAWL_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`
- [ ] `requirements.txt` — all deps pinned (crawl4ai, pdf-reader-mcp-sdk, langgraph, pydantic, fastapi, etc.)
- [ ] Dockerfile for backend (optional)
- [ ] GitHub Actions CI: pytest + tsc + lint + build

---

## Notes

- **No regex/deterministic parse phase** — all extraction via LLMs (Crawl4AI + pdf-reader-mcp + youtube)
- **KB = fuzzy precedent match** — cosine ≥ 0.85 (BGE-M3 later, exact-string v1)
- **Normalization = two LLM passes** — label→key, then unit→canonical + precedence
- **Audit = 5 checks + conformal CI** — no single confidence score
- **Refusal = INSUFFICIENT_EVIDENCE** — never guess, always human gate
- **Cost target = $0** — local LLMs (Gemma via vLLM/Ollama), free tiers, KB dedup