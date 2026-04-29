# deepagents-video-maker

DeepAgents-native video-maker orchestrator. Current runnable pipeline: **research → script**. Assets/assembly milestone will be integrated via a standalone rendering toolchain in a future plan.

## Quick Start

```bash
# Python env
uv sync  # requires `uv` installed (see below)

# Node packages
pnpm install

# Run tests
pnpm test:py

# Start LangGraph dev server
pnpm agent:dev
```

### Prerequisites

- `uv` (Python package manager)
  - If `uv` is not installed, `python -m pip install uv` is sufficient for dev.
- `pnpm` (Node package manager)
  - If `pnpm` is not installed, `corepack enable` will provide it.

## Architecture

```
src/deepagents_video_maker/   # Python orchestration layer (DeepAgents Producer)
skills/video-maker/           # Business knowledge md (milestones, agents, ratify)
.deepagents/skills/           # Subagent skill wrappers (researcher, scriptwriter)
web-ui/                       # Next.js + LangGraph Dev UI
scripts/                      # CLI runner + smoke tests
tests/                        # pytest unit tests
```

## Design Docs

See `docs/design/` for architecture and plan documents.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for first-time setup, validation commands, and contribution guidelines.
