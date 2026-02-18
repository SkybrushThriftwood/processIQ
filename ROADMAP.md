# ProcessIQ Roadmap

Phase 1 (MVP) is complete. This document describes what comes next and why.

For the detailed reasoning behind these decisions — market positioning, adoption patterns, feature trade-offs — see [docs/PRODUCT_STRATEGY.md](docs/PRODUCT_STRATEGY.md).

---

## What Phase 1 Delivers

A working analysis pipeline, chat-first interface, and session-scoped feedback loop. The agent can:

- Extract process data from text, CSV, and Excel files
- Identify bottlenecks and core value work through LLM judgment on deterministic metrics
- Generate constraint-aware recommendations with ranged ROI estimates
- Incorporate within-session feedback (rejected recommendations are not repeated)
- Persist conversations across browser refreshes

What it cannot do: remember anything across sessions, produce output that leaves the tool, search for context beyond what you provide, or stream responses.

---

## Phase 2 — Memory, Context, and Shareable Output

**Theme:** The agent starts fresh every session and produces output that stays inside the tool. Phase 2 gives it memory and makes its results leave the room.

---

### 2A — Cross-Session Feedback Loop

The feedback mechanism exists (thumbs up/down per recommendation) but is session-scoped. When you restart, the agent forgets what you liked and rejected.

**Work:**
- Persist `recommendation_feedback` to SQLite keyed by user ID
- On session start, load historical feedback alongside current analysis
- Extend `analyze.j2` to distinguish within-session feedback (explicit) from historical patterns (softer signal)
- On return session, prompt: "Last time we recommended [X]. Did you implement it? What changed?" — hooks into the feedback record and begins closing the outcome loop

**Why now:** The infrastructure is already in place — `user_store.py` manages UUID identity, `checkpointer.py` wraps SqliteSaver. This is the shortest path to a genuinely learning agent.

---

### 2B — Persistent Business Profile

Currently the business profile (industry, company size, regulatory level, etc.) must be re-entered every session. It belongs to the user, not the conversation.

**Work:**
- Add a `UserProfile` table to SQLite: stores industry, size, constraints, preferences
- Auto-populate sidebar fields from stored profile on session start
- Update profile when user changes fields or when the agent infers new facts from conversation
- Version profile updates so changes don't silently overwrite past values

**Why this matters:** Business context is what separates useful recommendations from generic advice. Losing it every session degrades recommendation quality for returning users and makes the tool feel like it never learns who you are.

---

### 2C — Process Visualization

After extraction, users see a table of steps. What they often actually want is: "show me where the bottleneck sits in the flow."

**Work:**
- Add an interactive flowchart view to the results display using Plotly or Mermaid
- Nodes sized by time or cost, colored by severity (green → red)
- Bottleneck nodes annotated with the linked issue
- Show dependency chains (`depends_on` is already in `ProcessStep` — this is a rendering problem, not a data problem)
- Exportable as PNG for reports and presentations

**Why Phase 2 (not Phase 3):** Visual output is the primary thing people screenshot and share. A process flowchart with bottlenecks highlighted is more immediately convincing than a text summary, and it is the difference between results that stay in the tool and results that get presented in a meeting. The dependency data is already captured — this is lower-effort than it appears.

---

### 2D — PDF/HTML Report Export

ProcessIQ currently exports CSV and markdown — functional for follow-up actions, but not the kind of output that gets shared with stakeholders.

**Work:**
- Generate a structured report: process diagram, executive summary, top issues, recommendations with ROI ranges, confidence level, explicit assumptions
- Two format targets: HTML (rendered in browser, can be saved/printed) and PDF (via `weasyprint` or `pdfkit`)
- Report is generated from the existing `AnalysisInsight` model — no new analysis needed, only rendering

**Why this matters:** Word-of-mouth in professional settings happens when someone forwards a document to their manager. A well-designed report gets shared; a Streamlit page does not. This is the highest-impact driver of organic growth for a tool in this category. See [docs/PRODUCT_STRATEGY.md](docs/PRODUCT_STRATEGY.md) for full reasoning.

---

### 2E — Docling UI Exposure

Docling is already integrated in the codebase (`ingestion/docling_parser.py`) but the UI only accepts CSV and Excel. PDF, DOCX, PowerPoint, and images are parsed by the same pipeline — they just need to be wired to the file upload handler.

**Work:**
- Extend the file upload handler to accept `.pdf`, `.docx`, `.pptx`, `.png`, `.jpg`
- Route these file types through `docling_parser.py` → existing LLM normalization path
- Update the UI file picker to reflect accepted formats
- Test against realistic documents: process SOPs, audit reports, slide decks with process flows

