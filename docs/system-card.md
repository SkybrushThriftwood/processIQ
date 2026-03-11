# System Card: ProcessIQ

## Summary

ProcessIQ is an AI-powered process optimization advisor. It analyzes a described business process, identifies likely bottlenecks and waste patterns, and proposes constraint-aware recommendations with assumption-driven ROI estimates.

This is a decision-support system: it suggests, the user decides.

## Intended Use

- Support process improvement discussions (where time is lost, where handoffs fail, which steps are high-risk)
- Generate constraint-aware improvement options (budget, hiring freezes, regulatory constraints)
- Provide rough ROI ranges with explicit assumptions

## Not Intended For

- Personnel evaluation or performance management
- Safety-critical operational changes
- Legal/compliance determinations without formal review
- Producing "ground truth" measurements when inputs are incomplete or estimated

## Inputs

- User-provided process descriptions (text) and/or uploaded files (CSV, spreadsheets, docs)
- Optional business profile (industry, company size, regulatory environment, notes)
- Optional constraints (budget limits, no-hire constraints, audit trail requirements, timelines)
- Optional prior analysis history for the same user (RAG)

## Outputs

- Structured issues and recommendations (with descriptions and expected benefit)
- Assumption-driven ROI ranges (approximate, based on explicit assumptions)
- Confidence and data-quality guidance (when context is insufficient)
- Optional reasoning trace (decision points for audit and review)

## System Components

- Deterministic calculations for metrics and ROI scaffolding
- LLM-based extraction (turns messy inputs into structured process steps)
- LLM-based judgment (waste vs core value, root causes, recommendation generation)
- Memory: SQLite persistence + ChromaDB similarity search for cross-session context (RAG)
- Conversation checkpointing via LangGraph SqliteSaver (SQLite) for multi-turn continuity

## Data Handling (High Level)

- Uploaded files are processed in-memory for extraction; raw files are not stored by ProcessIQ.
- ProcessIQ persists user-scoped profile and analysis history in local SQLite to improve future recommendations.
- ProcessIQ stores embeddings and metadata in a local ChromaDB directory for semantic retrieval (RAG).
- Conversation checkpoints may be stored in SQLite via LangGraph SqliteSaver.

If you use hosted LLM providers, what you send them is subject to their retention policies.

## Human Oversight And Control

- Users review and can edit extracted structured data before analysis.
- Recommendations are presented for review (accept/reject feedback); no auto-execution.
- Users can delete stored profile and analysis history ("Reset my data"); deleting embeddings/checkpoints is a planned improvement.

## Known Limitations And Failure Modes

- Incomplete inputs can lead to wrong conclusions or generic recommendations.
- LLM outputs can be incorrect or overly confident (hallucinations).
- ROI estimates are approximate and depend on assumptions and calibration to business size.
- Process descriptions can omit critical constraints; the system may need clarification loops.

## Risk Mitigations (Lightweight)

- Transparency: explicit assumptions, confidence-driven branching, reasoning trace
- Abuse resistance: input caps (file size limit, message truncation), file extension whitelist
- Privacy controls: user-scoped storage and user-controlled deletion; local LLM option (Ollama)

For details, see `docs/responsible-ai.md`.
