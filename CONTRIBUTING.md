# Contributing to ProcessIQ

## Setup

```bash
git clone https://github.com/SkybrushThriftwood/processIQ.git
cd processIQ
uv sync --group dev
cp .env.example .env
# Add your OPENAI_API_KEY or ANTHROPIC_API_KEY to .env
pre-commit install
```

## Development Workflow

```bash
# Run tests (fast, no LLM calls)
uv run pytest -m "not llm"

# Run all tests including LLM integration tests
uv run pytest

# Lint and format
uv run ruff check src/
uv run ruff format src/

# Type check
uv run mypy src/
```

## Design Principles

Before making changes, read `docs/PROJECT_BRIEF.md`. The key constraint:

**Algorithms calculate facts. The LLM makes judgments.**

The agent graph (`agent/graph.py`) has 4 nodes. Don't add nodes without a clear reason — the current structure handles most analysis needs through the `analyze.j2` prompt. Complexity belongs in the prompt and data models, not the graph topology.

Other principles:
- The UI only talks to the agent through `agent/interface.py` — never import from `agent/graph.py` directly in UI code
- No dead code — delete when removing a feature, don't comment out
- Every module starts with `logger = logging.getLogger(__name__)`
- Every agent node logs entry and what it produced

## Making Changes

1. Check `CHANGELOG.md` for recent decisions before starting — some design choices that look wrong are intentional
2. Run tests before and after your change
3. Update `CHANGELOG.md` for any non-trivial change (new features, architectural decisions, significant fixes)

## Submitting a Pull Request

- Keep PRs focused — one concern per PR
- Include a description of what problem the change solves
- Ensure `pytest -m "not llm"` passes
- Ensure `ruff check src/` passes with no errors

## Prompt Templates

Prompts live in `src/processiq/prompts/` as Jinja2 `.j2` files. When editing prompts:
- Test with varied inputs, not just the happy path
- Vague or conflicting instructions in the prompt tend to produce inconsistent structured output — be explicit
- `extraction.j2` controls the smart interviewer behavior; `analyze.j2` controls recommendation quality

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
