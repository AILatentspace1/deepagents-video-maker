# AGENTS.md

## Quick Start

```bash
uv sync && pnpm install
uv run pytest tests/deepagents_video_maker -q   # should be all green
uv run python scripts/deepagents_video_maker.py --check
uv run python scripts/run_golden_demo_smoke.py  # deterministic local golden demo to script checkpoint
pnpm test:py    # same pytest suite via package script
pnpm harness:validate  # validate better-harness config
pnpm agent:dev  # starts LangGraph dev server
pnpm ui:dev     # starts Next.js chat UI
```

## Architecture

- `src/deepagents_video_maker/` — DeepAgents Producer factory + typed tools for `video-maker-v2`
- `skills/video-maker-v2/` — Business knowledge markdown and v2 workflow contracts
- `.deepagents/skills/` — Subagent skill wrappers loaded by DeepAgents runtime
- `web-ui/` — Next.js chat UI connected to LangGraph dev server
- `scripts/deepagents_video_maker.py` — CLI entry point (`uv run python scripts/deepagents_video_maker.py`)

## Key Conventions

- Python commands: always `uv run ...`
- Node commands: always `pnpm ...`
- Environment variables: copy `.env.example` to `.env` and fill in keys
- `ORCHESTRATOR_SKILLS_ROOT` points to repo root (auto-set by agent.py)
- Default workflow is `video-maker-v2`; legacy `video-maker` is not supported
- Current runnable path is Source Intake → Script → user review checkpoint → Build Scenes → Render Package; build/render requires explicit user approval
- Golden demo path is documented in `docs/golden-demo.md`; it uses local folder fixtures and stops at the script checkpoint
- Native DeepAgents tools follow gated stages: `vm_init_video_session` → `vm_start_source_intake`/`vm_ratify_source_intake` → `vm_start_script`/`vm_build_scriptwriter_task`/`vm_ratify_script` → `vm_start_build_scenes(script_approved=True)`/`vm_build_remotion_task`/`vm_ratify_build_scenes` → `vm_start_render_package`/`vm_render_remotion_project`/`vm_package_render_output`/`vm_ratify_render_package`; then optionally `vm_build_publish_readiness_report`
- `folder` source writes `artifacts/source/source-manifest.md` and does not create `research.md`; `websearch` source requires `TAVILY_API_KEY`
- Publish readiness runs after `final/video.mp4` exists, writes `final/publish-readiness.md` and `ratify/publish-readiness.json`, and is advisory, not a replacement for render ratify
- Better-harness optimization is scoped to `skills/video-maker-v2/agents/scriptwriter.md`; use `pnpm harness:validate` before `pnpm harness:run`
