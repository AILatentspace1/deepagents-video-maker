# CLAUDE.md

## Commands

```bash
uv sync                          # install Python deps
pnpm install                     # install Node deps
uv run pytest tests/deepagents_video_maker -q   # run tests
uv run python scripts/deepagents_video_maker.py --check  # sanity check
uv run python scripts/run_golden_demo_smoke.py  # deterministic local golden demo to script checkpoint
pnpm golden:playable             # playable local MP4 proof
pnpm test:py                     # same pytest suite via package script
pnpm harness:validate            # validate v2 scriptwriter better-harness config
pnpm harness:run                 # run v2 scriptwriter optimization loop
pnpm ui:build                    # production UI build via Windows-safe wrapper
pnpm agent:dev                   # LangGraph dev server
pnpm ui:dev                      # Next.js UI dev server
```

## Key Files

- `src/deepagents_video_maker/agent.py` — `create_video_maker_agent()` factory
- `src/deepagents_video_maker/langchain_tools.py` — typed native `video-maker-v2` tools
- `skills/video-maker-v2/` — canonical project skill, contracts, and subagent prompts
- `.deepagents/skills/video-maker-v2-*` — DeepAgents runtime skill wrappers
- `scripts/deepagents_video_maker.py` — CLI runner
- `scripts/build-ui.mjs` — Windows-safe Next production build wrapper
- `docs/golden-demo.md` — canonical local demo ladder and validation commands

## Conventions

- Python: `uv run ...` always
- Node: `pnpm ...` always
- Default workflow is `video-maker-v2`; legacy `video-maker` is not supported
- No `.claude/skills` path references in code — use `skills/video-maker-v2/` instead
- Build/render requires explicit user approval after the script checkpoint
- Commit style: conventional commits (feat, fix, docs, chore, refactor, test)

## Better-Harness (scriptwriter-only)

Better-harness optimization is intentionally scoped to the v2 scriptwriter prompt:

```bash
pnpm harness:validate
pnpm harness:run
```

The active config is `harness/video-maker-minimal.toml`, and its editable surface is:

- `skills/video-maker-v2/agents/scriptwriter.md`

Do not reintroduce legacy `skills/video-maker/` or `tests/evals` package-script wiring unless the project explicitly decides to restore a broader eval harness.
