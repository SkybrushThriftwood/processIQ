# Changelog

All notable design decisions and changes to ProcessIQ are documented here.

Format: `[YYYY-MM-DD] Category: Description`

Categories: `DESIGN`, `ARCHITECTURE`, `SCOPE`, `TECH`, `DECISION`

---

## 2026-02-16

### FIX: Post-analysis follow-up conversation now uses LLM

- Follow-up questions after analysis (including "Questions to Consider") were handled by regex string matching with a canned response — no LLM call. Now routes all follow-up questions to the LLM with full analysis context, chat history, business profile, and constraints.
- Analysis results panel no longer vanishes when user sends a follow-up message (state `CONTINUING` now also renders results).
- Removed "what if" from re-analyze triggers — these are conversational questions, not re-analysis requests.
- New prompt template `followup.j2` for follow-up conversation context.

### FIX: Asterisk indicator on extracted steps

- Steps were marked with `*` (AI-estimated) even when the LLM just defaulted fields to 0 (no actual estimation). Now only shows `*` when estimated fields have non-zero values.

### FIX: Deprecated Streamlit API

- Replaced `use_container_width=True` with `width="stretch"` on data editor (deprecated after 2025-12-31).

### DESIGN: Sidebar, File Upload, and Extraction Improvements

- **Sidebar defaults removed**: Industry and Company Size no longer pre-select a value — show "Select..." placeholder instead. Made both fields optional on `BusinessProfile`.
- **Regulation Level tooltip**: Added `help=` tooltip matching the pattern used by Annual Revenue.
- **Privacy notice spacing**: Added visual gap between privacy notice box and "Technical details" expander.
- **File upload reset fix**: File uploader now clears on conversation reset via dynamic widget key counter.
- **"Send File" button**: File upload no longer auto-processes on selection. User must click "Send File" for explicit control.
- **xlsx extraction fix**: Binary Excel files were being decoded as UTF-8 garbage for the LLM fallback. Now converts via pandas to CSV text before passing to LLM normalization.
- **Early table creation**: Extraction prompt now creates a table as soon as step names are identifiable, even without timing data. Missing fields show as blank cells. "Confirm & Analyze" button is disabled until timing data is provided; "Estimate Missing" button remains available.

### CODE: Efficiency and Workflow Optimizations

- **Graph compilation caching** (`graph.py`): Module-level cache prevents recompiling the deterministic LangGraph on every analysis call
- **Parallel post-extraction LLM calls** (`interface.py`): Improvement suggestions and draft analysis now run concurrently via `ThreadPoolExecutor`
- **Structured output for analysis** (`nodes.py`): Replaced manual JSON parsing with `with_structured_output(AnalysisInsight)`, deleted ~50 lines of brittle `_parse_analysis_response()`; removed JSON schema section from `analyze.j2`
- **Instructor client caching** (`normalizer.py`): Anthropic/OpenAI Instructor clients cached at module level instead of recreated per call
- **Pre-compiled regex patterns** (`metrics.py`): Step-type inference patterns compiled once at module level
- **Transitive closure fix** (`metrics.py`): Fixed `_get_transitive()`/`_get_transitive_upstream()` shared visited set — was copying per recursion call, causing exponential blowup on reconvergent DAGs
- **Legacy dead code removal** (`state.py`, `chat.py`, `handlers.py`): Removed 15 unused form-based session state functions, 7 unused `_STATE_DEFAULTS` keys, and the `_render_analysis_results` AnalysisResult renderer (always showed "No results" since no node produces AnalysisResult)
- **Estimate comparison fix** (`handlers.py`): Replaced `repr()` string comparison with direct tuple equality for step data change detection

## 2026-02-12

### DESIGN: Progressive Disclosure on Recommendations

- Added `plain_explanation` and `concrete_next_steps` fields to `Recommendation` model in `insight.py`
- Updated `analyze.j2` prompt with instructions and examples for generating non-technical explanations and actionable first steps
- Updated `results_display.py` with two new `st.expander` sections per recommendation: "What this means in practice" and "How to get started"
- Both compact (issue-linked) and standalone recommendation renderers updated

