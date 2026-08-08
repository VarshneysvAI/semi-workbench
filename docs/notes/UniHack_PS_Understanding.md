# UniHack — Problem Statement: Complete Understanding

**Challenge:** AI-Powered Product Intelligence for Industrial Commerce
**Organizer:** Unilog (via Hack2skill)
**Purpose of this document:** Explain the problem being asked, in full depth, with supporting evidence. This document does NOT describe any solution or architecture — it is only for building a shared, correct understanding of what is being asked and why.

---

## 1. Official Challenge Text (as published)

> Industrial manufacturers manage vast amounts of product information across websites, catalogs, technical documents, and digital assets. Transforming this fragmented data into accurate, structured, and commerce-ready product intelligence is a complex and time-consuming process.
>
> Participants are challenged to build an AI-powered solution that can automate the creation, enrichment, and validation of product intelligence from limited product information.
>
> Solutions can explore approaches such as AI agents, RAG, knowledge graphs, document intelligence, vision-language models, and human-in-the-loop workflows to improve accuracy, scalability, and explainability.

**Expected Outcomes (stated verbatim in the portal):**
1. Generate structured product intelligence from limited inputs
2. Improve product data quality and consistency
3. Validate and enrich information with traceable outputs
4. Scale efficiently across large product catalogs

---

## 2. Who Is Asking This, and Why It's Not a Generic AI Prompt

This challenge is written by **Unilog**, a company that has run B2B product-content and commerce software since 1998 (Wayne, PA, USA; owned by Investcorp). Their core product is the **CX1 Platform**, which includes a module called **CX1 PIM** (Product Information Management).

Facts about their scale and business:
- They maintain relationships with roughly 10,000 manufacturers and provide access to over 10 million vendor-managed SKU assets.
- Their customers are B2B distributors in industries like HVAC, plumbing, pipe-valve-fittings (PVF), electrical supply, industrial supply, and construction materials.
- Their own marketing describes the core customer pain as managing large SKU counts, correcting data inconsistencies, and manually moving data between systems — this is nearly a word-for-word match to the challenge statement.

This means the challenge is not an abstract exercise — it maps directly onto a problem Unilog's paying customers already have.

---

## 3. Unilog Already Uses AI — This Changes What "Winning" Means

Unilog has a live product called **HyperScale**, an in-platform suite of AI agents (early access since October 2025). Two agents are confirmed live as of mid-2026:

- **Synonym Agent** — scans search behavior, finds gaps, suggests synonyms for admin review.
- **Product Description Agent** — finds products with missing/weak descriptions and generates descriptions and keywords **using data already in the catalog**.

A separate agent set, **HyperScale AWC (Autonomous Work Completion)**, automates operational workflows: PunchOut, onboarding, quote processing, fraud detection, catalog merchandising.

**Critical detail:** every one of these agents operates on data that is *already structured and already in the catalog*. None of them take raw, scattered, incomplete source material (a PDF, an image, a manufacturer webpage) and turn it into a structured record in the first place.

**This is the actual gap the hackathon is targeting** — the step *before* any of Unilog's existing AI can act. The challenge is not "build any AI system," it's "solve the specific piece of this pipeline Unilog has not automated yet."

One more fact worth noting for context: Unilog's own public material states their AI agents **"never publish anything without approval."** This is a stated design philosophy at the company, not just a hackathon suggestion — a submission's approach to trust/approval should be read against this.

---

## 4. Line-by-Line Breakdown of the Challenge Text

