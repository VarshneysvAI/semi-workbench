# SEMI — Differentiation (the "real" version)

> This is the document the user asked for: **SEMI vs the published repos — assuming we actually
> ship our proposal**, not the today-state deckware. Each row says (a) where we differ, (b)
> which judging axis it scores on, and (c) honestly, whether it is shipped today or is a
> commitment.

Judging rubric (UniHack 2026, equal 25% each): **Innovation · Accuracy · Quality · Scalability**.

## Theurette — SEMI vs the field, head-to-head (build-complete view)

| Axis the brief rewards | Every submitted repo (5 substantive) | SEMI (build-complete) | Rubric pole |
|---|---|---|---|
| **Input treated as stated** — `(manufacturer, part_number)` | None. They all require the source doc *(PDF / URL / scan)*. They skip the hard part. | Discovery first: from SKU + brand, search `site:manufacturer` + marketplaces, rank authority, missing sources flagged. **The only team answering the brief as written.** | Innovation + Scalability |
| **Refusal instead of low-confidence guessing** | None. They "flag low confidence for review" but still ship a value. | A value with thin evidence is **rejected** with `INSUFFICIENT_EVIDENCE`; the cell stays empty, not guessed. Judges instantly get "this one didn't fake it." | Innovation + Accuracy |
| **Audit that is math, not a second LLM guess** | VeriData's anti-hallucination = an LLM auditor agent (same hallucination surface). | Physical/physics constraint rules + cross-source contradiction + **split-conformal 95% CI** `[lo, hi]` per cell. Verifiable, testable. | Accuracy + Quality |
| **Every value carries `source_url` + interval** | Most cite the source but no quantified interval. | No value ships without `source_url`; conformal CI on values where deterministic. The default "why did you output this?" question is answered in code. | Accuracy + Quality |
| **Output that is commerce-ready, not JSON** | Generic JSON / CSV. | Unilog's own output schema (`output_mapper.py` with DAY3 markers). When the official schema drops (~Aug 11), we wire Day-3 to it directly — others re-mass JSON. | Quality + Scalability |
| **The flywheel — `changed_outcome` precedent** | None. They have approve/correct loops; none store the resolution so the next audit changes. | A human resolution is a ledger row (`source_url`, reason tags). A later near-duplicate SKU matches the precedent (BGE-M3 cosine ≥ 0.85) and the audit tilts before the human looks. **This is the "Self-Evolving" in our name**, and the hardest thing to copy in 3 days. | Innovation + Scalability |
| **Measured proof, in the repo, before the demo** | None publish numbers. | README ships coverage stats: `X/10 products · Y% of cells sourced · Z% refused · 0 invented`. The "no-number-without-a-source" promise, quantified. | Accuracy + Scalability |
| **Premium UX vs Streamlit grid** | Streamlit tables for 4 of 5 substantive teams. | React 19 console: 7 views, resizable sidebar, inspector panel, boot animation — UI you can screenshot for the deck in 10 seconds. | Quality |

## What the field *has* that we do *not* (honest)

- They can already run an end-to-end extraction on a real PDF today (Streamlit); our dashboard
  currently runs in **simulation** against seed data. This is the gap the Day-4–7 sprint closes.
- One repo (`di0206-innovator`) is already **deployed live** (Vercel + Render). We plan to deploy
  the same targets once the pipeline lights up — not before, so we don't ship a fake live URL.
- They have a second LLM-critic loop now; our math-based audit is still roadmap. We trade
  immediate parity for a stronger moat — but the moat must ship.

## The one-line positioning (use everywhere)

> Every team extracts product data. SEMI is the only submission that **starts from the actual
> industry input** (`part_number` + `brand`), **refuses to guess**, and **learns from each
> resolution** — measurable proof in the repo, not a prompt wrapping a PDF.

## Status legend (no faking)

- ✅ shipped today: FastAPI state-graph + Excel ingest + conflict resolver + WS ledger +
  `changed_outcome` ledger rows + 5/5 pytest + the 7-view console + `output_mapper` prep.
- ⛳ committed build (roadmap until the official schema + Gemma API land ~Aug 11): discovery,
  5-check audit + conformal CI, refusal-gate enforcement, Gemma client, measured-stats harness.
- See [`../TODO.md`](../TODO.md) for the day-by-day schedule and [`PROJECT.md`](PROJECT.md) for
  the rubric mapping.

## Why this is hard to copy in a sprint

The lead is not "we call a different API." It is: a *retrieval-led audit*, a *refusal regime*,
and a *resolution ledger that becomes precedent*. Each is a systems feature with a data shape
(other teams have no ledger row, no precedent index, no conformal calibration). The window in
which a competitor could re-architect to add all three is the same window in which they also have
to ship, deploy, and record a video. That is the moat.
