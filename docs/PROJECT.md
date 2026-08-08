# SEMI — Project Brief

> UniHack 2026 · AI-Powered Product Intelligence for Industrial Commerce
> Organizer: **Unilog** (via **Hack2skill**) · Submission **23 Aug 2026** · Finale **4 Sep 2026**
> Team size 1–4 · virtual · IP of winners transfers to Unilog · top performers considered for internships / PPO / full-time.

## The problem (verbatim)

> Industrial manufacturers manage vast amounts of product information across websites,
> catalogs, technical documents, and digital assets. Transforming this fragmented data into
> accurate, structured, and commerce-ready product intelligence is a complex and time-consuming
> process.
>
> Participants are challenged to build an AI-powered solution that can automate the creation,
> enrichment, and validation of product intelligence **from limited product information**.

**Expected outcomes (official):** (1) structured product intelligence from limited inputs,
(2) improved product data quality & consistency, (3) validated & enriched information with
**traceable outputs**, (4) scale efficiently across large product catalogs.

**Input we are scored against:** a minimal Excel row — `(manufacturer, part_number)` plus a
short description. The official Unilog output schema is released ~Aug 11; we treat its arrival
as our Day-1 GATE and do not over-fit to a guessed schema.

## What SEMI is

SEMI = **Self-Evolving Manufacturer Intelligence**. Given just `manufacturer + part_number`,
SEMI **discovers** manufacturer sources, **extracts** multi-format evidence, **adversarially
audits** every value, and emits **schema-bound** output — or **refuses to ship** with
`INSUFFICIENT_EVIDENCE` rather than guessing. Every emitted value carries `source_url` and,
where deterministic, a `95% split-conformal` interval. Human resolutions are stored as a ledger
row whose "precedent" tilts later audits — the **flywheel** that gives the system its name.

## Judging rubric (the 4 axes — equal 25% each)

| Axis (25%) | What it rewards | Where SEMI scores |
|---|---|---|
| **Innovation** | a new take, not "LLM over a PDF" | discovery-from-minimal-input + refusal gate + 2-pass ledger flywheel (no submitted team has any of these) |
| **Accuracy** | traceable, low-hallucination output | adversarial audit + conformal interval + **no value without `source_url`** + refusal on thin evidence |
| **Quality** | code, contract, UX polish | typed FastAPI + pytest suite + React 19 console with inspector + boot path, not a Streamlit grid |
| **Scalability** | works at catalog scale, not one demo SKU | batch ingest + WS streaming + measured coverage / refused-per-100 stats in the repo |

See [`docs/DIFFERENTIATION.md`](DIFFERENTIATION.md) for the field-by-field read and
[`docs/notes/`](notes/) for the full internal research log.

## Honest limitations (we will not hide these)

- Today the audit engine, discovery, conformal calibration, refusal gate and Gemma extraction
  are **roadmap, not shipped** (Day-by-day mapping in [`../TODO.md`](../TODO.md)).
- Cost figures in any deck are **structural estimates**, not audited financials.
- `changed_outcome` precedent match is currently exact-string; the BGE-M3 retrieval layer is
  Day 9–10.
- Dashboard runs in **simulation mode** against seed data until the backend + Gemma path lands.

## Status table (premium repos don't fake it)

| Capability | Today | Pending dataset / build |
|---|---|---|
| 7-view React console + sim engine | ✅ | — |
| FastAPI state-graph + resolver + WS ledger + 5/5 tests | ✅ | — |
| Unilog `output_mapper` (DAY3 markers) | ✅ prep | wire to official schema ~Aug 11 |
| Autonomous discovery | ⛳ roadmap | after schema lands |
| Adversarial audit + conformal CI + refusal gate | ⛳ roadmap | after discovery |
| Gemma extraction client | ⛳ roadmap | awaits API key |
| Measured proof in README | ⛳ roadmap | once eval set is fixed |
