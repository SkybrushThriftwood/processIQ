# ADR-0001: Use LangGraph for Agent Orchestration

**Date:** 2025-12-01
**Status:** Accepted

## Context

ProcessIQ needs more than a single LLM call. The core flow has to evaluate whether the input is good enough to analyze, ask clarifying questions if it isn't, run an investigation loop where the model decides what to look into, and only then produce a final result. That's not a straight pipeline — it's a graph with cycles and conditional branches.

I initially considered building this as a plain LangChain chain, but the investigation loop is a cycle (the model calls a tool, gets a result, decides whether to call another one), and LCEL simply can't express cycles without hacks. I also looked at writing a custom Python state machine from scratch — which is doable, but you end up reimplementing what LangGraph provides: typed state, conditional routing, checkpointing, and tool dispatch.

## Considered Options

1. **LangGraph** — stateful graph framework with typed nodes, conditional edges, built-in `ToolNode` for tool dispatch, `SqliteSaver` for conversation checkpointing, and LangSmith integration out of the box
2. **Raw LangChain LCEL** — composable chains with `RunnableBranch` for branching logic; no native support for cycles
3. **Custom Python state machine** — hand-rolled loop with a dict for state; no framework dependency but replicates most of what LangGraph provides

## Decision

Use **LangGraph**.

The investigation loop (`investigate ↔ tool_node`) is the deciding factor. It's a cycle — the LLM calls a tool, the tool returns a result, the LLM decides whether to call another tool or stop. LangGraph's `ToolNode` from `langgraph.prebuilt` handles this natively: it dispatches whichever tool the LLM called, injects the result back into the message history, and loops. Writing this cleanly without a graph abstraction would have taken significantly more scaffolding.

The `SqliteSaver` checkpointer also means conversation state persists across turns for free, which was a requirement for multi-turn chat.

## Trade-offs

- **Gains:** Cycles work cleanly, tool dispatch is built in, conversation checkpointing comes for free, LangSmith traces the full graph execution, and the `StateGraph` pattern is what employers in AI engineering roles recognize as the production approach
- **Costs/Risks:** LangGraph's API has changed significantly between versions and will continue to. The `StateGraph` / node / edge model has a learning curve before you can write any actual logic. Debugging is harder than a simple call stack — you need LangSmith or careful logging to follow what the graph is doing.

## Consequences

All agent logic lives as LangGraph nodes and edges in `agent/graph.py`. Adding new investigation capabilities means adding tools to `agent/tools.py` and binding them to `investigate_node` — the graph topology itself doesn't change. Migrating away from LangGraph would mean rewriting the entire `agent/` layer.