**Why now:** This is low implementation effort (the parsing infrastructure exists) and opens a significant use case. Users in finance, legal, and operations typically have process documentation in PDFs or Word documents — not CSV files. Supporting these formats removes the biggest input friction for professional users.

---

### 2F — ChromaDB RAG for Analysis History

Users who run repeated analyses (e.g. comparing processes across departments) currently have no way to retrieve past work as context.

**Work:**
- Add ChromaDB alongside SQLite (already in `pyproject.toml`, commented out)
- Embed past process descriptions and analysis results as vectors
- On new analysis, retrieve semantically similar past analyses and surface relevant context: "you analyzed a similar invoicing process in March — that one had a 40% rework rate at the legal step"
- Source attribution: results cite which past analyses informed recommendations

**Design constraint:** RAG is additive context, not a replacement for the current analysis pipeline. The core `check_context → analyze → finalize` graph does not change. Retrieved context is injected as additional input to `analyze.j2`, not a separate code path.

---

## Phase 3 — Depth and Scale

**Theme:** Results that go deeper, analysis that runs faster, and a foundation for larger inputs.

---

### Process Templates

Pre-built process templates (invoice approval, employee onboarding, bug triage, procurement, support ticket handling, etc.) with realistic baseline values pre-filled.

**Work:**
- Define 20–30 template process definitions in JSON: step names, typical durations, common dependencies, industry context
- "Start from a template" flow: user selects a template, sees it pre-populated in the data table, adjusts to match their actual process
- Templates carry baseline values that function as embedded benchmarks — no separate benchmark database needed for common processes
- Templates are also the primary demo content for new users who don't have a process ready to describe

**Why this matters:** This is the primary lever for reducing time-to-value for new users. Without it, a new user must have a process in mind, describe it accurately, wait for extraction, and review the result before seeing any value. With templates, they can load a familiar process and see results immediately. See [docs/PRODUCT_STRATEGY.md](docs/PRODUCT_STRATEGY.md) for analysis.

---

### Streaming Responses

LLM responses currently block until complete. For deep analysis with GPT-4 or Claude Opus, this means 10–20 seconds of waiting with no feedback.

**Work:** Replace blocking `model.invoke()` calls with streaming in the analyze node. Streamlit supports `st.write_stream()`. The main complexity is partial `AnalysisInsight` rendering — the UI needs to show a useful partial state while the structured output is still being assembled.

---

### Outcome Tracking

ProcessIQ generates recommendations but never knows if they were implemented or what happened. This breaks the learning loop at the most important point.

**Work:**
- After analysis, ask the user which recommendations they plan to implement (simple checklist, not required)
- On return sessions, surface those commitments: "Last time you said you'd try automating approval routing. Did you?"
- Store outcomes (implemented / not implemented / partial + optional impact note) in SQLite keyed to the recommendation and user ID
- Feed confirmed outcomes back into `analyze.j2` as high-confidence signals — stronger weight than preference feedback alone

**Why this matters:** Recommendation preferences tell the agent what users *like*. Outcomes tell it what actually *worked*. These are different signals. An agent that learns from outcomes rather than just preferences will calibrate recommendation quality over time, not just recommendation style.

---

### Benchmark Comparison (Opt-In)

A "how does our process compare?" feature, triggered explicitly by the user — not automatically appended to every analysis.

**Work:**
- Curated benchmark database for common process types (hiring, invoicing, onboarding, etc.) stored locally — no external API calls
- "Compare to benchmarks" button in results triggers a second LLM call with the benchmark data as context
- Output: specific gaps vs benchmark, not generic "industry average" noise

**Note:** Phase 3 process templates partially cover this — templates carry baseline values that serve as implicit benchmarks for common processes. Formal benchmark comparison adds value for less common or highly specific process types.

**Design principle:** Only fetch external context when the user explicitly asks. Relevance over comprehensiveness.

---

### Fine-Tuning for Extraction

The extraction path (`extraction.j2` + Instructor) has a well-defined input/output contract: raw text or file content in, valid `ProcessData` JSON out. This is the strongest candidate for fine-tuning in the codebase.

**Trigger condition:** Only worth doing if there is concrete evidence of failures — repeated Instructor retries, schema mismatches on common input patterns, or extraction cost becoming significant at scale. Don't do it speculatively.

