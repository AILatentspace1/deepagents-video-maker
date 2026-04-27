# AGENTS.md

## Quick Start

```bash
uv sync && pnpm install
uv run pytest tests/deepagents_video_maker -q   # should be all green
uv run python scripts/deepagents_video_maker.py --check
pnpm agent:dev  # starts LangGraph dev server
```

## Architecture

- `src/deepagents_video_maker/` — DeepAgents Producer factory + typed tools (research/script milestones)
- `skills/video-maker/` — Business knowledge markdown (milestones, agent prompts, ratify rules)
- `.deepagents/skills/` — Subagent skill wrappers loaded by DeepAgents runtime
- `web-ui/` — Next.js chat UI connected to LangGraph dev server
- `scripts/deepagents_video_maker.py` — CLI entry point (`uv run python scripts/deepagents_video_maker.py`)
- `scripts/smoke_skills_research_script.py` — Deterministic typed-tool smoke test

## Key Conventions

- Python commands: always `uv run ...`
- Node commands: always `pnpm ...`
- Environment variables: copy `.env.example` to `.env` and fill in keys
- `ORCHESTRATOR_SKILLS_ROOT` points to repo root (auto-set by agent.py)
