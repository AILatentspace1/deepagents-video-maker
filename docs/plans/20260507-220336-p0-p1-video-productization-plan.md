# P0/P1 Implementation Plan — Video Productization

- Created: 2026-05-07
- Review mode: `plan-eng-review`
- Source CEO review: [`E:\workspace\deepagents-video-maker\ceo_reviews\20260507-214703-ceo-review.md`](E:\workspace\deepagents-video-maker\ceo_reviews\20260507-214703-ceo-review.md)
- Repo: `E:\workspace\deepagents-video-maker`
- HEAD at planning time: `5afc302`

## Goal

Turn the current `video-maker-v2` DeepAgents workflow from a runnable artifact-gated adapter into a product loop that proves one credible video can be produced, reviewed, understood in UI, and judged publish-ready.

## Scope

### P0

1. **Golden demo path**
   - One canonical demo source fixture.
   - One deterministic smoke flow that proves Source Intake → Script checkpoint using native tools.
   - One documented approved-script → Build Scenes → Render Package path.
   - A human-readable `docs/golden-demo.md` with exact commands, expected artifacts, and limitations.

### P1

2. **Video production timeline in Web UI**
   - Show `video-maker-v2` milestones as first-class UI state.
   - Surface current status, blocking reason, and artifact links.
   - Keep existing chat/tool approval UX; add production visibility beside it.

3. **Post-render publish-readiness / taste gate**
   - Add a manual-first checklist artifact after `final/video.mp4` exists.
   - Do not block `render_package` technical completion initially.
   - Add a later optional gate for “publish-ready” status once the checklist is trusted.

## NOT in scope

- **Legacy `video-maker` compatibility** — v2-only is a deliberate simplification and must stay intact.
- **Full audio milestone** — audio can remain optional until the canonical video loop is reliable.
- **Automated LLM visual reviewer** — start with a deterministic/manual checklist before adding subjective model scoring.
- **Better Harness optimization beyond Scriptwriter** — useful later, but not the product proof.
- **Cloud deployment / auth hardening** — local product loop first; deployment is a later readiness layer.
- **P2 env hardening** — mention in docs where needed, but do not expand this plan into runner refactors.

## What already exists

| Existing asset | Reuse / change |
|---|---|
| `src/deepagents_video_maker/langchain_tools.py` native tools | Reuse. Add only minimal read-model helpers if UI needs structured state. |
| `src/deepagents_video_maker/state_store.py` `state.yaml` writer/loader | Reuse as canonical source of milestone truth. Extend carefully only if UI needs artifact refs or publish readiness. |
| `src/deepagents_video_maker/build_render_flow.py` build/render gates | Reuse. Add publish-readiness artifact adjacent to ratify output, not inside Remotion builder. |
| `skills/video-maker-v2/references/workflow-contract.md` | Update to include golden demo and publish-readiness handoff. |
| `web-ui/src/app/components/ChatInterface.tsx` tasks/files panel | Reuse visual patterns, but add a dedicated video timeline component instead of overloading generic todos. |
| `web-ui/src/app/hooks/useChat.ts` `StateType` | Extend with `video_maker?: VideoMakerUiState` if the LangGraph state can expose it; otherwise derive from tool messages/files as a fallback. |
| Current tests under `tests/deepagents_video_maker/` | Extend with golden demo and publish-readiness unit tests. |

## Architecture

### Desired product loop

```text
User request
  |
  v
vm_init_video_session
  |
  v
Source Intake gate
  | writes artifacts/source/source-manifest.md
  v
Script gate
  | writes artifacts/script/run-1/script-contract.json
  | writes artifacts/script/run-1/script.md
  v
USER SCRIPT REVIEW CHECKPOINT
  |
  | explicit approval
  v
Build Scenes gate
  | writes remotion-project/package.json
  | writes remotion-project/src/index.ts
  v
Render Package gate
  | writes final/video.mp4
  | writes final/thumbnail.jpg when available
  v
Publish-readiness review
  | writes final/publish-readiness.md
  | writes ratify/publish-readiness.json
  v
Golden demo docs + UI timeline show the whole path
```

### State and UI data flow

```text
Python native tools
  |
  | update state.yaml / ratify/*.json / artifact files
  v
FilesystemBackend virtual files + LangGraph thread state
  |
  +--> existing chat messages and tool results
  |
  +--> proposed VideoMakerUiState
        {
          output_dir,
          workflow_status,
          milestones[],
          artifacts[],
          current_blocker,
          next_actions[],
          publish_readiness?
        }
  |
  v
web-ui
  |
  +--> VideoProductionTimeline component
  +--> artifact link cards
  +--> script review / build approval callout
```

