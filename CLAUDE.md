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

## Better-Harness (Autonomous Optimization)

The project integrates [better-harness](https://github.com/langchain-ai/deepagents/tree/main/examples/better-harness)
for autonomous harness optimization.  An outer Deep Agent reads eval failures
and proposes edits to configurable harness surfaces (prompts, tools, skills).
Changes are kept only when the combined pass count improves.

### Eval structure

| Directory | Purpose |
|-----------|---------|
| `tests/evals/train/` | 5 training eval cases — guide the outer agent's proposals |
| `tests/evals/holdout/` | 3 regression-guard cases — reject proposals that break existing behavior |
| `tests/evals/scorecard/` | 2 final validation cases — confirm end-to-end correctness |

### Running evals

```bash
pnpm evals:train        # run train eval suite
pnpm evals:holdout      # run holdout (regression) suite
pnpm evals:scorecard    # run scorecard (end-to-end) suite
pnpm evals:all          # run all eval suites

# With report output (used by better-harness internally)
uv run pytest tests/evals/train --evals-report-file /tmp/report.json
uv run pytest tests/evals/train --model claude-sonnet-4-6 -q
```

### Harness configuration

`harness/video-maker.toml` maps all optimisable surfaces:

| Surface | Kind | Target |
|---------|------|--------|
| Producer prompt | `workspace_file` | `skills/video-maker/SKILL.md` |
| Researcher agent | `workspace_file` | `skills/video-maker/agents/researcher.md` |
| Scriptwriter agent | `workspace_file` | `skills/video-maker/agents/scriptwriter.md` |
| LangChain tools | `workspace_file` | `src/deepagents_video_maker/langchain_tools.py` |
| Agent factory | `workspace_file` | `src/deepagents_video_maker/agent.py` |
| Research milestone | `workspace_file` | `skills/video-maker/milestones/research.md` |
| Script milestone | `workspace_file` | `skills/video-maker/milestones/script.md` |
| Research ratify rules | `workspace_file` | `skills/video-maker/ratify/research-rules.md` |
| Script ratify rules | `workspace_file` | `skills/video-maker/ratify/script-rules.md` |

### Running the optimization loop

```bash
# Validate config first
pnpm harness:validate
# → uv run better-harness validate harness/video-maker.toml

# Baseline run (1 iteration, no changes)
pnpm harness:run
# → uv run better-harness run harness/video-maker.toml \
#       --output-dir runs/baseline --max-iterations 1

# Full optimization run
uv run better-harness run harness/video-maker.toml \
    --output-dir runs/optimised --max-iterations 10
```