### DESIGN: Business Context for Calibrated Recommendations

- **Problem**: Recommendations like "automate this for $15-50k/year" are meaningless without business scale context. A 3-store bakery and a 1000-person enterprise get the same generic suggestions.
- **Solution**: Added revenue range, free-text business notes, and full business profile threading into the analysis prompt.
- Added `RevenueRange` enum to `BusinessProfile` (8 tiers from "Under $100K" to "Over $100M" plus "Prefer not to say")
- Surfaced revenue dropdown and "About Your Business" text area in sidebar Business Context panel
- Built `_format_business_context_for_llm()` in `nodes.py` to serialize full profile into LLM-readable format
- Updated `analyze.j2` to receive `business_context` (replaces bare `industry` string) with explicit instruction to calibrate costs to business scale
- Updated `system.j2` to include revenue and notes in system prompt
- Updated `get_analysis_prompt()` signature: `industry` parameter replaced by `business_context`

### FIX: GPT-5 Series and Cross-Provider Model Resolution

- **GPT-5 parameter restrictions**: GPT-5 and o-series models reject `temperature!=1` and `max_tokens` (requires `max_completion_tokens`). Added `is_restricted_openai_model()` helper in `llm.py`; applied in both LangChain (`_get_openai_model`) and Instructor (`_extract_with_openai`) code paths.
- **Cross-provider model bug**: When user selected "anthropic" in UI but `.env` had `LLM_PROVIDER=openai`, the normalizer resolved to `gpt-5-nano` for Anthropic API calls (404 error). Root cause: `normalize_with_llm()` did not pass `provider` to `get_resolved_config()`.
- **Missing provider/analysis_mode threading**: `graph.py` (clarification), `interface.py` (improvement suggestions, parsed document normalization) all called `get_chat_model()` without `provider` or `analysis_mode`, ignoring user's UI selections. All call sites now thread these through.
- **Stale defaults**: Updated default models in normalizer from `gpt-4o`/`claude-sonnet-4` to `gpt-5-nano`/`claude-haiku-4-5-20251001` to match `model_presets.py`.
- **`.env` cleanup**: Updated comments to reference `model_presets.py`, corrected task names (`explanation`, `analysis` not `summary`, `framework`), corrected example model names.

---

## 2026-02-06

### CODE: UI Fixes Batch 2

- **LLM Provider Selector**: New sidebar radio (OpenAI / Anthropic / Ollama) above analysis mode; Ollama greys out mode selector
- **Model Presets**: New `model_presets.py` with per-provider/mode/task model config (GPT-5 series, Claude 4.5 Haiku/Sonnet, qwen3:8b)
- **Analysis Mode Wiring**: `analysis_mode` + `llm_provider` threaded from UI through `AgentState` → `_run_llm_analysis()` → `get_chat_model()`; fixes draft analysis not showing and empty LLM responses
- **Retry on Empty Response**: `_run_llm_analysis()` retries once if LLM returns empty content
- **Cost Label**: "Labor Cost ($)" → "Cost ($)" everywhere; tooltips via `st.data_editor` `column_config` with `help` text
- **Editable Table**: Data card table always editable inline (`st.data_editor` with NumberColumn); edits update process data in session state
- **Expert Mode Removed**: Removed toggle, two-column layout, "Edit Data" button, `handle_edit_button`, `handle_expert_data_change`, `is_expert_mode`/`set_expert_mode`
- **Estimate Missing Feedback**: Shows "all values already filled in" message when re-clicking produces no changes
- **Stale Session State**: `getattr()` guards for `estimated_fields` and `custom_industry` on Pydantic v2 instances

### DOCS: Documentation Overhaul

- Rewrote `PROJECT_BRIEF.md`: updated architecture diagrams, file structure, phase 1 scope, and success criteria to reflect LLM-first analysis pipeline
- Rewrote `CONVERSATION_FLOW.md`: updated state descriptions, resolved open questions, added new features (Estimate Missing, draft analysis, targeted questions)
- Rewrote `README.md`: new architecture diagram, proper quick start, tech stack table, project structure

