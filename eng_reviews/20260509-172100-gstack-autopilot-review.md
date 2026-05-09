# GStack Autopilot Review - deepagents-video-maker

- Run time: 2026-05-09T17:21:00+08:00
- Worktree: `C:\Users\Administrator\.codex\worktrees\a011\deepagents-video-maker`
- HEAD: `7b61660`
- Base branch detected: `master`
- Branch state: detached `HEAD`; attempts to create `codex/gstack-autopilot-*` and `codex-gstack-autopilot-*` failed with `Permission denied` writing `E:/workspace/deepagents-video-maker/.git/refs/heads/*.lock`.
- Review mode: autonomous repository reality check with gstack-style CEO/Eng/DX focus. Dual external model voices were not run in this desktop automation; findings below are grounded in repo files and fresh commands.

## What I checked

- `AGENTS.md`, `docs/golden-demo.md`, `package.json`, `pyproject.toml`
- `src/deepagents_video_maker/`, especially `ui_state.py`, `middleware.py`, and native tool payloads in `langchain_tools.py`
- `web-ui/src/app/hooks/useChat.ts`, `web-ui/src/app/components/ChatInterface.tsx`, `web-ui/src/app/components/VideoProductionTimeline.tsx`, and UI types
- `skills/video-maker-v2/` and harness references only as needed for workflow-contract and scriptwriter scope
- Existing tests under `tests/deepagents_video_maker/`

## Executive summary

The canonical `video-maker-v2` native path is healthy: Python tests, CLI check, script checkpoint smoke, downstream render smoke, playable MP4 smoke, and `corepack pnpm ui:build` all pass in this worktree. The strongest blocker is not the product pipeline. It is automation reproducibility: this detached worktree cannot create a git branch or commit, the user-global `pnpm.exe` shim fails before scripts run, and `pnpm harness:validate` points at `uv run better-harness` although `better-harness` is not installed in this fresh `uv sync` environment.

## Findings

### P0 - Git branch/commit operations are blocked in this worktree

Evidence:

```text
git switch -c codex/gstack-autopilot-20260509-171102
fatal: cannot lock ref 'refs/heads/codex/gstack-autopilot-20260509-171102': Unable to create 'E:/workspace/deepagents-video-maker/.git/refs/heads/codex/gstack-autopilot-20260509-171102.lock': Permission denied
```

Impact: the automation instruction says never edit on `master`/`main` or detached `HEAD`; because the worktree is detached and branch creation fails, safe source changes and commit are blocked. This is why this run limits implementation to review/plan artifacts.

### P1 - Plain `pnpm` is not reproducible from this Codex worktree, but `corepack pnpm` is

Evidence:

```text
pnpm --version
Error: EPERM: operation not permitted, lstat 'C:\Users\ADMINI~1'
```

`pnpm install --frozen-lockfile` failed the same way before any repo script ran. Setting `TEMP`, `TMP`, `HOME`, and `USERPROFILE` did not fix the user-global shim. However:

```text
corepack pnpm --version -> 9.15.0
corepack pnpm install --frozen-lockfile --ignore-scripts -> 0
corepack pnpm ui:build -> 0
```

Impact: `AGENTS.md` and `docs/golden-demo.md` currently teach `pnpm ...` as the primary path. In this automation environment, that path fails before reaching repo wrappers. The accurate workaround is to invoke the project package manager through Corepack, or ensure `pnpm` resolves to a non-user-profile shim.

### P1 - `harness:validate` is documented as runnable, but the fresh Python environment lacks `better-harness`

Evidence:

```text
uv run better-harness validate harness/video-maker-minimal.toml
error: Failed to spawn: `better-harness`
  Caused by: program not found
```

`package.json` maps `harness:validate` to `uv run better-harness validate ...`, while `pyproject.toml` dev dependencies do not include `better-harness`. Repo docs under `harness/README.md` and `harness/GITHUB_ISSUES.md` still describe manual installation from the DeepAgents repo.

Impact: fresh contributors and automations cannot trust `pnpm harness:validate` after `uv sync`. Either document it as optional/manual until installed, or make the dependency/bootstrap explicit.

### P2 - UI/backend `video_maker` state contract is now present and type-checked

Evidence:

- Backend projection: `src/deepagents_video_maker/ui_state.py` builds `video_maker` with milestones, artifacts, blockers, next actions, and publish readiness.
- Middleware: `src/deepagents_video_maker/middleware.py` attaches `video_maker` to top-level LangGraph state after native `vm_*` tool calls.
- Native tools: `src/deepagents_video_maker/langchain_tools.py` wraps state-changing payloads with `_with_ui_state`.
- UI: `web-ui/src/app/hooks/useChat.ts` exposes `videoMaker: stream.values.video_maker`; `ChatInterface.tsx` renders `VideoProductionTimeline`.
- Test: `tests/deepagents_video_maker/test_ui_state.py` covers projection and middleware update.
- Verification: `corepack pnpm ui:build` passed TypeScript and production build.

Remaining gap: this run did not start `pnpm agent:dev`/`pnpm ui:dev` or capture a live browser proof that a real LangGraph thread pushes `stream.values.video_maker` into the timeline. That is now the main proof gap, not a static contract gap.

## Verification results

| Command | Result | Notes |
|---|---:|---|
| `uv sync` with worktree `.uv-cache` | PASS | Created fresh `.venv`; ignored by git. |
| `pnpm install --frozen-lockfile` | FAIL | User-global `pnpm.exe` hits `EPERM lstat C:\Users\Administrator`. |
| `corepack pnpm install --frozen-lockfile --ignore-scripts` | PASS | Uses `pnpm@9.15.0` from `packageManager`. |
| `uv run pytest tests/deepagents_video_maker -q` | PASS | 87 tests passed, 1 LangGraph warning. |
| `uv run python scripts/deepagents_video_maker.py --check` | PASS | v2 files present. |
| `uv run python scripts/run_golden_demo_smoke.py` | PASS | Script checkpoint proof. |
| `uv run python scripts/run_golden_render_smoke.py` | PASS | Simulated downstream render/package proof. |
| `uv run python scripts/run_golden_playable_smoke.py` | PASS | Playable MP4 proof via local ffmpeg path. |
| `corepack pnpm golden:script` | PASS | Package alias works when invoked through Corepack. |
| `corepack pnpm golden:render` | PASS | Package alias works when invoked through Corepack. |
| `corepack pnpm golden:playable` | PASS | Package alias works when invoked through Corepack. |
| `uv run better-harness validate harness/video-maker-minimal.toml` | FAIL | `better-harness` command missing. |
| `corepack pnpm harness:validate` | FAIL | Same missing `better-harness` root cause. |
| `corepack pnpm ui:build` | PASS | Next.js 16 production build passed. |

## Implemented safe bounded fix after branch creation was restored

- Updated `AGENTS.md` with a Windows/Codex `corepack pnpm ...` fallback for user-profile `pnpm` shim failures.
- Updated `docs/golden-demo.md` with the same Corepack fallback and an explicit `better-harness` prerequisite note.
- Updated `harness/README.md` to state that a fresh `uv sync` does not install `better-harness` and to show Corepack harness commands for Windows/Codex worktrees.

## Not in scope for this run

- No credential, deployment, publishing, or broad workflow rewrite changes.
- No live browser/UI thread proof. Static UI build passed; runtime proof is a separate next step.

## Recommended next step

Fix the git ref permission/branch creation issue first. Then make the smallest reproducibility patch: document/use `corepack pnpm` for Codex Windows worktrees and clarify that `better-harness` requires separate installation or an explicit dependency/bootstrap step.
