# Changelog

All notable project and documentation changes for ProcessIQ are tracked here.

## 2026-03-17

### Fix: complete user data deletion

- `DELETE /profile/{user_id}` now deletes ChromaDB embeddings and LangGraph checkpoints in addition to SQLite rows
- Added `delete_user_embeddings()` to `persistence/vector_store.py`
- Added `delete_user_checkpoints(thread_ids)` to `persistence/checkpointer.py`; also extended `delete_thread()` to cover the `checkpoint_writes` table
- Frontend settings drawer now shows a caveat when Ollama is selected, noting that extraction falls back to OpenAI

### Documentation

- Reworked the portfolio-facing documentation set for accuracy, consistency, and cross-linking.
- Corrected setup and deployment guidance to match the actual codebase and CI commands.
- Documented current limitations that were previously implicit.

### Architecture

- Investigation findings now feed back into final confidence and issue severity through the parsed `<investigation_verdict>` block.
- `finalize_analysis_node` adjusts confidence modestly based on investigation evidence and appends the rationale to `confidence_notes`.

### Fixes

- Improvement suggestions now clearly lead with a blocked-analysis message when confidence is below 60%.
- Annual volume extracted from user input is now preserved and used in downstream ROI calculations.
- `/health` now exposes whether LangSmith tracing is effectively enabled, and the UI reflects that in the data/privacy section.
- Empty-state example prompts are now visual only and no longer submit automatically on click.

## 2026-03-16

### Tests

- Added focused unit coverage for `agent/interface.py`, including `extract_from_text`, `analyze_process`, `continue_conversation`, and `AgentResponse` helpers.
- Overall backend coverage increased from roughly 64% to 72%.

## 2026-03-13

### Export

- Replaced the single export action in the UI with a dropdown for Markdown, plain text, and PDF.
- PDF export is rendered server-side with WeasyPrint and returns vector PDF output with selectable text.
- `GET /export/csv/{thread_id}` is available in the API, but remains an API-only capability for now.

### Contracts and UI

- Renamed constraint fields to align Python and TypeScript on `no_new_hires`, `no_layoffs`, and `timeline_weeks`.
- Refreshed the UI theme toward neutral surfaces and a calmer accent system.

## 2026-03-12

### CI/CD

- Added GitHub Actions workflows for backend and frontend checks.
- Added Bandit and detect-secrets to the backend quality pipeline.
- Removed the older Streamlit UI path from the main application surface.
- Completed the cross-session rejection loop so rejected recommendations persist and influence later runs.

## 2026-03-11

### Documentation and Architecture

- Added responsible AI and system-card documents.
- Added the initial ADR set covering LangGraph, ChromaDB, the LLM factory, and the FastAPI + Next.js split.
- Added `memory_synthesis_node` to compress retrieved context before the main analysis prompt.
- Fixed routing so post-analysis follow-up questions use the follow-up prompt path rather than re-running full analysis by default.

## 2026-03-10

### Memory and Retrieval

- Expanded embedded analysis memory with process summaries and issue descriptions for stronger semantic retrieval.
- Added a similarity threshold of `0.4` before retrieved analyses are injected into the analysis path.
- Passed rejection reasons through to retrieved-memory prompt blocks.

### Scope

- Added proposal export support.
- Added annual volume and annualized process metrics.
- Expanded the analysis library data stored in SQLite.
- Added ruled-out recommendations to make constraint reasoning visible.
- Switched the process graph to a left-to-right layout with a minimap.

## 2026-03-09

### Frontend

- Added the analysis library view and the React Flow process graph renderer.
- Fixed `currentProcessData` propagation after analysis completion so later edits stay grounded in the latest extracted data.

## 2026-03-08

### Persistence

- Added SQLite-backed persistence for profiles and analysis sessions.
- Added ChromaDB retrieval scoped by user for cross-session memory.
- Added `GET /profile`, `PUT /profile`, `POST /feedback`, and `context_sources` response data.

## 2026-03-06

- Added the configurable investigation cycle override.
- Hardened FastAPI request handling with rate limits, input caps, file extension whitelisting, and session eviction.

## 2026-03-05

### Platform Shift

- Replaced the earlier Streamlit UI with a FastAPI backend and Next.js frontend.
- Added `/analyze`, `/extract`, `/extract-file`, `/continue`, and `/graph-schema`.
- Introduced the two-phase UI layout and the settings panel.

## 2026-02-27

### Agent Workflow

- Added the bounded investigation loop with tool calling.
- Added `analyze_dependency_impact`, `validate_root_cause`, and `check_constraint_feasibility`.
- Fixed extraction routing so supplementary data is treated as an update instead of a clarification failure.

## 2026-02-17

- Added recommendation feedback capture.
- Added process-data merging across file uploads and text edits.
- Added ROI estimates to recommendations.
- Added step grouping metadata for alternative and parallel paths.

## 2026-02-16

- Expanded the unit test suite substantially.
- Moved structured analysis output to schema-backed parsing instead of manual JSON handling.

## 2026-02-12

- Added progressive disclosure to recommendations.
- Added the `RevenueRange` model used for better business-context calibration.

## 2026-02-06

- Added an LLM provider selector and analysis presets.
- Simplified the LangGraph topology from the earlier draft design.

## 2026-02-05

### Analysis Design

- Formalized the "algorithms for facts, LLM for judgments" analysis approach.
- Added conversational edit support and the analysis prompt architecture that powers the current result format.

## 2026-02-04

- Added per-task LLM configuration.
- Added LangGraph `SqliteSaver` persistence.

## 2026-02-03

### Decision

- Introduced `agent/interface.py` as the stable boundary between the UI/API layer and the graph internals.

## 2026-01-28

### Decision

- Rejected a multi-agent architecture in favor of a single LangGraph workflow with focused nodes.

## 2026-01-27

### Decision

- Chose SQLite plus ChromaDB as the initial persistence stack for Phase 2.

## 2026-01-26

### Decision

- Kept the early design memory-ready even before cross-session persistence shipped.
