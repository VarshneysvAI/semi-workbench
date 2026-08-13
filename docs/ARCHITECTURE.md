# Architecture

Single Eraser flow chart for the full SEMI pipeline. Paste this into an
`eraser.io` document inside a ```er fence to render it.

```er
direction down

legend [position: bottom-left] {
  [color: blue, label: "LLM call (Gemini - free tier)"]
  [color: green, label: "Free / open-source tool"]
  [color: orange, label: "Decision / gate"]
  [color: red, label: "Human-in-the-loop"]
  [color: purple, label: "Persisted data (SQLite)"]
  [shape: cylinder, color: purple, label: "SQLite store"]
}

RawFile [shape: document, icon: file-text, color: blue, label: "Raw Unilog File - CSV/XLSX - any domain - ~1000 rows - 6 cols (MPN - Desc - Brand x3 - Manuf)"]

SchemaDiscover [color: blue, label: "PHASE 1 - Schema Discovery - runs once per file - $0"] {
  ColumnStats [icon: search, color: blue, label: "csv-explorer-mcp - column types - uniqueness - nulls - placeholder ratio - samples (measured facts)"]
  LLMDiscover [icon: zap, color: blue, label: "Gemini structured call - temperature=0 - domain? product_kind? column roles + confidence? attribute blueprint for THIS domain"]
  SchemaPlan [shape: cylinder, icon: database, color: purple, label: "SchemaPlan - persisted in schema_plans - columns to roles - attributes - confidence - needs_human"]
  ColumnStats > LLMDiscover > SchemaPlan
}

HumanAsk [shape: diamond, icon: alert-triangle, color: red, label: "needs_human? (LLM stuck?)"]
HumanAnswer [icon: users, color: red, label: "Human answers - plan updated - never guess"]
SchemaPlan > HumanAsk
HumanAsk > HumanAnswer: yes
HumanAnswer -- SchemaPlan: update plan

Execute [color: green, label: "PHASE 2 - Execute per SKU x blueprint slot"] {
  Deterministic [icon: check-square, color: green, label: "1. Deterministic pass - enum match - last-number qty - uom attach ($0)"]
  KBHit [shape: diamond, icon: database, color: purple, label: "2. Knowledge base hit? - same domain + attribute - conf >= 0.95"]
  WebExtract [icon: globe, color: green, label: "3. Web extraction - agent-reach search chain - Jina Reader fetch (free) - Firecrawl fallback (500 free credits/mo) - Gemini strict-JSON + evidence quote - source_validator blocks marketplaces"]
  SaveCited [shape: cylinder, icon: database, color: purple, label: "4. Persist cited value - value - uom - source_url - evidence_snippet - confidence - extractor"]
  Deterministic > KBHit
  KBHit > SaveCited: hit
  KBHit > WebExtract: miss
  WebExtract > SaveCited
}
HumanAsk > Execute: no

Gate [shape: diamond, icon: check-square, color: orange, label: "PHASE 3 - Gate - confidence x completeness"]
SaveCited > Gate

LovNormalize [icon: settings, color: green, label: "catalog-normalizer MCP - LOV collapse - taxonomy-grounded - provenance: canonicalized / extracted"]
FinalSheet [shape: document, icon: send, color: blue, label: "Final delivery sheet - 252 cols - 5 descriptions from cited slots only - MFR URL + Ref URLs from evidence - Dept/Class/Fine from plan"]
Gate > LovNormalize: high + complete
LovNormalize > FinalSheet

HumanReview [shape: cylinder, icon: users, color: red, label: "Human review queue - pending / approved / rejected / corrected"]
Gate > HumanReview: low / unsure
HumanReview > FinalSheet: decision

Cost [color: green, label: "Cost ledger - full 1000-SKU run"] {
  Cost1 [label: "Gemini: 1 call per file + KB-deduped slot calls - free tier ($0)"]
  Cost2 [label: "agent-reach + Jina + ddgs + exa - local CLIs and free tiers ($0)"]
  Cost3 [label: "Firecrawl: 500 free credits per month - covers ~1000 slots - then Jina"]
  Cost4 [label: "catalog-normalizer MCP - open source ($0)"]
  Cost5 [shape: oval, color: green, label: "Total ~ $0 + Gemini free-tier headroom - KB dedup shrinks calls run-over-run"]
}

Differentiator [color: blue, label: "Why this differs - vs visible 2026 UNIHACK team (ChromaDB seed + Gemini inference, no citations)"] {
  Diff1 [icon: zap, color: blue, label: "Schema discovered by LLM per file - phone file != dishwasher file != belt file"]
  Diff2 [icon: shield, color: green, label: "Every value cited - URL + evidence quote - no invented plausible values"]
  Diff3 [icon: users, color: red, label: "Human gate before anything ships - stuck means ask, never guess"]
}
```
