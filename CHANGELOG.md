# Changelog

All notable design decisions and changes to ProcessIQ are documented here.

Format: `[YYYY-MM-DD] Category: Description`

Categories: `DESIGN`, `ARCHITECTURE`, `SCOPE`, `TECH`, `DECISION`

---

## 2026-02-06

### FIX: Type annotation for `get_llm_provider()` return type

- Changed `get_llm_provider()` return type from `str` to `Literal["anthropic", "openai", "ollama"]` in `state.py`
- Resolves 4 Pyright type errors in `handlers.py` where the `str` return was incompatible with `Literal` parameters on `extract_from_file`, `extract_from_text`, and `analyze_process`

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
