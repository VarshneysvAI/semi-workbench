# SEMI Workbench — Execution Plan (latest)

> **One-page standing for report/PPT (2026-08-09, SEMI v1.0, UniHack 2026).**
> Full day-by-day: [`../../TODO.md`](../../TODO.md).

## What runs today (verified)
- **Frontend (React 19, Vite)** — 7-view Obsidian console + Inspector:
  Overview, Sheet, Discovery, Audit, Review Queue, Evidence, Ledger; boot video,
  resizable sidebar, live-engine simulation (copy-on-write, 60fps @ 8×).
- **Backend (FastAPI)** — Excel ingest → state graph → conflict resolver →
  websocket ledger (`changed_outcome` rows); `POST /api/discover/{sku}` runs the
  live hybrid chain and attaches sources + Gemma-extracted candidates.
- **Discovery chain (strict priority, first with hits wins):**
  1. **agent-reach** (CLI, when installed — probe via `doctor --json`/`--help`)
  2. **Firecrawl `/search`** (key; web+pdf categories)
  3. **Exa** (key)
  4. **ddgs** (DuckDuckGo, no key) — always-on last resort; live-verified Aug 9
- **Fetch router (content-type aware, with provenance `fetched_via`):**
  PDF → Firecrawl parsePDF → Jina; WEB → Firecrawl → Jina → bs4;
  VIDEO → yt-dlp subtitles → agent-reach transcribe → Jina.
- **Extraction:** deterministic regex primary; **Gemma single-field via Gemini
  free tier** (`gemma-4-31b-it`, strict-JSON, temp 0.0, live-verified) fills gaps;
  refuses (`LLMNotConfigured` / empty value) rather than fake.
- **Tests:** 23 pytest green, offline-deterministic; CI green (frontend
  tsc+lint+build, backend pytest) on push.

## Remaining execution order
1. **Day 6-7 — adversarial audit engine** ✅ SHIPPED Aug 9: `backend/audit/`
   (physics rules → contradiction → weighted consensus → refusal gate →
   split-conformal intervals), `GET /api/audit/{sku}`, 39/39 tests.
2. Day 8 — resolver UI wiring in dashboard + recovery ledger uplift
   (precedent flywheel, BGE-M3 ≥ 0.85) + feed resolutions into conformal
   calibration.
3. Day 9-10 — precedent retrieval + fallback classifier overlay.
4. Day 11 — measured-stats harness (X/Y sourced, Z% refused, 0 invented).
5. Day 12-13 — deploy (Vercel + Render) once the pipeline is real.
6. Day 14 — pitch video, deck, workflow diagram, submission checklist.

## Decisions locked this sprint
- **LLM channel:** Gemini free tier serves `gemma-4-31b-it` (NIM dropped — slow).
- **Discovery:** never ddgs-only — agent-reach → Firecrawl → Exa → ddgs.
- **No faking:** every value ships `source_url` + provenance; empty beats guessed.

---

# SEMI Workbench — Day 0 Plan

## Goal
A complete, working, smooth UI for the SEMI manufacturer-intelligence console:
black glassmorphic theme (Obsidian, permanent), real logo + boot video, live
engine simulation with honest evidence trails, and — next milestone — real
internet search via agent-reach.

## Current state (verified)
- All 7 routes working: Overview, Sheet, Discovery, Audit, Review queue,
  Evidence, Ledger + side Inspector.
- Resizable/collapsible sidebar (drag splitter, mobile drawer), page
  transitions, boot screen (video + skip, first-visit only).
- Engine: copy-on-write rows, memoized sheet (only touched rows re-render),
  reduced backdrop blur — 60fps at 8x speed.
- Theme: Obsidian only (theme picker removed).
- Boot: `public/boot.mp4` + `public/logo.png` (favicon + sidebar).
- Checks: `npx tsc --noEmit` clean, `npm run lint` (oxlint) 0 errors,
  `npm run build` passes.

## Bug fixes (this session)
- Inspector transcript was cross-contaminated across rows sharing a part
  number -> events now carry `pid` (row id) and are filtered per row.
- Written cells re-triggered their write animation on unrelated re-renders ->
  keyed cell branches (animation only on real writes).
- Performance: copy-on-write engine ticks + `React.memo` sheet rows +
  reduced blur radii + no width transition while dragging.
- A11y: aria-labels on sheet search + manufacturer filter.

## Next milestone: real search with agent-reach
1. `server/app.mjs` — zero-dependency Node bridge exposing:
   - `GET /api/health` — which agent-reach channels are live
   - `GET /api/search?q=...` — Exa search (results: url, title, snippet)
   - `GET /api/fetch?url=...` — Jina Reader page text
2. `vite.config.ts` — repoint `/api` proxy from `localhost:8000` to the
   bridge (currently dead FastAPI target; `/ws` untouched).
3. Engine: async search queue in Discovery (1 req/s, per-PN cache), real
   `source_url` + snippet as evidence; Extraction reads page text and heuris-
   tically finds the attribute; graceful fallback to the simulated flow when
   the bridge or a channel is unavailable.
4. UI: "LIVE / SIM" indicator in the header; live sources get a `verified`
   tick in Evidence + Inspector; ledger rows keep real URLs.
5. Keep `agent-reach` safe mode; channels needing logins (Reddit/Twitter/…)
   stay optional.

## Known config drift (no user impact)
- `package.json` still lists `axios` + `socket.io-client` (unused; FastAPI
  scaffolding). Remove or wire up with the bridge.
- `tailwind.config.js` `glow`/`glow-violet`/keyframes are legacy; harmless.

## Verify before shipping each change
```
cd "D:\c-files\my-project\hackproject new\dashboard"
npx tsc --noEmit && npm run lint && npm run build
```
Dev server: `npm run dev` (http://localhost:5173), HMR log in `dev-server.log`.
