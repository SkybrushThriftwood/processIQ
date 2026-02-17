# Changelog

All notable design decisions and changes to ProcessIQ are documented here.

Format: `[YYYY-MM-DD] Category: Description`

Categories: `DESIGN`, `ARCHITECTURE`, `SCOPE`, `TECH`, `DECISION`

---

## 2026-02-17

### ARCHITECTURE: File Upload Merging

- File uploads now merge with existing process data instead of replacing it. Matching steps (by name, case-insensitive) have their values updated; new steps are appended; existing-only steps are preserved.
- Added `ProcessData.merge_with()` method. Fields overwritten by file data are removed from `estimated_fields` (no longer marked as AI-estimated).
- Enables the workflow: describe process in text -> upload spreadsheet with costs -> merged table ready for analysis.

### FIX: Extraction Model Selection for OpenAI

- Switched extraction and clarification tasks from `gpt-5-nano` (reasoning model) to `gpt-4o-mini` across all analysis modes. Reasoning models burned 12k+ tokens on internal chain-of-thought for simple schema-filling tasks, causing slow responses and occasional empty outputs when the reasoning budget was exhausted.
- Analysis and explanation tasks still use reasoning models where deeper thinking adds value.

### FIX: Multiple Bug Fixes

- **Asterisk on user-edited values**: Table edits now remove fields from `estimated_fields` when the user changes a value, preventing false AI-estimated markers.
- **Duplicate logging**: Replaced module-level `_logging_configured` flag with `app_logger.handlers` check. The flag reset on every Streamlit rerun, causing handler accumulation (2-4x log messages).
- **OpenAI zeros vs blanks**: Strengthened extraction prompt to explicitly require every "not provided" zero to be listed in `estimated_fields`. Anthropic inferred this; OpenAI needed it spelled out.
- **File stays in uploader**: Increment file upload key counter after processing to clear the widget.
- **Follow-up answers hidden**: In CONTINUING state, analysis results now collapse into an expander so follow-up conversation stays visible.

### DESIGN: ROI Estimates on Recommendations

- Added `estimated_roi` field to `Recommendation` model for rough dollar-range estimates.
- Analysis prompt instructs LLM to calculate ROI from actual process data (time x cost, error reduction) rather than inventing figures.
- Displayed with styled callout and "(rough estimate)" label below each recommendation.

### DESIGN: Step Numbering with Alternative/Parallel Group Support

- Added `group_id` and `group_type` fields to `ProcessStep` and `ExtractedStep` models. `group_type` is either `"alternative"` (either/or, e.g., phone OR email) or `"parallel"` (simultaneous, e.g., invoice paid AND tax entry).
- New "Step #" column in the data table with computed numbering: sequential steps show "1", "2", "3"; alternatives show "1a (OR)", "1b (OR)"; parallel steps show "5a (AND)", "5b (AND)".
- Updated extraction prompt with grouping detection instructions and examples.

---

## 2026-02-16

### CODE: Comprehensive test suite (265 tests)

- Created 19 test files covering models, analysis algorithms, agent routing, ingestion loaders, exports, prompts, exceptions, and LLM utilities.
- Coverage: models 100%, analysis 90–100%, agent/edges 100%, ingestion 81–94%, exports 81–100%, exceptions 100%.
- Added `pytest-cov` dev dependency and `@pytest.mark.llm` marker for LLM-dependent tests.

### DESIGN: Post-Analysis Follow-Up Conversation

- Follow-up questions after analysis were previously handled by regex string matching with a canned response. Now routes all follow-up questions to the LLM with full analysis context, chat history, business profile, and constraints.
- New prompt template `followup.j2` for follow-up conversation context.
- Analysis results panel no longer disappears when a follow-up message is sent.

### CODE: Efficiency and Workflow Optimizations

- **Graph compilation caching**: Module-level cache prevents recompiling the LangGraph on every analysis call.
- **Parallel post-extraction LLM calls**: Improvement suggestions and draft analysis run concurrently via `ThreadPoolExecutor`.
- **Structured output for analysis**: Replaced manual JSON parsing with `with_structured_output(AnalysisInsight)`, removing ~50 lines of brittle parsing code.
- **Instructor client caching**: Clients cached at module level instead of recreated per call.
- **Transitive closure fix** (`metrics.py`): Fixed shared visited set causing exponential blowup on reconvergent DAGs.
- **Dead code removal**: Removed 15 unused form-based session state functions, 7 unused `_STATE_DEFAULTS` keys, and a renderer that never ran.

---

## 2026-02-12

### DESIGN: Progressive Disclosure on Recommendations

- Added `plain_explanation` and `concrete_next_steps` fields to `Recommendation` model.
- Updated results display with two new expander sections per recommendation: "What this means in practice" and "How to get started."
- Both compact (issue-linked) and standalone recommendation renderers updated.

### DESIGN: Business Context for Calibrated Recommendations