**Work:**
- Collect 100–200 (input description, correct `ProcessData` extraction) pairs from real or realistic process descriptions
- Fine-tune a smaller model (`gpt-4o-mini` or an open-weights equivalent) on these pairs
- The fine-tuned model handles extraction; the stronger base model stays on analysis
- `extraction.j2` can be shortened significantly — few-shot examples move into weights

**What this buys:** Lower cost and latency on every extraction call. A fine-tuned `gpt-4o-mini` can match `gpt-4o` quality on this narrow, schema-constrained task.

**What it doesn't buy:** Better judgment. Fine-tuning teaches format and style, not reasoning. The analysis path stays with the strongest available model and full prompt engineering.

**Constraint:** When `ProcessData` schema changes (new fields, changed types), the fine-tuned model needs retraining. Factor this maintenance cost into the decision.

---

### Frontend Migration

Streamlit was the right choice for rapid prototyping — zero boilerplate, built-in chat components, fast iteration. But it has real constraints that will become friction as the product matures: limited control over layout and styling, no native websocket support for streaming, and a programming model that reruns the entire script on every interaction.

**Trigger condition:** When the UI needs something Streamlit can't do cleanly — true streaming output, richer process visualization, or a more polished visual design.

**Candidates to research:**
- **FastAPI + React/Next.js** — full control, standard web stack, significant extra complexity
- **Gradio** — similar to Streamlit but more component-focused; unlikely to solve the root constraints
- **Reflex** — Python-native reactive UI, closer to React's model without writing JS; worth evaluating
- **Panel/Holoviz** — stronger for data-heavy dashboards, weaker for chat-first interfaces

**What a migration looks like:** The UI layer is already isolated behind `agent/interface.py` — the agent doesn't know or care what renders it. A migration is a frontend replacement, not an architecture change. `handlers.py` and `state.py` would need to be rewritten for the new framework, but `agent/`, `analysis/`, `ingestion/`, and `export/` are untouched.

**No decision made yet.** Research needed before committing to a direction.

---

## What Is Not on the Roadmap

**Web search / real-time external data** — latency, cost, and reliability concerns outweigh the benefit for most use cases. Curated benchmarks and templates are more controllable and predictable.

**Multi-user collaboration** — ProcessIQ's value is in single-user depth, not team coordination. Shared analyses would require auth, permissions, and conflict resolution — significant infrastructure for unclear benefit at this stage. The report export (2D) covers the primary "share with my manager" need without requiring a multi-user system.

**Fine-tuning for analysis** — prompt engineering via `analyze.j2` is faster to iterate and easier to inspect than fine-tuning for the judgment-heavy analysis path. That stays prompt-driven.

**Mobile app** — process analysis is a desk activity. Users are reviewing tables, editing step data, and reading detailed recommendations. The Streamlit interface is not mobile-appropriate and a mobile redesign would be a separate product.

**Email notifications / reminders** — requires SMTP, auth, and consent infrastructure disproportionate to the value. Outcome tracking (Phase 3) achieves the same behavioral loop within the existing session model.

---

## Sequencing Rationale

| Priority | Item | Why |
|----------|------|-----|
| 2A first | Cross-session feedback | Shortest path from "session-scoped" to "learning agent". Infrastructure already exists. Adds outcome prompt hook. |
| 2B second | Persistent business profile | Business context is the primary driver of recommendation quality. Session loss degrades every analysis for returning users. |
| 2C third | Process visualization | Dependency data already exists. Visual output is what gets shared and presented. Enables report export. |
| 2D fourth | PDF/HTML report export | Requires visualization to be worth generating. Highest driver of organic growth — reports get forwarded. |
| 2E fifth | Docling UI exposure | Low effort (parser exists). Opens the professional-user use case (SOPs, audit docs, slide decks). |
| 2F sixth | ChromaDB RAG | Highest infrastructure cost in Phase 2. More valuable once profile and feedback persistence are validated. |
| Templates | Phase 3 | Highest impact on new-user time-to-value. Requires defining and curating the template library. |
| Streaming | Phase 3 | High perceived impact, moderate implementation complexity. Worth doing once memory features are solid. |
| Outcome tracking | Phase 3 | Requires return users to exist first. Meaningful once 2A–2B create a returning-user population. |
| Benchmarks | Phase 3 | Templates partially cover this. Formal benchmark comparison adds value for non-standard processes. |
| Fine-tuning | Phase 3 | Only if extraction failures or cost are a demonstrated problem at scale. |
| Frontend migration | Phase 3+ | Research needed first. Only when Streamlit's constraints actively block required features. |