| Phrase | Literal meaning | Why it matters |
|---|---|---|
| "Product **Intelligence**" (not "product data") | A level above raw fields — implies some reasoning/inference, not just field extraction | Sets the bar above simple extraction |
| "**accurate**, structured, and **commerce-ready**" | Three separate bars: correctness, format, and publish-readiness | "Commerce-ready" is a distinct, extra requirement — not just "correct JSON" |
| "complex **and** time-consuming" | Two separate problems: difficulty AND speed | Speed/efficiency is explicitly part of the ask, not a bonus |
| "**automate** the creation, enrichment, and validation" | Three ordered steps: create → enrich → validate | Validation is framed as occurring after creation/enrichment, i.e. as a gate |
| "validate and enrich information with **traceable** outputs" | Every value must be attributable to a source/method | This is the concrete, buildable definition of "explainability" in this PS — not a vague concept |
| "Scale **efficiently**" | Not just "can it scale" but "at reasonable cost/speed per item" | Cost/throughput is a real evaluated dimension, evidenced directly by this word |
| "**Improve** product data quality and consistency" | Word choice implies correcting/reconciling *existing* messy data too, not only generating new records | Broadens scope beyond "new product onboarding" to "cleanup of existing catalog" |
| "knowledge graphs" listed explicitly | Named as an expected approach category, not just an example | Suggests relationship-based/graph modeling is a favored technique, not incidental |

---

## 5. What the PS Leaves Unspecified (real ambiguity, not solved by reading closer)

- Exact format of "limited product information" for testing — one photo? A partial spec sheet? A bare product name? Not defined.
- No sample dataset or schema is provided by Unilog for this hackathon (as of this document).
- No explicit definition of what "explainable" output should look like beyond the word "traceable."
- No stated minimum accuracy/consistency threshold — quality bar for judging is not numeric.

These are open questions that require independent research/decisions, not something extractable from the text itself.

---

## 6. Supporting Domain Research (context, not solution)

**Industry standards exist for exactly this kind of product data.** ETIM, eCl@ss, and UNSPSC are established classification systems used in industrial/technical commerce that define fixed attribute dictionaries per product category (permitted units, data types, valid values). Their existence is a fact independent of any solution choice — they are part of the real-world problem space Unilog operates in.

**This exact technical problem has been benchmarked recently.** A June 2026 benchmark (arXiv 2606.14383, "IndustryBench-MIPU," from Alibaba) tested AI models on recovering structured attribute-value pairs from industrial product images (spec tables, nameplates, technical drawings). Finding: even the best models reach 86–94% precision on single images, but only recover roughly half of all attributes at the full-product level, and accuracy drops significantly (15–34 percentage points) when evidence must be combined across multiple images/sources. This confirms, with evidence rather than assumption, that the "validation/consistency across scattered sources" part of the challenge is a genuinely unsolved, active research problem — not something already solved by calling an LLM API.

---

## 7. Logistics (facts, for reference)

- **Prize pool:** ₹5,00,000 total (Winner ₹2,00,000 / 1st Runner-up ₹1,50,000 / 2nd Runner-up ₹1,00,000 / two Special Awards ₹25,000 each)
- **Team size:** 1–4 (solo permitted)
- **Eligibility:** Undergraduate engineering students, India
- **Timeline:** Registration & submission: 29 Jul – 23 Aug 2026 · Evaluation: 24 Aug – 1 Sep 2026 · Finale/results: 4 Sep 2026
- **Evaluation criteria (stated):** innovation, technical implementation, business relevance, overall impact
- **IP clause:** IP rights for **winning** solutions transfer to the organizers upon confirmation of award
- **Possible outcome beyond prize money:** top performers may be considered for internships, PPOs, or full-time roles at Unilog

---

## Sources
- unilogcorp.com (platform/product-content, hyperscale, homepage)
- natlawreview.com / cbs42.com — Unilog HyperScale press release, Oct 2025
- unilogcorp.com/resources/blog-posts — "AI Belongs in Your Workflows, Not on Your To-Do List" (June 2026); "Before We Ask You to Automate, Here's What We Automated" (May 2026)
- hawksearch.com — Unilog CX1 CIMM2 integration page
- arXiv 2606.14383 — IndustryBench-MIPU benchmark (June 2026)
- Hack2skill UniHack event portal (challenge text, prizes, timeline, FAQs)

---

*This document is intentionally solution-free. Its only purpose is to make sure everyone working on this starts from the same, evidence-checked understanding of what is actually being asked.*
