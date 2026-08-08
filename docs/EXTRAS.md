# SEMI — Demo, Video & Submission Assets

Pitch assets are *support*, not the source of truth (a judge scores the repo + code). Until
submission these are placeholders; they live here so a final-week scramble has one home.

## 90-second demo script (target)
1. **Hook (10s)** — "Given just `(NIBCO, BV-1001)`, SEMI has to find the spec, audit it, or refuse."
2. **Input (10s)** — show the Unilog input row.
3. **Discovery (20s)** — sources surfaced, ranked; missing sources flagged.
4. **Audit + refusal (20s)** — a value refused with `INSUFFICIENT_EVIDENCE`; ledger reason shown.
5. **Resolution → flywheel (20s)** — human picks; ledger row appears; counter `changed_outcome=true`.
6. **Close (10s)** — proof line: "X/10 products · Y% cells sourced · 0 invented."

## 3-minute submission video (max, per rules)
- 0:00–0:30 problem (spec fragmentation; datasheets disagree on the same SKU)
- 0:30–2:30 live demo of the golden path above
- 2:30–3:00 team + roadmap (pilot → standards-grade output)

> Record early; the lablab guideline is explicit: teams that record in the last 6 h lose to a
> broken demo. Final re-record after the schema lands (~Aug 11).

## Brand assets
- `dashboard/public/logo.png` — 1566×1536 wordmark
- `dashboard/public/boot.mp4` — boot animation (3.2 MB final)
- Theme: "Obsidian" black glassmorphic, permanent.

## Submission checklist (per rules)
- [ ] Repo public by submission (private during polish is fine; flip before 23 Aug)
- [ ] Live link: _Vercel_ (dashboard) + _Render_ (backend)
- [ ] 3-min video on a public host
- [ ] Devpost-style fields filled
- [ ] All 3rd-party libs / APIs listed (incl. any AI/ML tools used)
- [ ] `.env.example` only — never `.env`