## Implementation phases

### Phase 0 — Lock fixtures and plan boundaries

**Files/modules likely touched**

- `docs/plans/`
- `docs/golden-demo.md`
- `tests/fixtures/` or `tests/deepagents_video_maker/fixtures/`
- `README.md` only if a short pointer is needed.

**Steps**

1. Create a minimal checked-in demo source fixture under `tests/fixtures/golden_demo_source/`.
2. Keep it small: markdown/text only, enough to generate a 1-3 minute script.
3. Define canonical demo request:
   - topic: `AI Agent Intro`
   - source: `folder`
   - duration: `1-3min`
   - style: `professional`
   - aspect_ratio: `16:9`
4. Document expected artifact paths and the user approval checkpoint.

**Acceptance criteria**

- A new contributor can understand the demo without reading old memory or chat history.
- The fixture does not require external APIs.
- The demo path does not imply websearch or full production rendering is deterministic.

### Phase 1 — Golden demo smoke flow

**Files/modules likely touched**

- `scripts/`
- `tests/deepagents_video_maker/`
- `src/deepagents_video_maker/session.py`
- `src/deepagents_video_maker/source_flow.py`
- `src/deepagents_video_maker/script_flow.py`

**Steps**

1. Add `scripts/run_golden_demo_smoke.py` or equivalent pytest-backed script.
2. Use native functions/tools directly; do not invoke an LLM in the base smoke.
3. Assert:
   - `goal.yaml` exists.
   - `state.yaml` has `source_intake` completed.
   - `artifacts/source/source-manifest.md` exists and lists fixture files.
   - `script-contract.json` can be generated.
   - script checkpoint behavior is documented even if generated script is fixture-assisted.
4. Add a checked-in approved script fixture for downstream build/render documentation.

**Acceptance criteria**

- `uv run pytest tests/deepagents_video_maker -q` stays green.
- `uv run python scripts/deepagents_video_maker.py --check` stays green.
- Golden demo smoke can run without `TAVILY_API_KEY`.

### Phase 2 — Publish-readiness artifact

**Files/modules likely touched**

- `src/deepagents_video_maker/build_render_flow.py`
- `src/deepagents_video_maker/langchain_tools.py`
- `src/deepagents_video_maker/models.py`
- `tests/deepagents_video_maker/test_build_render_flow.py`
- `skills/video-maker-v2/references/workflow-contract.md`

**Steps**

1. Add a deterministic `build_publish_readiness_report(state, checklist_input=None)` helper.
2. Write:
   - `final/publish-readiness.md`
   - `ratify/publish-readiness.json`
3. Checklist dimensions:
   - source faithfulness,
   - visual hierarchy,
   - pacing,
   - subtitle readability,
   - thumbnail usefulness,
   - publish decision: `publish_ready`, `needs_revision`, or `not_reviewed`.
4. Initially default to `not_reviewed` unless user or reviewer supplies checklist values.
5. Add `vm_build_publish_readiness_report(output_dir, ...)` tool.
6. Do **not** make this a hard blocker for `workflow_status=completed` yet; instead surface it as product readiness.

**Acceptance criteria**

- Missing final video returns a clear error.
- Existing render package completion semantics do not break.
- Checklist JSON is stable and testable.

### Phase 3 — UI timeline state contract

**Files/modules likely touched**

- `web-ui/src/app/types/types.ts`
- `web-ui/src/app/hooks/useChat.ts`
- `web-ui/src/app/components/`
- possibly `src/deepagents_video_maker/langchain_tools.py` if UI state must be emitted by tools.

**Steps**

1. Define `VideoMakerUiState` in `web-ui/src/app/types/types.ts`:
   - `outputDir`
   - `workflowStatus`
   - `milestones`
   - `artifacts`
   - `currentBlocker`
   - `nextActions`
   - `publishReadiness`
2. Extend `StateType` with `video_maker?: VideoMakerUiState`.
3. Add a pure mapping function in TypeScript:
   - input: `stream.values.video_maker`, `todos`, `files`, and recent tool outputs.
   - output: normalized timeline view model.
4. Prefer explicit `video_maker` state when available; fallback to files/tool messages only for older threads.

**Acceptance criteria**

