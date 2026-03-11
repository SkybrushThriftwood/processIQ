# ADR-0003: Abstract LLM Provider Behind a Single Factory

**Date:** 2025-11-15
**Status:** Accepted

## Context

ProcessIQ makes a lot of LLM calls, and they're not all the same: extraction can use a cheaper model, analysis benefits from a stronger one, and different users will run the system against different providers — OpenAI for convenience, Anthropic for quality preference, Ollama for privacy or offline use.

The naive approach is to import `ChatOpenAI` or `ChatAnthropic` directly at each call site. That works until you want to change providers, add a new one, or give users a choice — at which point you're doing a multi-file find-and-replace and hoping you didn't miss anything.

## Considered Options

1. **Single factory function in `llm.py`** — all provider logic in one place; callers specify a task or provider override; task-level config maps to specific model strings in `config.py`
2. **Direct provider imports at each call site** — simple and transparent, but provider logic is scattered and changing providers touches every call site
3. **Dependency injection via constructor** — pass the model object into each node/function; more testable in isolation but adds boilerplate to every function signature and complicates LangGraph node wiring

## Decision

Use a **single factory function** (`get_chat_model()` in `src/processiq/llm.py`).

Everything goes through one module. The factory reads `settings.llm_provider` and `settings.llm_model` from pydantic-settings (populated via `.env`). Per-task model overrides are defined as named constants in `config.py` and passed as a `task` argument. Provider-specific SDK classes (`ChatOpenAI`, `ChatAnthropic`, `ChatOllama`) only appear in `llm.py` — nothing else imports them directly.

This also makes the privacy story concrete: set `LLM_PROVIDER=ollama` in `.env` and the entire system switches to local inference with no external API calls.

## Trade-offs

- **Gains:** Swap provider in one line (`.env`), consistent logging and error handling everywhere, clean privacy path via Ollama, easy to add a new provider in one place
- **Costs/Risks:** Tests that exercise LLM calls need to patch `llm.get_chat_model` rather than a local variable, which is a slightly more global mock. The task-level config indirection can make it non-obvious which model is actually being called during debugging.

## Consequences

Adding a new provider (e.g. Gemini) requires one new branch in `get_chat_model()`, one new import, and a new enum value in config. No call sites change. The Ollama path is the foundation of the privacy and self-hosting story documented in `docs/responsible-ai.md`.
