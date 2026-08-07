# SEMI — Self-Evolving Manufacturer Intelligence

**UniHack 2026 · AI-Powered Product Intelligence for Industrial Commerce**

Given a minimal Excel input `(manufacturer, part_number)`, SEMI autonomously
discovers manufacturer sources, extracts multi-format evidence, adversarially
self-audits each value (physical constraints, cross-source contradiction,
compositional consistency, disproof search, conformal 95% coverage), and emits
values bound to the Unilog output schema — or refuses with `INSUFFICIENT_EVIDENCE`.

## Stack

- **Backend** — FastAPI + SQLite (backend). Discovery via Playwright,
  extraction deterministic-first with a local Gemma 4 12B fallback,
  BGE-M3 embeddings for contradiction search.
- **Frontend** — React + TypeScript + Vite + Tailwind, five console views.

## Run

```bash
# backend (Python 3.11 venv)
uv venv --python 3.11
uv pip install -r backend/requirements.txt
uv run uvicorn backend.server:app --reload --port 8000

# frontend
cd dashboard && npm install && npm run dev   # http://localhost:5173
```

## Docs

- Plan &amp; build checklist: `TODO.md`, `UniHack_Final_Plan.md`
- `docs/api_contract.md` — FastAPI ⇄ dashboard contract