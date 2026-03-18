# ProcessIQ Project Brief

## Purpose

This document is the concise product and architecture brief for ProcessIQ.

It exists to answer four questions quickly:

1. What does the product do?
2. Who is it for?
3. How is it implemented today?
4. What is intentionally still incomplete?

For implementation details, use these docs alongside this brief:

- [README.md](../README.md)
- [architecture.md](architecture.md)
- [backend.md](backend.md)
- [frontend.md](frontend.md)
- [ai-analysis-design.md](ai-analysis-design.md)

## What ProcessIQ Does

ProcessIQ is an AI-assisted business process analysis tool for teams that do not have process-mining infrastructure, event logs, or a dedicated analytics function.

The product turns a plain-language workflow description or uploaded process document into:

- structured process steps
- deterministic timing, cost, dependency, and confidence calculations
- LLM-generated issues, recommendations, and follow-up questions
- an interactive process graph
- proposal-style exports

The core design principle is:

> Algorithms calculate facts. The LLM makes judgments.

That split is deliberate. Process metrics, confidence scoring, graph generation, and persistence are deterministic code. The LLM is used for extraction, interpretation, and recommendation generation.

## Target User

The current product is aimed at:

- operations managers
- consultants
- process owners
- owner-operators at small and mid-sized businesses

These users usually understand the workflow operationally, but they often lack:

- structured process data
- process-mining software
- internal analytics support

ProcessIQ is designed to work from conversational input and existing business documents rather than requiring event-log integration.

## Current Product Flow

The web app follows a chat-first workflow:

1. The user describes a process in chat or uploads a file.
2. The backend extracts or updates structured `ProcessData`.
3. The user reviews and edits the extracted process in an inline table.
4. The user runs analysis.
5. The app renders issues, recommendations, graph output, scenarios, and source data.
6. The user can give recommendation feedback, export results, revisit prior sessions, or refine the process and re-analyze.

This is implemented today in the Next.js frontend and FastAPI backend. It is not just a conceptual flow.

## Current Architecture

ProcessIQ is a three-layer application:

1. `frontend/`
   Next.js 15, React 19, Tailwind CSS, React Flow
2. `api/`
   FastAPI HTTP layer, request validation, CORS, rate limiting
3. `src/processiq/`
   Python package containing extraction, deterministic analysis, LangGraph orchestration, persistence, and export logic

High-level runtime flow:

```text
Browser
  -> typed frontend API client
FastAPI
  -> processiq.agent.interface
LangGraph workflow + deterministic analysis modules
  -> SQLite + ChromaDB persistence
```

Important implementation boundaries:

- `src/processiq/agent/interface.py` is the stable application boundary used by the API
- `src/processiq/analysis/` contains deterministic metrics, confidence, ROI, and visualization logic
- `src/processiq/ingestion/` handles CSV, Excel, and document parsing plus LLM-backed extraction
- `src/processiq/persistence/` handles profiles, analysis history, checkpoints, and vector retrieval

## What Is Shipped Today

The current repository already includes:

- a Next.js frontend with a chat-first, two-phase layout
- a FastAPI backend with typed schemas and rate limiting
- editable extracted process data before analysis
- LangGraph-based analysis with clarification and bounded investigation behavior
- persistent profile and session history
- ChromaDB-backed retrieval of prior analyses
- recommendation feedback capture
- a React Flow process graph
- Markdown, plain-text, and PDF export in the UI
- CSV export in the backend API

## Important Current Limitations

These are current implementation realities, not future-state aspirations:

- Extraction is not fully provider-neutral. The UI allows `ollama`, but extraction still falls back to OpenAI-compatible extraction logic.
- The web UI does not currently use `POST /continue`, `GET /graph-schema/{thread_id}`, or the CSV export endpoint even though the API exposes them.
- The frontend has no automated test suite yet.
- Identity is browser-local UUID state, not authenticated account-backed identity.
- Persistence is still local-disk oriented, which makes the current deployment shape best suited to local or controlled single-instance use.

## Why The Architecture Matters

This project is stronger than a thin "chat wrapper" because it shows several non-trivial engineering decisions:

- clear separation between deterministic analysis and LLM reasoning
- a bounded LangGraph workflow instead of a free-form agent loop
- typed frontend/backend contracts
- semantic retrieval combined with transactional persistence
- a renderer-agnostic graph schema produced on the backend and rendered in React Flow
- explicit handling of confidence, missing data, and recommendation feedback

The most important part of the system is not any single model call. It is the way extraction, deterministic analysis, memory, graph output, and UI state are composed into a coherent workflow.

## What This Document Is Not

This file is intentionally a brief.

It is not:

- a changelog
- a deployment guide
- a prompt design document
- a product roadmap

Use the specialized docs for those topics.

## Review Notes

This file was rewritten because the previous version mixed:

- outdated implementation details
- planned behavior presented as shipped behavior
- stale endpoint and UI descriptions
- older architecture framing from before the current FastAPI and Next.js shape stabilized

If this brief changes materially, update the linked docs in the same pass so the repository stays internally consistent.
