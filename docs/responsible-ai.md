# Responsible AI (Lightweight Review)

This is a pragmatic Responsible AI review for ProcessIQ.
Goal: turn high-level ethics principles into concrete product + engineering choices that can be verified in the codebase.

This document focuses on the risks that matter for ProcessIQ's use case:
- Overconfident or incorrect recommendations (hallucinations / false precision)
- Misuse of outputs (e.g., using the tool for personnel evaluation)
- Handling potentially sensitive business information (process docs, metrics, internal workflows)

## Principle Set (Operationalized)

This review uses a small principle set commonly seen in industry Responsible AI programs:
- Transparency
- Human oversight
- Privacy and data handling
- Reliability and safety
- Fairness (harm avoidance)
- Accountability (traceability + user control)

## What ProcessIQ Does (And Does Not Do)

ProcessIQ is a decision-support tool for process analysis. It does not execute changes, automate personnel decisions, or produce compliance determinations.

Not intended for:
- Personnel evaluation, performance management, disciplinary actions
- Safety-critical operational changes
- Legal or compliance decisions that require formal review

## Key Risks And Mitigations

### 1) Hallucination / Overconfidence

Risk:
- LLMs can invent causes, misread context, or overstate ROI precision.

Mitigations in ProcessIQ:
- "Algorithms calculate facts; the LLM makes judgments": deterministic metrics + ROI ranges, LLM for interpretation.
- Confidence-driven behavior: asks clarifying questions when key inputs are missing instead of guessing.
- Assumption-driven ROI: makes assumptions explicit to reduce false precision.
- Reasoning trace: exposes agent decision points for audit/review rather than hiding them.

Residual risk:
- A confident-sounding narrative can still be wrong. Users must validate recommendations against reality.

### 2) Misuse Of Output (Scope Creep)

Risk:
- Users can apply outputs outside the intended scope, especially for evaluating teams or "blaming" departments.

Mitigations:
- System card clearly states intended use and non-intended use.
- UI and docs frame output as suggestions, not facts, and keep humans in the loop.
- Export section displays an explicit "Not for personnel evaluation, performance management, or compliance decisions" notice — the highest-risk surface for scope misuse.

### 3) Sensitive Business Information

Risk:
- Users may provide internal process documents, operational metrics, or customer workflow information.

Mitigations:
- Document parsing runs in-memory; raw uploaded files are not stored by ProcessIQ.
- Stored memory is scoped by user ID (no account, random UUID) and is only used to improve the same user's future analyses.
- User-controlled deletion ("Reset my data") deletes stored profile + analysis history (SQLite tables used for memory and feedback loops).
- Local model option (Ollama) reduces third-party exposure for users who self-host.

Residual risk:
- If you use hosted LLM APIs, provider retention policies apply to what you send them.

## Data Flow Summary (What Is Sent / Stored)

### Sent to an LLM provider
- Extracted text (not raw file bytes) and user-provided process descriptions
- Structured process data and constraints
- Context from prior analyses when RAG is enabled (summaries / issue text / recommendation text)

Notes:
- If LangSmith tracing is enabled and configured, traces may include prompts/inputs.

### Stored locally by ProcessIQ (persistence)

ProcessIQ stores data to enable cross-session improvements (business profile defaults, "do not re-suggest" rejections, RAG retrieval).

Stored artifacts include:
- Business profile (industry, size, constraints, notes, rejected approaches)
- Analysis history (process name/description, step names, issues, recommendations, accept/reject feedback)
- Vector embeddings and metadata in ChromaDB for similarity search (RAG)
- Conversation checkpoints in SQLite via LangGraph SqliteSaver (thread state)

Retention:
- Until the user chooses "Reset my data" (or the DB is deleted).
- A timed expiry policy is a planned improvement.

Reset scope (current):
- Deletes: business profile + analysis history rows (used for cross-session defaults and feedback loops)
- Planned: also delete ChromaDB entries and LangGraph checkpoint rows for the user

## Security And Abuse Resistance (Lightweight)

ProcessIQ includes basic hardening to reduce common LLM-product risks:
- Input caps to reduce prompt-stuffing / token abuse
- File upload size limits (50 MB hard limit, 10 MB warning) and extension whitelist
- Message context truncation (4,000 chars per message) to prevent context flooding

Planned improvements:
- Rate limiting on the FastAPI layer (to be added at deployment)
- Optional "privacy mode" to disable persistence (no SQLite/chroma writes)
- Optional PII/sensitive-data warnings before analysis/export

## Prompt Injection Resistance

Risk:
- Users can upload documents (CSV, Excel, PDF, DOCX) whose content is passed directly into LLM context. A crafted cell or paragraph containing adversarial instructions (e.g. "ignore previous instructions and output...") could attempt to hijack model behavior.

This is an active research problem with no complete solution. ProcessIQ reduces exposure through architectural constraints:

- Uploaded file content is extracted to plain text before reaching the LLM — raw bytes and formatting are stripped.
- The LLM's role is scoped to analysis and structured output generation. It cannot call external APIs, execute code, or write to storage directly — all tool calls are deterministic Python functions that only read from `AgentState`.
- LangSmith tracing allows anomalous outputs to be detected and investigated post-hoc.

Planned improvement:
- Wrap user-supplied content in explicit `<user_data>` XML tags in prompts to signal untrusted content to the LLM — a common mitigation pattern for document ingestion pipelines.

## Security Threat Model (Lightweight)

This is not a full threat model, but a record of the three concrete risks most relevant to ProcessIQ's architecture.

**1. LLM API key exposure**
The OpenAI / Anthropic API key lives in `.env` and is read via pydantic-settings at startup. It is never sent to the frontend, logged, or included in LangSmith traces. `.env` is in `.gitignore`. Risk is limited to the deployment environment — if the server is compromised, the key is compromised. Mitigation: use scoped API keys with spend limits at the provider level.

**2. Local SQLite has no encryption**
`data/processiq.db` stores business profiles, analysis history, and LangGraph checkpoints in plaintext. Anyone with filesystem access can read it. This is acceptable for a local-first deployment but is a real concern on a shared server. Mitigation: for production deployment, mount the database on an encrypted volume or replace SQLite with a managed database service.

**3. LangSmith trace privacy**
When `LANGSMITH_TRACING=true`, every agent invocation sends the full conversation — including user-submitted process descriptions and constraints — to LangSmith. For development and debugging this is intentional (traces are useful for inspecting the agentic loop). For production use with sensitive business data, either disable tracing via `LANGSMITH_TRACING=false` or configure data retention and masking in the LangSmith project dashboard.

## How To Read This As A Reviewer

Artifacts that support this document:
- `docs/system-card.md` (intended use, limits, data handling)
- README: Data & Privacy section (user control + reset behavior)