- **Problem**: Recommendations like "automate this for $15–50k/year" are meaningless without business scale context. A 3-store bakery and a 1000-person enterprise get the same generic suggestions.
- **Solution**: Added revenue range, free-text business notes, and full business profile threading into the analysis prompt.
- Added `RevenueRange` enum to `BusinessProfile` (8 tiers from "Under $100K" to "Over $100M" plus "Prefer not to say").
- Surfaced revenue dropdown and "About Your Business" text area in sidebar.
- Built `_format_business_context_for_llm()` in `nodes.py` to serialize full profile into LLM-readable format.
- Updated `analyze.j2` to receive `business_context` (replaces bare `industry` string) with explicit instruction to calibrate costs to business scale.

### FIX: GPT-5 Series and Cross-Provider Model Resolution

- GPT-5 and o-series models reject `temperature!=1` and `max_tokens`. Added `is_restricted_openai_model()` helper; applied in both LangChain and Instructor code paths.
- Fixed cross-provider model bug where selecting "anthropic" in UI but having `LLM_PROVIDER=openai` in `.env` caused the wrong model to be used.
- All call sites in `graph.py` and `interface.py` now thread `provider` and `analysis_mode` through correctly.

---

## 2026-02-06

### CODE: UI and Analysis Pipeline (Rework Phase 4)

- **LLM Provider Selector**: New sidebar radio (OpenAI / Anthropic / Ollama).
- **Model Presets**: New `model_presets.py` with per-provider/mode/task model config (GPT-5 series, Claude 4.5 Haiku/Sonnet, qwen3:8b).
- **Analysis Mode Wiring**: `analysis_mode` + `llm_provider` threaded from UI through `AgentState` → `_run_llm_analysis()` → `get_chat_model()`.
- **Expert Mode Removed**: Removed toggle, two-column layout, and related session state functions. Inline editable table is always available.

### CODE: Agent Graph Cleanup (Rework Phase 4)

- Rewired graph: old flow (8 nodes) → new flow (4 nodes: `check_context → analyze → finalize`).
- Removed old algorithm-first nodes from `nodes.py` (bottleneck detection, generic suggestions, constraint validation, ROI calculation).
- Simplified `edges.py` and `state.py`.
- `nodes.py`: 829→339 lines (−59%), `graph.py`: 288→207 lines (−28%).

### CODE: Interview Improvements (Rework Phase 3)

- Targeted follow-up questions based on `ConfidenceResult.data_gaps` (replaces generic "Does this look correct?").
- "Estimate Missing" button for step-level gaps.
- Draft analysis preview shown immediately after extraction (when confidence ≥ 0.5).

### CODE: Summary-First Results Display (Rework Phase 2)

- New layout: "What I Found" → "Main Opportunities" with severity badges → "Core Value Work" → expandable details.
- Issues linked to specific recommendations.

### DOCS: Documentation Overhaul

- Rewrote `PROJECT_BRIEF.md`, `CONVERSATION_FLOW.md`, and `README.md` to reflect the LLM-first analysis pipeline.

---

## 2026-02-05

### ARCHITECTURE: LLM-Based Analysis Pipeline (Rework Phase 1)

- **Problem:** Old architecture used algorithms that just found `max(time)` and called it a "bottleneck."
- **Solution:** Algorithms calculate FACTS (percentages, dependencies), LLM makes JUDGMENTS (waste vs value).
- New modules: `analysis/metrics.py` (process metrics), `models/insight.py` (Issue, Recommendation, NotAProblem).
- New prompt: `analyze.j2` (pattern detection, waste vs value distinction, trade-off analysis).
- Validated on creative agency example: correctly identified creative work as core value, not waste.

### CODE: Conversational Edit Support

- LLM calls now include current process data and recent conversation history as context.
- New `agent/context.py` module for serializing process data and filtering messages.
- Updated extraction prompt with UPDATE decision path for edit requests.

---

## 2026-02-04

### ARCHITECTURE: Per-Task LLM Configuration

- Different tasks can use different models (e.g., fast model for extraction, strong model for analysis).
- `LLMTaskConfig` with resolution order: analysis mode preset → task-specific env var → global settings.
- Three user-facing presets: Cost-Optimized, Balanced (default), Deep Analysis.

### ARCHITECTURE: LangGraph SqliteSaver Persistence

- `persistence/checkpointer.py`: SqliteSaver wrapper with singleton pattern.
- `persistence/user_store.py`: UUID-based user identification without login.
- Thread ID format: `{user_id}:{conversation_id}` for per-user conversation history.

---

## 2026-02-03

### DECISION: UI Paradigm Shift — Forms to Chat-First

- **Problem:** Form-based UI too clunky for non-technical users (bakery owner example).
- **Solution:** Pivot to chat-first interface with file drop; forms become "edit mode" for reviewing extracted data.
- Created `agent/interface.py` as clean API between UI and LangGraph (UI never imports `graph.py` directly).

### CODE: Chat-First UI Implementation