- UI compiles with `pnpm --filter deepagent-video-maker-ui lint` or equivalent available script.
- No runtime crash when `video_maker` is absent.
- Existing chat, files, todos, and approval interrupts still render.

### Phase 4 — UI timeline component

**Files/modules likely touched**

- `web-ui/src/app/components/VideoProductionTimeline.tsx`
- `web-ui/src/app/components/ChatInterface.tsx`
- `web-ui/src/app/components/TasksFilesSidebar.tsx` only if shared layout is needed.

**Steps**

1. Add `VideoProductionTimeline` component.
2. Render milestone states:
   - pending,
   - in progress,
   - blocked,
   - completed,
   - failed.
3. Show artifact links/cards:
   - source manifest,
   - script,
   - Remotion project,
   - final video,
   - thumbnail,
   - publish-readiness report.
4. Show checkpoint callouts:
   - “Script ready for review”
   - “Build scenes waiting for explicit approval”
   - “Publish readiness not reviewed”
5. Mount it above the composer or in the existing metadata panel so it remains visible during long runs.

**Acceptance criteria**

- Empty/new thread shows no misleading timeline.
- Active video run shows next action clearly.
- Long file paths truncate but remain copyable/openable through existing file view behavior where possible.

### Phase 5 — Documentation and review hooks

**Files/modules likely touched**

- `docs/golden-demo.md`
- `README.md`
- `AGENTS.md`
- `skills/video-maker-v2/SKILL.md`
- `skills/video-maker-v2/references/workflow-contract.md`

**Steps**

1. Document golden demo commands.
2. Document the UI timeline states and how they map to native tools.
3. Document publish-readiness as product readiness, not technical render success.
4. Add a short “known limitations” section:
   - no full automated taste review yet,
   - websearch requires `TAVILY_API_KEY`,
   - render requires local Remotion dependencies and browser/ffmpeg availability.

**Acceptance criteria**

- New docs match actual commands in `package.json` and `scripts/`.
- Docs do not claim build/render is automatic before script approval.

## Test plan

### Python tests

Add or extend:

- `tests/deepagents_video_maker/test_golden_demo_smoke.py`
- `tests/deepagents_video_maker/test_build_render_flow.py`
- `tests/deepagents_video_maker/test_langchain_tools.py`
- `tests/deepagents_video_maker/test_state_store.py` only if state schema changes.

Assertions:

- Golden fixture produces source manifest without network.
- Script checkpoint cannot start before source intake completion.
- Build scenes still rejects missing `script_approved=True`.
- Publish-readiness helper rejects missing final video with clear error.
- Publish-readiness helper writes markdown + JSON with stable schema.

### UI tests

If the current UI has no test harness, add minimal component-level tests only if the repo already supports them. Otherwise keep Phase 4 verified by:

- TypeScript compile / lint.
- Manual browser smoke with `pnpm agent:dev` + `pnpm ui:dev`.
- Story-like fixture object rendered through the component if easy to add.

### End-to-end smoke

Recommended manual smoke after implementation:

```powershell
$env:UV_CACHE_DIR='E:\workspace\deepagents-video-maker\.uv-cache'
uv run python scripts/deepagents_video_maker.py --check
uv run pytest tests/deepagents_video_maker -q
pnpm harness:validate
pnpm agent:dev
pnpm ui:dev
```

On this Windows machine, if `pnpm` hits `C:\Users\ADMINI~1` temp permission issues, rerun with:

```powershell
$env:TEMP='C:\tmp'
$env:TMP='C:\tmp'
```

## Failure modes

| Codepath | Realistic failure | Test? | Error handling? | User-visible? | Gap |
|---|---|---:|---:|---:|---|
| Golden demo source fixture | Fixture path missing after checkout | Yes | Yes | Clear test failure | No |
| Source manifest | Folder contains too many/unsupported files | Existing partial | Partial | Manifest lists first 200 | No |
| Script checkpoint | Agent claims script done but file missing | Existing | Yes via ratify | Clear ratify error | No |
| Build scenes | User approval skipped accidentally | Existing | Yes | Clear tool error | No |
| Render package | `ffprobe` missing | Existing/extend | Yes | Ratify issue | No |
| Publish readiness | Final video missing | Add | Yes | Clear tool error | No |
| Publish readiness | Subjective checklist defaults to false confidence | Add | Yes: `not_reviewed` default | Visible in UI | No |
| UI timeline | `video_maker` state absent on old threads | Add TS fallback | Yes | Timeline hidden | No |
| UI artifact links | Files live on local disk but not in LangGraph `files` state | Needs manual smoke | Partial | Link may be non-clickable | WARNING |
| UI status | Stale state after tool update | Needs manual smoke | Partial | User sees outdated milestone | WARNING |