### CODE: Agent Graph Cleanup (Rework Phase 4)

- Rewired graph: old flow (8 nodes) → new flow (4 nodes: `check_context → analyze → finalize`)
- Removed old algorithm-first nodes from `nodes.py` (bottleneck detection, generic suggestions, constraint validation, ROI calculation)
- Simplified `edges.py` and `state.py` (removed unused fields and routing)
- Deleted 7 files (6 unused prompts + `bottleneck.py`)
- `nodes.py`: 829→339 lines (-59%), `graph.py`: 288→207 lines (-28%)

### CODE: Interview Improvements (Rework Phase 3)

- Targeted follow-up questions based on `ConfidenceResult.data_gaps` (replaces generic "Does this look correct?")
- "Estimate Missing" button for step-level gaps (reuses existing ESTIMATE path in extraction prompt)
- Draft analysis preview shown immediately after extraction (when confidence >= 0.5)

### CODE: Summary-First Results Display (Rework Phase 2)

- New layout: "What I Found" → "Main Opportunities" with severity badges → "Core Value Work" → expandable details
- Issues linked to specific recommendations (not generic "automate this step" suggestions)
- Prefers `AnalysisInsight` (LLM-based) over legacy `AnalysisResult` (algorithm-based)

### UX: Column Renames and Estimated Value Indicators

- "Extraction Confidence" → "Data Completeness", "Error Rate" → "Problem Frequency", "Cost ($)" → "Labor Cost ($)"
- Per-field asterisk tracking via `estimated_fields` list (only AI-estimated values get marked, not user-provided ones)
- Free-form industry field when "Other" selected in business context

---

## 2026-02-05

### ARCHITECTURE: LLM-Based Analysis Pipeline (Rework Phase 1)

- **Problem:** Old architecture used algorithms that just found `max(time)` and called it a "bottleneck"
- **Solution:** Algorithms calculate FACTS (percentages, dependencies), LLM makes JUDGMENTS (waste vs value)
- New modules: `analysis/metrics.py` (process metrics), `models/insight.py` (Issue, Recommendation, NotAProblem)
- New prompt: `analyze.j2` (pattern detection, waste vs value distinction, trade-off analysis)
- Validated on creative agency example: correctly identified creative work as core value, not waste

### CODE: Conversational Edit Support

- LLM calls now include current process data and recent conversation history as context
- New `agent/context.py` module for serializing process data and filtering messages
- Updated extraction prompt with UPDATE decision path for edit requests
- Token limits: max 50 table rows, 3 history messages, 4000 chars per message

### UX: Extraction Prompt Improvements

- Strengthened prompt to prefer clarification over guessing for vague inputs
- Added ESTIMATE path for when users explicitly request estimates
- Contextual error guidance instead of generic "couldn't understand"

---

## 2026-02-04

### ARCHITECTURE: Per-Task LLM Configuration

- Different tasks can use different models (e.g., fast model for extraction, strong model for analysis)
- `LLMTaskConfig` with resolution order: analysis mode preset → task-specific env var → global settings
- Three user-facing presets: Cost-Optimized, Balanced (default), Deep Analysis

### ARCHITECTURE: LangGraph SqliteSaver Persistence

- `persistence/checkpointer.py`: SqliteSaver wrapper with singleton pattern
- `persistence/user_store.py`: UUID-based user identification without login
- Thread ID format: `{user_id}:{conversation_id}` for per-user conversation history
- Graph invocation passes thread_id config for automatic state checkpointing

### CODE: Expert Mode Panel

- Editable process data table using `st.data_editor` with real-time updates
- Confidence breakdown by category, per-step field coverage indicators
- Two-column layout (3:2) when expert mode enabled: chat left, data right

### DESIGN: Smart Interviewer Pattern

