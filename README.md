# deepagents-video-maker

DeepAgents-native video-maker orchestrator. Current runnable pipeline: **research → script**. Assets/assembly milestone will be integrated via a standalone rendering toolchain in a future plan.

## Quick Start

```bash
# Python env
uv sync

# Note: run Python commands via `uv run ...`

# Node packages
pnpm install

# Note: run Node commands via `pnpm ...`

# Run tests
pnpm test:py

# Or (canonical):
uv run pytest tests/deepagents_video_maker -q

# Repo sanity check
uv run python scripts/deepagents_video_maker.py --check

# Start LangGraph dev server
pnpm agent:dev
```

## Contributing (first-time setup)

If you're new to the repo, the fastest path to a green local validation run is:

```bash
uv sync
pnpm install
uv run pytest tests/deepagents_video_maker -q
uv run python scripts/deepagents_video_maker.py --check
```

For project/issue workflow conventions, see `docs/github-project.md`.

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