- Chat component with message types: TEXT, FILE, DATA_CARD, ANALYSIS, CLARIFICATION, STATUS, ERROR.
- Advanced options sidebar: constraints, business context, analysis mode (collapsed by default).
- State machine: WELCOME → GATHERING → CONFIRMING → ANALYZING → RESULTS.

### CODE: Docling Integration for Document Parsing

- `ingestion/docling_parser.py`: Semantic chunking preserves document structure (tables, headings, lists).
- Supports 14 formats: PDF, DOCX, PPTX, Excel, HTML, PNG, JPG, TIFF, BMP.

---

## 2026-02-02

### ARCHITECTURE: Centralized LLM Factory

- `llm.py` with `get_chat_model()` supporting Anthropic, OpenAI, and Ollama providers.
- Algorithms provide facts, LLM explains reasoning.
- Expanded system prompt with definitions, terminology glossary, and anti-hallucination rules.

---

## 2026-02-01

### TECH: Jinja2 Prompt Templating

- Migrated all inline prompt strings to `.j2` templates in `prompts/` folder.
- Deleted old `agent/prompts.py` (inline strings).

### CODE: Data Ingestion Module

- `ingestion/csv_loader.py`, `excel_loader.py`: Auto-detect delimiters, column name mapping, messy value cleaning.
- `ingestion/normalizer.py`: LLM-powered extraction with Instructor, automatic retries on validation failure.
- Custom exception hierarchy: `ProcessIQError`, `InsufficientDataError`, `ExtractionError`.

---

## 2026-01-31

### CODE: LangGraph Agent Implemented

- `agent/state.py`: AgentState TypedDict with analysis fields and control flow.
- `agent/nodes.py`: Node functions implementing 4 agentic decision points (context sufficiency, bottleneck prioritization, constraint conflict resolution, confidence-driven output).
- `agent/edges.py`: Conditional routing with clarification loop.
- End-to-end test: 3 bottlenecks, 3 suggestions, 88% confidence, $130K/year ROI.

### CODE: Analysis Algorithms (Pure Logic, No LLM)

- `analysis/bottleneck.py`: Weighted scoring based on time, error rate, cost, and cascade impact via dependency graph.
- `analysis/roi.py`: PERT-style ROI with pessimistic/likely/optimistic ranges.
- `analysis/confidence.py`: Data completeness scoring (process 60%, constraints 25%, profile 15%).

---

## 2026-01-30

### CODE: Pydantic Models Created

- `models/process.py`: ProcessStep, ProcessData.
- `models/constraints.py`: Constraints, Priority enum.
- `models/analysis.py`: AnalysisResult, severity/type enums.
- `models/memory.py`: BusinessProfile, AnalysisMemory (Phase 2 ready).

---

## 2026-01-29

### SCOPE: Phase 1 Scope Defined

- Phase 1: Conversational input + file upload → LLM extracts → user reviews → analysis.
- Phase 2: Full conversational interview, persistent memory, RAG.
- Files: in-memory BytesIO, never written to disk.

### TECH: pydantic-settings for Configuration

- Centralized Settings class with type validation and `.env` file loading.

---

## 2026-01-28

### DECISION: Multi-Agent Architecture Rejected

- LangGraph nodes already provide task separation; multi-agent adds unnecessary complexity.
- Tasks are sequential (ingest → analyze → suggest → validate), not parallel.

### TECH: Phase 1 Dependencies Finalized

- Added: instructor, langsmith, pydantic-settings, langchain-core/community/anthropic.
- Removed from Phase 1: chromadb (no RAG until Phase 2).

### ARCHITECTURE: Folder Structure and Standards

- Root-level modules: config.py, constants.py, exceptions.py, logging_config.py.
- Python standard logging from day one, every module, every node.

---

## 2026-01-27

### DECISION: SQLite + ChromaDB Dual-Store for Phase 2

- SQLite for structured data (profiles, history, preferences).
- ChromaDB for vector search and semantic similarity.
- LangGraph Store rejected — limited to key-value lookups.

### DECISION: Spinner over Streaming for Phase 1

- Spinner showing current analysis step; streaming deferred to Phase 2.

---

## 2026-01-26

### DECISION: Agent Justification Documented

- Four agentic decision points: context sufficiency, multi-bottleneck prioritization, constraint conflict resolution, confidence-driven branching.
- Litmus test: system must make judgment calls, not just execute steps.

### ARCHITECTURE: Memory-Ready Design

- Phase 1: populate from input, don't persist.
- Phase 2: add persistence with profile approach (single doc) and collection approach (discrete items).

### TECH: Data Models and Frontend Strategy

- Pydantic BaseModel for domain models, TypedDict for LangGraph state.

### SCOPE: Phase 1 (MVP) vs Phase 2 Boundaries

- Phase 1: Chat + file upload, core agent, Streamlit UI.
- Phase 2: Persistent memory, full RAG.

### DESIGN: Agent Architecture Classification

- Utility-based agent: competing objectives (cost vs time vs quality vs constraints).
- Evolution path to learning agent in Phase 2 (user feedback, pattern learning).