- LLM returns EITHER extracted data OR clarifying questions — never both
- `ExtractionResponse` discriminated union enforced by Instructor schema
- Natural conversational tone for clarifications (not robotic numbered lists)

---

## 2026-02-03

### DECISION: UI Paradigm Shift — Forms to Chat-First

- **Problem:** Form-based UI too clunky for non-technical users (bakery owner example)
- **Solution:** Pivot to chat-first interface with file drop; forms become "edit mode" for reviewing extracted data
- Created `agent/interface.py` as clean API between UI and LangGraph (UI never imports graph.py directly)

### CODE: Chat-First UI Implementation

- Chat component with message types: TEXT, FILE, DATA_CARD, ANALYSIS, CLARIFICATION, STATUS, ERROR
- Advanced options sidebar: constraints, business context, analysis mode (collapsed by default)
- Privacy notice component (two-tier: simple default, technical expandable)
- State machine: WELCOME → GATHERING → CONFIRMING → ANALYZING → RESULTS
- Conversation flow handlers: clarification responses, reset detection, re-analyze with modified constraints

### CODE: Docling Integration for Document Parsing

- `ingestion/docling_parser.py`: Semantic chunking preserves document structure (tables, headings, lists)
- Supports 14 formats: PDF, DOCX, PPTX, Excel, HTML, PNG, JPG, TIFF, BMP
- Pipeline: `parse_document()` → `ParsedDocument` → `normalize_parsed_document()` → `ProcessData`
- Verified with sample messy Excel: correct table extraction and LLM normalization

---

## 2026-02-02

### CODE: Streamlit UI Implemented

- Complete single-page phased UI: header, process input forms, constraints, business context, data review, results display, export
- Structured clarification questions with typed widgets (text/number/select/boolean)
- Export module: CSV (Jira-compatible), text, and markdown summary formats
- Session state management with UIPhase enum and type-safe getters/setters

### ARCHITECTURE: Centralized LLM Factory

- `llm.py` with `get_chat_model()` supporting Anthropic, OpenAI, and Ollama providers
- LLM explanation integration: algorithms provide facts, LLM explains "why"
- Expanded system prompt with definitions, terminology glossary, and anti-hallucination rules
- `llm_explanations_enabled` config flag for testing/cost control

### DESIGN: Transparency & Trust

- Documented what's calculated vs. AI-generated with trustworthiness levels
- Users making financial decisions need to know what they can rely on

---

## 2026-02-01

### TECH: Jinja2 Prompt Templating

- Migrated all inline prompt strings to `.j2` templates in `prompts/` folder
- Templates: system, extraction, clarification, bottleneck/suggestion explanation, framework-specific, summary
- Deleted old `agent/prompts.py` (inline strings)

### CODE: Data Ingestion Module

- `ingestion/csv_loader.py`: Auto-detect delimiters, column name mapping, messy value cleaning
- `ingestion/excel_loader.py`: Auto-detect header row, multi-sheet support
- `ingestion/normalizer.py`: LLM-powered extraction with Instructor, automatic retries on validation failure
- Custom exception hierarchy: ProcessIQError, InsufficientDataError, ExtractionError

---

## 2026-01-31

### CODE: LangGraph Agent Implemented

- `agent/state.py`: AgentState TypedDict with analysis fields and control flow
- `agent/nodes.py`: 6 node functions implementing 4 agentic decision points (context sufficiency, bottleneck prioritization, constraint conflict resolution, confidence-driven output)
- `agent/edges.py`: Conditional routing with clarification loop and alternative generation
- `agent/graph.py`: StateGraph construction with conditional edges
- End-to-end test: 3 bottlenecks, 3 suggestions, 88% confidence, $130K/year ROI

### CODE: Analysis Algorithms (Pure Logic, No LLM)

- `analysis/bottleneck.py`: Weighted scoring based on time, error rate, cost, and cascade impact via dependency graph
- `analysis/roi.py`: PERT-style ROI with pessimistic/likely/optimistic ranges and payback period
- `analysis/confidence.py`: Data completeness scoring (process 60%, constraints 25%, profile 15%)

