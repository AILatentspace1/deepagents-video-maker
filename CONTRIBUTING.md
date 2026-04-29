# Contributing

Welcome! This guide helps first-time contributors set up the repository and run the basic validation commands.

## First-time setup

### Prerequisites

- **`uv`** — Python package manager. Install with `python -m pip install uv` if not present.
- **`pnpm`** — Node package manager. Install with `corepack enable` if not present.

### Setup commands

```bash
# 1. Install Python dependencies
uv sync

# 2. Install Node dependencies
pnpm install
```

## Validation commands

Run these commands to verify your setup is working before making changes:

```bash
# Run the Python test suite
uv run pytest tests/deepagents_video_maker -q

# Run the CLI sanity check
uv run python scripts/deepagents_video_maker.py --check
```

## Tooling conventions

- **Python commands** must always use `uv run ...` (e.g. `uv run pytest`, `uv run python`).
- **Node commands** must always use `pnpm ...` (e.g. `pnpm install`, `pnpm agent:dev`).

## Other useful commands

```bash
# Start the LangGraph dev server
pnpm agent:dev

# Start the Next.js UI dev server
pnpm ui:dev
```

## GitHub issues and project

Issues are tracked in this repository with labels, milestones, and a GitHub Project board. See [`docs/github-project.md`](docs/github-project.md) for details on the project structure, labels, and how to pick up a `good first issue`.

When working on an issue, make sure your PR:

- links to the issue (e.g. `Closes #<number>`),
- passes `uv run pytest tests/deepagents_video_maker -q`, and
- follows the `uv run` / `pnpm` conventions above.
