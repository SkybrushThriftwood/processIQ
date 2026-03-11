# ADR-0002: Use ChromaDB for Vector Storage

**Date:** 2026-01-15
**Status:** Accepted

## Context

Phase 2 adds RAG: before running a new analysis, the agent retrieves semantically similar past analyses and injects them as context. That requires an embedding store with similarity search.

The constraints I was working with:
- No infrastructure budget — everything has to run locally without a separate server process
- Python-native (no language boundary)
- The dataset is small: tens to low hundreds of analyses per user
- The same embedding pipeline needs to be extensible to user-uploaded documents in Phase 3

## Considered Options

1. **ChromaDB** — embedded Python library, persistent local storage, no server required, provider-aware embeddings (OpenAI / Ollama)
2. **pgvector (PostgreSQL extension)** — production-grade vector search, but requires a running PostgreSQL instance which is significant infrastructure overhead for a local-first deployment
3. **FAISS** — Meta's similarity search library, fast and battle-tested, but no built-in persistence (you have to manage serialization yourself) and no metadata filtering
4. **Pinecone / Weaviate (hosted)** — zero operational overhead, but adds a paid external dependency and sends all analysis data to a third party — which contradicts the privacy story

## Decision

Use **ChromaDB** with `PersistentClient`.

It runs in-process and writes to a local directory — no infrastructure to set up. For the dataset size ProcessIQ operates at, query performance is not a concern. The provider-aware embedding support fits cleanly with the existing LLM provider abstraction (the same OpenAI / Ollama config drives embeddings and chat). All ChromaDB calls are wrapped in try/except so RAG degrades gracefully if the library isn't available — it's an enhancement, not a hard dependency.

## Trade-offs

- **Gains:** Zero infrastructure, in-process, persistent, Python-native, graceful degradation, local data (no third-party sending)
- **Costs/Risks:** ChromaDB is not built for multi-tenancy or concurrent writers across processes — at any real production scale with multiple users on a shared server, this breaks. The ChromaDB API has also changed significantly between versions. The local file storage means data is lost on ephemeral cloud deployments unless a persistent volume is mounted.

## Consequences

The ChromaDB persist directory (`CHROMA_PERSIST_DIRECTORY`) is a local path configured via env var. At deployment, a persistent volume mount is required or the vector data won't survive redeploys. Migrating to a hosted vector DB in Phase 3 means replacing `persistence/vector_store.py` only — the rest of the RAG pipeline is untouched.
