# CLAUDE.md

## Commands

```bash
uv sync                          # install Python deps
pnpm install                     # install Node deps
uv run pytest tests/deepagents_video_maker -q   # run tests
uv run python scripts/deepagents_video_maker.py --check  # sanity check
pnpm agent:dev                   # LangGraph dev server
pnpm ui:dev                      # Next.js UI dev server
```

## Key Files

- `src/deepagents_video_maker/agent.py` — `create_video_maker_agent()` factory
- `src/deepagents_video_maker/langchain_tools.py` — typed tools (vm_build_researcher_task etc.)
- `skills/video-maker/SKILL.md` — Producer skeleton
- `scripts/deepagents_video_maker.py` — CLI runner

## Conventions

- Python: `uv run ...` always
- Node: `pnpm ...` always
- No `.claude/skills` path references in code — use `skills/video-maker/` instead
- Commit style: conventional commits (feat, fix, docs, chore, refactor, test)

## Harness Optimization (better-harness)

Autonomous optimization of agent prompts using eval-driven feedback:

```bash
# Run eval tests
pnpm test:evals

# Validate harness config
pnpm harness:validate

# Run optimization loop (requires better-harness installed)
pnpm harness:run
```

See `harness/README.md` for setup instructions.
