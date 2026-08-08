# SEMI — Competitive Landscape

Field survey of the **published** UniHack 2026 repos, captured **2026-08-08** (between public
push and us going private). 7 repos found via `gh search`; 5 carry substance, 2 are empty.

> Note: this is read-only reconnaissance. We do not copy from any repo; we use the field to
> confirm what nobody has built yet, and to keep SEMI honest about how generic it would look if
> we shipped nothing new.

## The field (7 published repos)

| Repo | Substance | Pipeline one-liner | Input shape | Output |
|---|---|---|---|---|
| `suryaprakashsiddina/unihack-product-intelligence` | strong | LLM extract → Chroma RAG → ddg web → LLM critic → Streamlit approve | PDF / URL / pasted text | JSON/CSV |
| `hrithikeshgoud-ui/veridata-ai-unihack` | medium | extract → dual-agent LLM audit → HITL | PDF / text / URL | structured + citations |
| `jayshreek2511-cloud/unihack` (CommerceAI) | medium | OCR → extract → normalize → dup-detect | PDF / scanned catalog | generic JSON |
| `samriddhitiwary/UniHack` (CatalogIQ AI) | medium-strong | React + FastAPI, DynamoDB, SPEC-001..018 CSV engine | CSV / batch | generic JSON |
| `shubhamanawade125/specforge-ai` | empty | (description only: "Autonomous AI Catalog Extraction") | — | — |
| `di0206-innovator/UniHack` (ProductIntel AI) | thin | AI-Studio UI + FastAPI; **deployed Vercel+Render** | PDF/png/jpg/csv/xlsx | JSON/Excel |
| `Sreevalli20/unihack` | empty | ("# UniHack" only) | — | — |

## The one pattern

Every substantive repo is the **same archetype**:

> *input document → LLM extraction → normalized fields + a confidence number → an approve /
> correct screen.*

The only differences are extraction choices (which LLM, which parser) and which *LLM-critic
loop* validates the output. None of them:

- take the input the brief actually says — `(manufacturer, part_number)` — and go **find** the
  data,
- refuse to ship a value it cannot prove,
- publish measured coverage / refusal numbers, or
- emit anything Unilog's own content business would recognize as "commerce-ready."

## What this means

A generic fight on this axis ends as a coin flip (prompt quality, deck lottery, time-to-build).
The only thing that survives an imitation game is a *non-prompt* capability. That is the input
for [`DIFFERENTIATION.md`](DIFFERENTIATION.md).

## Sources
- Published repos: `gh search repos unihack --sort updated --limit 20`
- Official brief + suggested stack: Hack2skill LinkedIn post, 29 Jul 2026
- Prize + IP + hiring pipeline: Resquare LinkedIn post, 4 Aug 2026