## Critical engineering decisions

### Decision 1 — Do publish-readiness as advisory first

Recommendation: **advisory first, not a hard workflow blocker**.

Reason: the current technical completion path is already clean. Blocking `workflow_status=completed` on a subjective gate would blur “render succeeded” with “publish approved” and make failure semantics harder to explain.

Implementation:

- Keep `render_package` technical status unchanged.
- Add `publish_readiness.status`.
- UI displays “Rendered, not yet publish-reviewed” when applicable.

### Decision 2 — Make UI timeline tolerant of partial state

Recommendation: **derive from explicit `video_maker` state when present, but degrade gracefully**.

Reason: LangGraph thread state and file state may vary across local dev, old threads, and SDK versions. The UI should never crash because a production timeline field is absent.

Implementation:

- Type all fields optional at the boundary.
- Normalize into required display fields in one pure function.
- Test missing/partial states.

### Decision 3 — Keep golden demo non-networked

Recommendation: **folder-source fixture first**.

Reason: P0 is trust and repeatability. Websearch adds API keys, network variability, and source drift before the product loop is proven.

Implementation:

- Use `source=folder`.
- Add a separate future TODO for a `websearch` demo once Tavily-backed source intake is stable in automation.

## Parallelization strategy

| Step | Modules touched | Depends on |
|---|---|---|
| Golden demo smoke | `scripts/`, `tests/`, `docs/` | — |
| Publish-readiness artifact | `src/deepagents_video_maker/`, `tests/`, `skills/` | — |
| UI state contract | `web-ui/src/app/types`, `web-ui/src/app/hooks` | — |
| UI timeline component | `web-ui/src/app/components` | UI state contract |
| Docs finalization | `docs/`, `README.md`, `AGENTS.md`, `skills/` | Golden demo smoke + publish-readiness |

Parallel lanes:

- **Lane A:** Golden demo smoke → docs finalization.
- **Lane B:** Publish-readiness artifact → docs finalization.
- **Lane C:** UI state contract → UI timeline component.

Execution order:

1. Launch Lane A, Lane B, and first half of Lane C in parallel if using worktrees.
2. Merge A/B after tests pass.
3. Finish UI component after the state contract is agreed.
4. Final docs pass after all behavior is real.

Conflict flags:

- Lane A and Lane B may both touch `docs/` and `skills/video-maker-v2/references/workflow-contract.md`; coordinate final docs sequentially.
- Lane C should avoid Python source unless explicit `video_maker` state emission is added.

## Rollout checklist

1. Implement golden fixture and smoke test.
2. Add publish-readiness helper/tool and tests.
3. Add UI types and normalization.
4. Add timeline component and mount it.
5. Update docs.
6. Run validation:
   - `uv run python scripts/deepagents_video_maker.py --check`
   - `uv run pytest tests/deepagents_video_maker -q`
   - `pnpm harness:validate`
   - UI compile/lint command available in `web-ui/package.json`
7. Run one manual local UI smoke.

## Completion summary

- Step 0: Scope Challenge — scope accepted with P2 env hardening deferred.
- Architecture Review: 2 issues found — state contract must be tolerant; publish-readiness must not block technical completion yet.
- Code Quality Review: 1 issue found — avoid spreading timeline parsing across UI components.
- Test Review: diagram produced, 4 gaps identified.
- Performance Review: 1 issue found — UI must not poll large local artifacts.
- NOT in scope: written.
- What already exists: written.
- TODO candidates: 3 items embedded in plan, not added to `TODOS.md`.
- Failure modes: 0 critical gaps flagged if listed tests are implemented.
- Outside voice: skipped.
- Parallelization: 3 lanes, 3 parallel starts / docs sequential finish.
- Lake Score: 8/10 — complete enough for product proof without expanding into audio/cloud/eval.

## TODO candidates

1. **Add websearch golden demo later**
   - Depends on stable `TAVILY_API_KEY` setup and source URL completeness.
2. **Promote publish-readiness to hard gate later**
   - Depends on repeated checklist usefulness across real videos.
3. **Add automated visual/taste reviewer later**
   - Depends on a small corpus of accepted/rejected rendered videos.
