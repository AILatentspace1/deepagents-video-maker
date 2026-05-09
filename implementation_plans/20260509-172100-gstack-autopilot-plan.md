# GStack Autopilot Implementation Plan - deepagents-video-maker

- Run time: 2026-05-09T17:21:00+08:00
- Worktree: `C:\Users\Administrator\.codex\worktrees\a011\deepagents-video-maker`
- HEAD: `7b61660`
- Base branch: `master`
- Current branch: detached `HEAD` (branch creation blocked by `.git/refs` permission)

## Goal

Keep the canonical `video-maker-v2` workflow verifiable for automations and contributors: Python/native path, golden demo, playable render proof, UI build, and harness validation should have commands that either pass after documented bootstrap or fail with an accurate prerequisite.

## Scope

Safe bounded scope after branch creation is restored:

1. **Windows/Codex pnpm reproducibility docs**
   - Files: `AGENTS.md`, `docs/golden-demo.md`, optionally `CLAUDE.md` if the repo wants agent-facing parity.
   - Change: add a short Windows/Codex note: if the user-global `pnpm.exe` shim fails with `EPERM lstat C:\Users\Administrator` or `C:\Users\ADMINI~1`, use `corepack pnpm ...` from the repo root. Keep normal `pnpm ...` commands for standard shells.
   - Risk: low. Docs-only. Avoid changing package manager semantics.

2. **Harness prerequisite accuracy**
   - Files: `AGENTS.md`, `docs/golden-demo.md`, `harness/README.md`, optionally `package.json` only if the project chooses to add a bootstrap wrapper.
   - Change: state clearly that `pnpm harness:validate` requires `better-harness` to be installed. Do not claim it is green immediately after `uv sync` unless `better-harness` is declared or bootstrapped.
   - Risk: low for docs-only; medium if changing dependencies because `better-harness` source/install path may be external.

3. **Live UI proof follow-up**
   - Files: no source edit initially; artifact only under `eng_reviews/` or `test-results/`.
   - Action: after `corepack pnpm install`, start `corepack pnpm agent:dev` and `corepack pnpm ui:dev`, then use browser QA to prove `stream.values.video_maker` renders `VideoProductionTimeline` for a real thread.
   - Risk: medium runtime flake; do not change UI code unless proof exposes a bug.

## Explicit safe-to-implement subset for this run

Initially no source/package/docs code edit was safe because:

- The worktree is detached.
- `git switch -c codex/gstack-autopilot-*` and `git switch -c codex-gstack-autopilot-*` both fail with `.git/refs/heads/*.lock` permission denied.
- The automation instructions explicitly prohibit working directly on detached `HEAD` before edits.

After the branch issue was fixed, the safe subset implemented in this run was:

- Wrote this plan artifact.
- Wrote the paired review artifact.
- Bootstrapped Python dependencies with repo-local cache/temp.
- Installed Node dependencies via `corepack pnpm install --frozen-lockfile --ignore-scripts` after proving plain `pnpm` shim is the failing layer.
- Updated `AGENTS.md`, `docs/golden-demo.md`, and `harness/README.md` with Corepack fallback and `better-harness` prerequisite clarity.
- Ran fresh verification commands.

## Proposed patch once branch creation works

### Patch A - docs-only command accuracy

Files:

- `AGENTS.md`
- `docs/golden-demo.md`
- `harness/README.md`

Content shape:

````markdown
### Windows/Codex pnpm shim note

If `pnpm ...` fails before running repo scripts with `EPERM lstat C:\Users\Administrator` or `C:\Users\ADMINI~1`, run the same command through Corepack from the repo root:

```powershell
corepack pnpm install --frozen-lockfile
corepack pnpm golden:playable
corepack pnpm ui:build
```

This uses the repo `packageManager` pin (`pnpm@9.15.0`) and avoids the user-profile pnpm executable shim.
````

### Patch B - harness prerequisite clarity

Files:

- `AGENTS.md`
- `harness/README.md`

Content shape:

```markdown
`pnpm harness:validate` requires the external `better-harness` CLI to be installed in the active `uv` environment. A fresh `uv sync` does not install it yet; follow `harness/README.md` first or expect `Failed to spawn: better-harness`.
```

Do not add a dependency until the team decides whether `better-harness` should be vendored, pulled from the DeepAgents repo, or installed from a package index.

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Editing while detached | Unreviewable/uncommitted changes | Stop source edits until branch creation is fixed. |
| Switching all docs from `pnpm` to `corepack pnpm` | Could annoy normal local developers | Present Corepack as Windows/Codex fallback, not global replacement. |
| Adding `better-harness` blindly | May pull wrong package/source | Keep docs-only unless install source is verified. |
| UI proof requires local ports | Dev servers may hang or need env keys | Use folder-source golden prompt and local noop auth; stop if model keys are required. |

## Verification commands

Use repo-local cache/temp on Windows:

```powershell
$env:UV_CACHE_DIR = Join-Path (Get-Location) '.uv-cache'
$env:TEMP = Join-Path (Get-Location) '.tmp'
$env:TMP = $env:TEMP
uv sync
corepack pnpm install --frozen-lockfile --ignore-scripts
uv run pytest tests/deepagents_video_maker -q
uv run python scripts/deepagents_video_maker.py --check
corepack pnpm golden:script
corepack pnpm golden:render
corepack pnpm golden:playable
corepack pnpm ui:build
corepack pnpm harness:validate  # expected to fail until better-harness is installed
```

## Current verification snapshot

- PASS: `uv sync`
- PASS: `corepack pnpm install --frozen-lockfile --ignore-scripts`
- PASS: `uv run pytest tests/deepagents_video_maker -q`
- PASS: `uv run python scripts/deepagents_video_maker.py --check`
- PASS: `uv run python scripts/run_golden_demo_smoke.py`
- PASS: `uv run python scripts/run_golden_render_smoke.py`
- PASS: `uv run python scripts/run_golden_playable_smoke.py`
- PASS: `corepack pnpm golden:script`
- PASS: `corepack pnpm golden:render`
- PASS: `corepack pnpm golden:playable`
- PASS: `corepack pnpm ui:build`
- FAIL: plain `pnpm ...` due `EPERM lstat C:\Users\Administrator`/`C:\Users\ADMINI~1`
- FAIL: `harness:validate` due missing `better-harness`

## Commit plan

Commit is no longer blocked after the branch issue was fixed:

```powershell
git add AGENTS.md docs/golden-demo.md harness/README.md eng_reviews/<review>.md implementation_plans/<plan>.md
git commit -m "docs: clarify Windows verification prerequisites"
```

Do not push or open a PR unless explicitly instructed.
