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