---

## 2026-01-30

### CODE: Pydantic Models Created

- `models/process.py`: ProcessStep, ProcessData with computed properties (total_time, total_cost)
- `models/constraints.py`: Constraints, ConflictResult, Priority enum
- `models/analysis.py`: Bottleneck, Suggestion, ROIEstimate, AnalysisResult with severity/type enums
- `models/memory.py`: BusinessProfile, AnalysisMemory (Phase 2 ready)

### CODE: Sample Test Data

- `data/sample_process.csv`: 5-step expense approval with dependencies
- `data/sample_constraints.json`, `data/sample_context.json`: Business profile and constraints
- `data/sample_messy.xlsx`: Intentionally inconsistent data for LLM normalization testing

---

## 2026-01-29

### SCOPE: Conversational Input Moved to Phase 1

- Phase 1: User describes process in text → LLM extracts → user reviews
- Phase 2: Full conversational interview (agent drives Q&A)

### SCOPE: File Upload with Extract-and-Discard Pattern

- Upload → parse → LLM normalize → user reviews → store as Pydantic models → discard file
- Files are in-memory BytesIO, never written to disk

### TECH: pydantic-settings for Configuration

- Centralized Settings class with type validation and .env file loading
- SecretStr for API keys, configurable log level, confidence threshold

---

## 2026-01-28

### DECISION: Multi-Agent Architecture Rejected

- LangGraph nodes already provide task separation; multi-agent adds unnecessary complexity
- Tasks are sequential (ingest → analyze → suggest → validate), not parallel

### TECH: Phase 1 Dependencies Finalized

- Added: instructor, langsmith, pydantic-settings, langchain-core/community/anthropic
- Removed from Phase 1: chromadb (no RAG until Phase 2)

### ARCHITECTURE: Folder Structure and Standards

- Root-level modules: config.py, constants.py, exceptions.py, logging_config.py
- Merged tools/ into agent/tools.py; split tests into unit/ and integration/
- Python standard logging from day one, every module, every node
- Custom exception hierarchy with human-readable error translation

---

## 2026-01-27

### ARCHITECTURE: Short-Term vs Long-Term Memory

- Short-term: LangGraph TypedDict state (session-scoped, in-memory)
- Long-term: SQLite + ChromaDB (persistent across sessions, Phase 2)

### DECISION: SQLite + ChromaDB Dual-Store for Phase 2

- SQLite for structured data (profiles, history, preferences)
- ChromaDB for vector search and semantic similarity
- LangGraph Store rejected — limited to key-value lookups

### DECISION: Spinner over Streaming for Phase 1

- Spinner showing current analysis step; streaming deferred to Phase 2

### SCOPE: Phase 2 Roadmap Consolidated

- Collected all Phase 2 items in one place: memory, ingestion, analysis, UX improvements

---

## 2026-01-26

### DECISION: Agent Justification Documented

- Four agentic decision points: context sufficiency, multi-bottleneck prioritization, constraint conflict resolution, confidence-driven branching
- Litmus test: system must make judgment calls, not just execute steps

### ARCHITECTURE: Memory-Ready Design

- Phase 1: populate from input, don't persist
- Phase 2: add persistence with profile approach (single doc) and collection approach (discrete items)

### TECH: Data Models and Frontend Strategy

- Pydantic BaseModel for domain models, TypedDict for LangGraph state
- Streamlit for Phase 1 UI
- Forms primary, CSV as power-user option, LLM extraction for messy data

### SCOPE: Phase 1 (MVP) vs Phase 2 Boundaries

- Phase 1: Forms, basic CSV/Excel, core agent, Streamlit UI
- Phase 2: Persistent memory, conversational input, PDF/image extraction, full RAG

### DESIGN: Agent Architecture Classification

- Utility-based agent: competing objectives (cost vs time vs quality vs constraints)
- Evolution path to learning agent in Phase 2 (user feedback, pattern learning)
