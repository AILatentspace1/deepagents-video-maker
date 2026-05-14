# CEO Review — deepagents-video-maker (follow-up)

- **Date:** 2026-05-14 01:05:00 UTC
- **Branch:** `claude/gracious-gates-1U7jZ`
- **HEAD:** `9380e5d` (feat(skill): implement Stage 1 plan for video-maker skill with detailed task breakdown and acceptance criteria)
- **Reviewer skill:** `gstack/plan-ceo-review` (https://github.com/garrytan/gstack.git) — not installed locally on this host, so adapted for **non-interactive written delivery** identically to the prior review at `cc_ceo_reviews/20260509T012631Z-plan-ceo-review.md`. CEO posture, 11-section framework, prime directives, and required outputs are preserved. AskUserQuestion ceremonies are replaced with explicit written recommendations.
- **Mode selected:** EXPAND SCOPE (cautiously). The project has *materially advanced* since the prior review: it is no longer "M1 hardening + assets/assembly deferred." All four milestones (`source_intake → script → build_scenes → render_package`) are now operational, golden playable demo can produce an MP4, and the script→build_scenes hand-off correctly gates on explicit user approval. The right CEO move now is to recognize the architectural bet held under load, then push the *quality* axis (publish-readiness, observability, schema versioning) rather than add more milestones.
- **Posture:** Rigorous reviewer. Zero silent failures. Every error has a name. Permission #9 invoked where I see a fundamentally better path. The prior review's TODOs are tracked: which closed, which carry, which got worse.

---

## 0. Pre-Review System Audit

### Repository state

- Working tree clean. Branch `claude/gracious-gates-1U7jZ`, HEAD `9380e5d`.
- **47 commits since prior review HEAD `fbc0074`** — heavy activity. Themes (in order of LOC delta): v2 skill carved out, build/render milestone implemented, Remotion subagent added, source-intake replaced research, web-UI middleware projection, golden-playable smoke, FFmpeg in CI, websearch surfaced as a visible step, better-harness scriptwriter-only optimization, VSCode launch/tasks, Stage-1 skill task breakdown.
- **18 Python source files / 2,872 LOC** (was 15 / ~1,700 LOC). +69% LOC, the bulk in `build_render_flow.py` (514) and `source_flow.py` (293) — both *net-new* milestone implementations, not bloat.
- **33 test files** under `tests/` (was 15). The 19 under `tests/deepagents_video_maker/` are the production gate. **84 tests pass** when ffmpeg is missing (test_golden_demo_smoke is the one excluded; it requires ffmpeg on PATH). With ffmpeg present, CI is green — the earlier commit `93bf38a` added ffmpeg to CI explicitly.
- `tests/evals/` exists (`scorecard`, `train`, `holdout` subtrees). Per CLAUDE.md, broader eval harness is intentionally NOT package-script-wired right now — better-harness is scriptwriter-only.

### Workflow has been renamed and re-scoped

The prior review's "research → script" pipeline is gone. The current canonical workflow is:

```text
Setup → Source Intake → Script → user script review → Build Scenes → Render & Package
```

with optional Generate Audio (deferred until a native audio milestone lands). `skills/video-maker-v2/SKILL.md` is the canonical skill; `.deepagents/skills/video-maker-v2-*` are runtime wrappers; legacy `skills/video-maker/` is no longer the active surface. README, AGENTS.md, and CLAUDE.md all agree on this. **The aspirational-vs-operational gap I flagged last review is closed.**

### Status of prior-review TODOs (carried)

| # | Title | Last review | Status today |
|---|---|---|---|
| 1 | PyYAML migration for `state_store` | P1 | ❌ **Open.** PyYAML is in `dependencies` but `state_store.py` still hand-rolls YAML. Risk has *grown* — `ratify` payload is now JSON-serialized into a single quoted YAML scalar (`state_store.py:30`), which is brittle. |
| 2 | Surface Tavily absence to producer | P1 | ✅ **Partial / different shape.** `vm_websearch` is now a distinct typed tool so Tavily absence surfaces as a tool error rather than silent low-quality research, but `agent.build_researcher_extra_tools` is gone (the researcher subagent itself was removed). Net better. |
| 3 | Generalize `block_if_tool_call_dropout` to all milestones | P1 | ❌ **Open.** `controller.py:25-28` only auto-infers `source_intake`'s expected artifact. Script, build_scenes, render_package have no symmetric coverage. |
| 4 | Output-dir collision guard in `init_video_session` | P1 | ❌ **Open.** `session.py:33` still does `mkdir(parents=True, exist_ok=True)` with no collision check. |
| 5 | Reconcile SKILL.md aspirational scope | P1 | ✅ **Closed.** v2 skill describes a workflow that matches what is wired. |
| 6 | Consolidate `_to_virtual_path` | P2 | ⚠️ **Partial.** Down from 3× to 2× — `build_render_flow.py:20` imports from `script_flow`, so script_flow is now the single source of truth (good). One stray copy may remain in `scripts/`. Pull both into a single helper. |
| 7 | Slim typed-tool kwargs surface | P2 | ❌ **Worse.** The 13-kwarg fan-out is now **14 kwargs** across **5 typed tools** (`vm_init_video_session`, `vm_ratify_source_intake`, `vm_build_scriptwriter_task`, `vm_ratify_script`, `vm_build_remotion_task`). 70 redundant call-site parameters total. |
| 8 | Delete dead Windows-only code | P2 | ⚠️ **Need to verify** — the `82cf0c5` commit "remove hardcoded Windows path" suggests partial cleanup; `93bf38a` covers Windows path normalization. Confirm `execute_pwsh`, `project_glob`, `patch_deepagents_path_validation` are gone. |
| 9 | `state_schema_version` field | P2 | ❌ **Open.** `save_state_yaml` (`state_store.py:79`) still writes no version field. Will hurt when audio milestone lands. |
| 10 | Structured logging | P2 | ⚠️ **Token only.** One `logging.getLogger(__name__).exception(...)` call exists at `langchain_tools.py:454-455`. No configured logger, no module loggers across the package, no INFO-level events for milestone transitions. |
| 11 | Pin upper bounds on `deepagents`, `langchain*` | P2 | ❌ **Open.** `pyproject.toml:7-11` still uses lower bounds only. |
| 12 | Drop unused `tavily-python` dep | P3 | ❌ **Open.** Still listed alongside `langchain-tavily`. |
| 13 | E2E producer protocol stub-model test | P2 | ✅ **Closed (by proxy).** `test_golden_demo_smoke.py` and `run_golden_playable_smoke.py` cover the full pipeline deterministically (the smoke is what `pnpm golden:playable` runs). Promote to a stub-model variant for true protocol coverage. |
| 14 | Adversarial topic round-trip tests | P2 | ❌ **Open.** No tests for embedded quotes / multi-line / Chinese-with-quotes in `goal.yaml`. |
| 15 | Promote manifest-schema.md to `docs/` | P2 | ⚠️ **Need to verify** — `docs/golden-demo.md` exists and is canonical; manifest-schema may live under `skills/video-maker-v2/references/`. The schema is no longer the single load-bearing contract — `script-contract.json` is now per-run alongside `script.md`. |
| 17 | CHANGELOG.md + v0.1.0 tag | P3 | ❌ **Open.** No `CHANGELOG.md`. `pyproject.toml` still `version = "0.1.0"`. |
| 18 | Path-confinement on `local_file` / `excalidraw_file` | P3 | ❌ **Open.** No new guard. |

**Closed:** 5/12 (TODO #2 partial, #5, #6 partial, #13 partial). **Open or regressed:** the rest. The 14-kwarg fan-out is the only item that got materially worse.

### What is new and unflagged

- `build_render_flow.py` (514 LOC) is the new largest source file. It owns subprocess execution (pnpm/ffmpeg/ffprobe), Remotion render orchestration, packaging, and publish-readiness reporting. **Single biggest new surface; biggest new risk locus.**
- `middleware.py` (115 LOC) projects per-tool video-maker state into LangGraph state for the web UI. Wraps every `vm_*` tool call.
- `ui_state.py` (140 LOC) builds the UI projection. Reads from disk; runs synchronously on every tool call.
- `vm_websearch` (`langchain_tools.py:107-119`) is a distinct visible step before `vm_ratify_source_intake`. Good UX call.
- Per-run **script-contract.json** is now written by `start_script_milestone` (`script_flow.py:36-38`), then guarded against rewrite by `build_scriptwriter_task_description`. This is a *real* protocol commit — the contract is the input, the script is the output, ratify checks one against the other.
- Stage-1 task breakdown and acceptance criteria added at HEAD (commit `9380e5d`). Not yet read; flagged for Section 11.

### Recently touched files (signal: where attention is going)

`langchain_tools.py`, `build_render_flow.py`, `script_flow.py`, `source_flow.py`, `ratify.py`, `middleware.py`, `ui_state.py`, skill files, CI config, golden-demo doc, package.json scripts. The team is operationalizing the full pipeline — **scope is expanding deliberately**.

---

## Step 0: Premise Challenge + Mode Selection

### 0A. Premise Challenge — is this the right problem?

> "DeepAgents-native Producer with skills-based progressive disclosure to drive an end-to-end short-form video pipeline (source intake → script → user-review → build scenes → render package), validated by deterministic ratify gates."

Three premises worth challenging directly:

1. **"Source Intake replaces Research."** This is a *correct* premise inversion. The prior `research → script` design framed the producer as a researcher first. The new framing is: **the producer is a composition orchestrator; the source manifest is an index, not a knowledge document.** Source Intake is indexing only; extraction happens inside Scriptwriter Pass 0 (`SKILL.md`). This is sharper and lower-risk — there is no "research artifact" to hallucinate facts into. ✅ Keep.

2. **"Subprocess Remotion render inside the typed tool surface."** `vm_render_remotion_project` shells out to `pnpm tsc` + Remotion render + Remotion still (`build_render_flow.py:277-285`, `442+`). 30-minute timeout. Output is captured but not streamed. **The cost:** the producer model sees a single end-of-run payload — success or a giant stderr blob — and has no incremental signal. If the render takes 8 minutes and then fails on the still frame, the user has nothing actionable until the timeout. **Recommendation:** keep subprocess execution, but stream stderr to a `logs/render-run-N.log` file *and* return the last 50 lines on failure. The typed-tool result should also include the command, cwd, exit code, and log path, so the producer (and the web UI) can render a "render failed at step X — last 50 lines" panel without re-reading the entire stderr capture.

3. **"Web-UI middleware swallows all UI-projection exceptions."** `middleware.py:40-41` and `middleware.py:51-52` both `except Exception: return result`. The principle (UI projection must never break the tool call) is *right*, but the implementation is silent. When the projection fails — even due to a real bug — the chat shows the same tool result it always would, and nobody sees the broken UI. **Same violation as the original Tavily-silent-import.** Easy fix: `logging.getLogger(__name__).exception(...)` on the `except`, *and* surface a tiny `video_maker.projection_error` field in the message so the web-UI can show a debug banner. The same pattern already exists at `langchain_tools.py:453-455`; just mirror it here.

**Verdict on premises:** problem framing is sharper than before. The two new failure modes (silent render log loss; silent UI projection failure) repeat the old "every error has a name" violation — both are easy to fix.

### 0B. Existing Code Leverage — what already partially solves this?

| Sub-problem | Existing code | Reused? |
|---|---|---|
| Milestone state machine | `models.MilestoneState`, `session.DEFAULT_MILESTONES` | ✅ |
| Artifact ratify pattern | `ratify.ratify_script` / `ratify_source_manifest` / `ratify_build_scenes` / `ratify_render_package` | ✅ |
| Run-N directory convention | `session.create_milestone_run` | ✅ |
| Tool-call dropout detection | `controller.block_if_tool_call_dropout` | ✅ source_intake only — same gap as before, now over a wider pipeline |
| Subagent prompt + skill loading | `prompts.load_subagent_prompt`, `agent.build_subagents` | ✅ scriptwriter + remotion-builder |
| Subprocess command runner | `build_render_flow._run_command` | ✅ render and ffprobe |
| Goal/state YAML persistence | `state_store` hand-rolled | ✅ but still reinvented; risk grew |
| Goal flowing through tool calls | `_goal_from_inputs_or_goal_file` | ✅ but kwargs explosion is worse |
| UI state projection | `ui_state.build_video_maker_ui_state` + `middleware.VideoMakerUiStateMiddleware` | ✅ — net-new, mostly clean |
| Path virtualization | `script_flow._to_virtual_path` (now reused from `build_render_flow`) | ✅ down from 3× to 2× |

### 0C. Dream State Mapping

```text
  CURRENT STATE                  THIS BRANCH                12-MONTH IDEAL
  ─────────────                  ───────────                ──────────────
  All 4 milestones               Stage-1 skill              All 4 milestones +
  operational; golden            task breakdown             optional Generate Audio,
  playable smoke renders         (9380e5d).                 plus per-scene HITL,
  an MP4 end-to-end.             vm_websearch as a          + reviewer/editor
                                 distinct visible step.     subagents wired.
  Script-approval gate           Better-harness             Layer-2 quality:
  enforces user review.          scriptwriter-only          publish-readiness flow
                                 optimization.              becomes a real review
  Web-UI projects state          ratify serialization       agent, not a checklist.
  via middleware                 polished.                  Schema-versioned state.
  (live timeline).                                          Structured logs +
                                                            session inspector UI.
  84 v2 tests + golden                                      Failure-mode docs +
  smoke green.                                              runbooks per milestone.
```

The branch delivers **executable end-to-end** vs the prior branch's **documentation-and-tests hardening**. Materially: the project crossed from "M1 working" to "all M0-M4 working." The next dream-state delta is **quality, not pipeline scope** — publish-readiness, structured logging, schema versioning.

### 0C-bis. Implementation Alternatives (next move)

```text
APPROACH A: Quality push — make what exists boring-reliable
  Summary: Close the open prior-review TODOs (PyYAML, schema version, kwargs
           slim, structured logging, dropout for all milestones, render log
           streaming, middleware logging) before adding any new pipeline scope.
           Add adversarial-topic and dropout symmetry tests.
  Effort:  S-M (human ~3-5 days; with CC ~1-2 days)
  Risk:    Low. Pure hardening + recoverability.
  Pros:    - Removes the scar tissue debt that was flagged last review and grew.
           - Render-log streaming converts the worst current UX failure
             (silent render timeout) into actionable failure.
           - PyYAML migration unblocks the adversarial-topic tests that
             will otherwise fail and stay un-merged.
           - Cheapest path to a defensible v0.1 tag.
  Cons:    - No new user-visible features.
  Reuses:  Everything currently in tree.

APPROACH B: Generate Audio milestone (the next operational frontier)
  Summary: Implement TTS + Whisper alignment as the optional audio milestone
           described in SKILL.md. Adds vm_start_audio, vm_build_tts_task,
           vm_ratify_audio. Consumed by Remotion Builder via audio-contract.md.
  Effort:  M-L (human ~1.5-2 weeks; with CC ~4-7 days)
  Risk:    Med — TTS provider choice (whichever) becomes a dep; Whisper-based
           alignment adds an optional extra. New subprocess surface for ffmpeg
           muxing. New ratify gates: per-scene audio file present, duration
           within scene_duration_seconds tolerance, no truncation.
  Pros:    - Closes the gap between "renderable video" and "narrated video."
           - audio-contract.md is already drafted — re-use, don't redesign.
           - Real product value: enables longer-form videos and accessibility.
  Cons:    - Hardest single milestone to ratify correctly (timing tolerance,
             SSML edge cases, voice fallback).
           - Provider lock-in considerations.
  Reuses:  scriptwriter Pass-0 output, subprocess runner, ratify pattern.

APPROACH C: Publish-readiness becomes a real review gate (Layer 2)
  Summary: Today `vm_build_publish_readiness_report` writes a checklist that
           the user fills in. Promote it to a reviewer-subagent loop:
           reviewer reads final/video.mp4 metadata + script.md + source-manifest
           and writes a structured review with per-dimension scores. Producer
           shows it to the user, who can request a re-render or accept.
  Effort:  M (human ~1 week; with CC ~3-4 days)
  Risk:    Med — model needs to "review" a video it can't watch; will rely on
           script + metadata. Real signal possible only with sampled frames or
           a Whisper transcript-of-rendered-output cross-check.
  Pros:    - First Layer-2 quality milestone; lays groundwork for GAN Evaluator.
           - Closes the "render succeeded vs publishable" gap (now an open
             item in the README publish-readiness rules).
  Cons:    - Without video-frame inspection, reviewer is text-bound and may
             over-trust the script.
           - Sets a precedent for evaluator subagents that will need careful
             prompt design.
  Reuses:  Existing ratify-payload contract; subagent skill loading; goal.yaml.

RECOMMENDATION: A first, then B. Defer C to Q3+.

  WHY: Approach A is small, defensible, and unlocks future work. Approach B
  is the next *missing* milestone that gives a clearly better product (an
  actual narrated video instead of a silent one). Approach C is high-ambition
  Layer-2 that, without frame inspection, risks producing reviews that look
  authoritative but are not. Sequence A → B → C protects the architectural
  bet (controller-only) by widening dropout coverage and structured logging
  BEFORE the audio milestone adds a new tool-call dropout surface.
```

### 0D. Mode-Specific Analysis (EXPAND SCOPE — cautiously)

**Complexity check:** 18 source files / 2,872 LOC + ~250 LOC web-UI. Largest: `build_render_flow.py` (514) and `langchain_tools.py` (554). Both are dispatch hubs and that is appropriate — each function in `langchain_tools.py` is a thin wrapper. `build_render_flow.py` is hairier; it owns subprocess orchestration *and* publish-readiness *and* ratify hooks. **Split candidate:** extract `render_runner.py` (subprocess execution + log capture) and `publish_readiness.py` from `build_render_flow.py`. ~250-LOC reduction in the biggest file.

**Minimum set that achieves the stated goal:** the 17 typed tools + 2 subagents + 4 ratify gates + script-approval gate. That is exactly what is wired. No further reduction is honest.

### 0E. NOT in Scope (this review respects it)

- Generate Audio milestone — explicitly deferred per SKILL.md; recommended for Approach B (next).
- Reviewer / Editor / scene-batch-generator / scene-patch-generator subagents — prompts exist on disk; not wired into `create_video_maker_agent`. Deferred to Approach C.
- GAN Evaluator contract loop — designed in legacy v1 SKILL.md, *not present* in v2 skill. Implicitly dropped (correct call IMO).
- Reflexion lessons read/write — silent in code; no longer referenced from v2 skill. Implicit drop (correct).
- Production deploy — dev-only by design.

---

## Section 1: Architecture Review

### Component dependency graph (current)

```text
                ┌────────────────────────────────────────────────┐
                │      User / Web UI (LangGraph dev server)      │
                │      (web-ui/agent/agent.py: agent factory)    │
                └──────────────────────┬─────────────────────────┘
                                       │ invokes via thread_id
                                       ▼
        ┌─────────────────────────────────────────────────────────┐
        │   create_video_maker_agent (agent.py:43-88)             │
        │   model: anthropic|deepseek|zhipuai                     │
        │   system_prompt: prompts/producer.md                    │
        │   tools: build_langchain_tools() (17 typed tools)       │
        │   subagents: ["scriptwriter", "remotion-builder"]       │
        │   middleware: VideoMakerUiStateMiddleware               │
        │   backend: FilesystemBackend(virtual_mode=True)         │
        └────────────┬──────────────────────┬─────────────────────┘
                     │                      │
            ┌────────┴───────┐      ┌───────┴────────┐
            ▼                ▼      ▼                ▼
        typed tools     middleware  producer.md   subagent task()
        (source_flow.py, wraps      hard-rules     scriptwriter
         script_flow.py,  every     controller     (.deepagents/
         build_render_   vm_* call  protocol       skills/video-
         flow.py,        & projects                 maker-v2-
         ratify.py,      ui_state                   scriptwriter)
         session.py,                               remotion-builder
         state_store.                              (.deepagents/
         py,                                        skills/video-
         controller.py)                             maker-v2-
                                                    remotion-builder)
                     │                                       │
                     └───────────┬───────────────────────────┘
                                 ▼
        ┌──────────────────────────────────────────────────────┐
        │  Filesystem (output/<session>/)                      │
        │  goal.yaml, state.yaml,                              │
        │  artifacts/source/source-manifest.md,                │
        │  artifacts/script/run-N/{script-contract.json,       │
        │                          script.md},                 │
        │  artifacts/build_scenes/run-N/,                      │
        │  remotion-project/{package.json,src/index.ts,...},   │
        │  final/{video.mp4,thumbnail.jpg,                     │
        │         publish-readiness.md},                       │
        │  ratify/{<milestone>-run-N.json}                     │
        └──────────────────────────────────────────────────────┘

External processes (invoked via subprocess from build_render_flow):
  - pnpm install / pnpm tsc (in remotion-project/)
  - Remotion render (composition_id → out/video.mp4)
  - Remotion still (→ out/thumbnail.jpg)
  - ffprobe (final video duration validation)
  - ffmpeg (golden playable smoke renderer)
```

### Architecture findings

**A1 — Render subprocess surface is the new largest-blast-radius zone.**
`_run_command` (build_render_flow.py:277) takes a `command: list[str]` (good — no shell=True) and a `cwd`. 30-minute timeout. Returns `(returncode, stdout, stderr)`. **Issues:**
- Output is captured in memory in one shot. A 30-minute Remotion render with verbose logs can produce 100+ MB of stderr — held in RAM and serialized into the tool result. Stream to `logs/<milestone>-run-N.log` and return the last N lines.
- The 1800s timeout is hardcoded. For long-form (5-10min) renders this is tight. Make it `goal.duration`-aware, or accept it as a parameter.
- No cancellation path. If the producer/UI wants to abort mid-render, there's no hook.

**A2 — Web-UI middleware is a new silent-failure surface.**
`middleware.py` wraps every `vm_*` tool call. The wrap is `except Exception: return result`, twice (sync and async). UI projection failures are invisible. Same fix as `langchain_tools.py:454`: log + thread a `projection_error` field into the response so the UI can debug.

**A3 — Tool-call dropout is still only auto-wired for source_intake.**
`controller.block_if_tool_call_dropout` (`controller.py:25-28`) infers the expected artifact only for `source_intake`. For `script`, `build_scenes`, `render_package` the caller must pass `expected_artifact` explicitly — but no code in `langchain_tools.py` or the producer prompt does so. **Same gap as prior review #3.** Generalize the artifact resolver: per milestone, lookup the canonical artifact path (script.md for current run; remotion-project/package.json; final/video.mp4).

**A4 — `_to_virtual_path` reduced from 3× to 2×.**
`build_render_flow.py:20` imports from `script_flow`. ✅ Net better. Still two implementations (script_flow + scripts/). Move to `serialization.py` or `paths.py`.

**A5 — 14-kwarg fan-out across 5 typed tools.**
`vm_init_video_session`, `vm_ratify_source_intake`, `vm_build_scriptwriter_task`, `vm_ratify_script`, `vm_build_remotion_task` all accept 14 identical optional goal-shaped kwargs. The bodies all funnel through `_goal_from_inputs_or_goal_file`. **This is worse than before** (was 13×4=52, now 14×5=70). Since `goal.yaml` is always written at `vm_init_video_session` time, after init *every* later call can read it from disk. **Recommendation:** keep `prompt`/`topic`/... only on `vm_init_video_session`. Strip from all post-init tools. The producer is then forced to use `vm_init_video_session` once at the start, and every later call has `output_dir + (run_number)` only. The kwargs explosion is invitation for the LLM to drift; remove the invitation.

**A6 — Session collision still unprotected.**
`init_video_session` (`session.py:33`) `mkdir(exist_ok=True)`. Same risk as before. Add a uniqueness guard.

**A7 — `controller.can_enter_milestone` only covers one transition.**
`controller.py:54-60`: only checks the `script` transition. `build_scenes` and `render_package` transitions are guarded only inside the `start_*_milestone` helpers (raising `RuntimeError`). Hoist the gate to `can_enter_milestone` so the producer can ask permission without trying.

**A8 — Rollback posture (unchanged, still solid).**
`output/<session>/` is git-ignored, no DB, no migrations. Reversibility 5/5 for sessions. Producer-side rollback unchanged (`workflow_status = blocked`). The only new wrinkle is that a mid-render abort leaves `remotion-project/node_modules` and `out/` orphaned — costs disk, doesn't corrupt anything.

### Architecture diagrams produced
1. ✅ Component dependency graph (above).
2. Missing — but high-leverage: render-pipeline sequence diagram (producer → vm_start_build_scenes → vm_build_remotion_task → task(remotion-builder) → vm_ratify_build_scenes → vm_start_render_package → vm_render_remotion_project → vm_package_render_output → vm_ratify_render_package). Add to `docs/design/` when next milestone lands.

---

## Section 2: Error & Rescue Map

| METHOD/CODEPATH | WHAT CAN GO WRONG | EXCEPTION CLASS | RESCUED? | RESCUE ACTION | USER SEES |
|---|---|---|---|---|---|
| `agent.create_video_maker_agent` | DeepAgents not installed | `ImportError → RuntimeError` | Y | re-raise with clear message | "DeepAgents runtime is required..." |
| `middleware._attach_ui_state` | ui_state projection raises | bare `Exception` | **Y but SILENT — GAP** | `return result` | nothing; UI shows stale projection forever |
| `middleware.wrap_tool_call` outer | same | bare `Exception` | **Y but SILENT — GAP** | `return result` | same |
| `langchain_tools._with_ui_state` | projection raises | bare `Exception` | Y + logged | `logging.exception(...)` | log entry only — better than middleware |
| `session.init_video_session` | output_dir already exists (collision) | none | N | `mkdir(exist_ok=True)` silently | **silent data loss** (goal/state overwrite) |
| `state_store.load_goal_yaml` | YAML file with quote/backslash in topic that hand-rolled `_unquote` mishandles | partial | partial | `ValueError` only if topic missing entirely | **silent corruption** path exists |
| `state_store.load_state_yaml` | malformed file from older writer | `ValueError` from `MilestoneStatus(value)` or `int(value)` | N | uncaught | crash |
| `state_store.load_state_yaml` | ratify scalar with embedded double-quote/backslash | `json.JSONDecodeError` | Y | `current.ratify = {}` (state_store.py:158-159) | **silent data loss** — ratify history disappears |
| `start_script_milestone` | called before source_intake completed | `RuntimeError` | Y | raise | "cannot start script milestone: source_intake status=..." ✅ has "Fix:" hint |
| `start_build_scenes_milestone` | called before script completed | `RuntimeError` | Y | raise | "cannot start build_scenes: script status=..." ✅ |
| `start_build_scenes_milestone` | called without `script_approved=True` | `RuntimeError` | Y | raise | "cannot start build_scenes without script_approved=True" ✅ |
| `vm_start_script` / `vm_start_build_scenes` / `vm_start_render_package` | upstream not complete | RuntimeError caught → structured error | Y | `{"error": str(exc), ...}` | structured error result ✅ |
| `render_remotion_project` | `pnpm install` fails | `RuntimeError` | Y | raise → caller wraps to structured error | last 50 lines of stderr? **NO — entire stdout/stderr captured but in memory only**; user sees one giant string ← **degraded UX** |
| `render_remotion_project` | pnpm/Remotion not installed | `FileNotFoundError` from subprocess.run | N | uncaught | crash on first call ← **gap** |
| `render_remotion_project` | render exceeds 1800s | `subprocess.TimeoutExpired` | Y | (line 459) | "ffprobe timed out / render timed out" ✅ but only after 30 min |
| `ratify_render_package` | ffprobe missing | none — `shutil.which` check elsewhere | partial | depends on probe_runner | crash if not guarded |
| `controller.block_if_tool_call_dropout` | only auto-resolves artifact for `source_intake` | none | N | returns False silently | dropout undetected on script/build_scenes/render_package ← **GAP** |
| `build_publish_readiness_report` | final video missing | `RuntimeError` | Y | raise → caller wraps | clear error with "Fix:" hint ✅ |
| `_goal_from_inputs` | non-numeric `quality_threshold` | `ValueError` from `int()` | N | uncaught | crash → tool error message |
| `_goal_from_inputs_or_goal_file` | output_dir missing goal.yaml AND no inputs | `FileNotFoundError` from `load_goal_yaml` | N | uncaught | crash → tool error |
| `vm_websearch` | Tavily missing | depends on `run_websearch_and_cache` (not read) | likely partial | unknown | depends |
| `vm_render_remotion_project` | pnpm command line injection via `composition_id` | composition_id is splatted into argv; if not quoted properly, shell metacharacters could matter | N | **needs verification** — see Section 3 |

### Critical gaps (RESCUED=N AND silent, in priority order)

1. **`middleware` silent UI-projection failure.** `middleware.py:40-41, 51-52`. Mirror `langchain_tools._with_ui_state` logging pattern. Surface a `projection_error` field.
2. **`init_video_session` overwrite without warning.** `session.py:33`. Add existence check; either bail with structured error or auto-suffix `-2`.
3. **Tool-call dropout uncovered for script / build_scenes / render_package.** `controller.py`. Generalize the artifact resolver.
4. **Render subprocess output is in-memory only.** `build_render_flow._run_command`. Stream to `logs/`. Return last 50 lines and the log path on failure.
5. **Hand-rolled YAML still corrupts ratify scalar on adversarial topics.** `state_store.py:30, 152-159`. PyYAML migration is the right answer; the project already depends on it.
6. **`pnpm`/`ffprobe` missing → `FileNotFoundError` not converted to a clean error.** `build_render_flow.render_remotion_project`. `shutil.which` precheck + named error.

---

## Section 3: Security & Threat Model

| Threat | Likelihood | Impact | Mitigated? |
|---|---|---|---|
| Path traversal via `local_file` / `excalidraw_file` | Low (single-user tool) | Med | None added since prior review |
| Prompt injection via `local_file` content | Med (any document fed in) | Med-High | None — same as before |
| LLM base URL hijack via `ANTHROPIC_BASE_URL` | Low | High | None — document in README |
| Secret leakage via `.env` | Low | High | ✅ `.gitignore:14-15` covers `.env` and `.env.local`. (Verified.) |
| Web-UI bound to public interface | Low | High | LangGraph dev binds 127.0.0.1 by default |
| **NEW — Subprocess argv injection via `composition_id`** | Med — user/producer-supplied string flows to `pnpm remotion render <id>` | High | Partial. `_run_command` uses argv list (no shell=True), so shell metacharacters are inert — but Remotion's CLI may treat unexpected `--foo` prefixes as flags. Validate `composition_id` matches `^[A-Za-z][A-Za-z0-9_-]*$` before splatting. |
| **NEW — `pnpm install` runs arbitrary postinstall scripts** | Low | High | None. `pnpm install` in the per-session remotion-project will execute whatever `postinstall` hooks the generated `package.json` declares. The remotion-builder subagent writes `package.json`; if it's compromised (prompt injection from source content), arbitrary code runs locally. Mitigation: `--ignore-scripts` for install or pin Remotion's known-good lockfile pattern. |
| **NEW — Tavily websearch caches arbitrary URLs to disk** | Low | Low-Med | Cached results land in output dir; size unbounded. Add a size cap. |

### Recommendations

- **S1.** Validate `composition_id` (`vm_render_remotion_project`) against a strict regex before passing to subprocess.
- **S2.** Run `pnpm install --ignore-scripts` in `build_render_flow`. Document the trade-off in `docs/runbooks/`.
- **S3.** Bound websearch cache size (e.g., 5MB per run).
- **S4.** Carry forward S1-S4 from prior review (path confinement on `local_file`/`excalidraw_file`, prompt-injection note in README, base-URL warning, dead pwsh code purge).

---

## Section 4: Data Flow & Interaction Edge Cases

### Data flow: build → render

```text
  user "approve" ──▶ vm_start_build_scenes(script_approved=True)
       │                                          │
       │ [script not completed?]                  │
       │ → RuntimeError ← rescued → structured    │
       │   error in result                        │
       ▼                                          ▼
  vm_build_remotion_task ──▶ task(remotion-builder) ──▶ remotion-project/**
       │                              │
       │                       [subagent writes broken package.json?]
       │                       → only caught at vm_ratify_build_scenes ← OK
       ▼                              ▼
  vm_ratify_build_scenes ──▶ ratify_build_scenes
       │                              │
       │                       [missing package.json or src/index.ts?]
       │                       → ratify fails, retry/block ← OK
       ▼
  vm_start_render_package
       │
       ▼
  vm_render_remotion_project ──▶ subprocess (pnpm tsc, render, still)
       │                              │
       │                       [pnpm not on PATH?] ← GAP (uncaught FileNotFound)
       │                       [render exceeds 30 min?] ← TimeoutExpired
       │                       [stderr 100 MB?] ← held in memory
       │                       [postinstall hook?] ← arbitrary code ← GAP
       ▼
  vm_package_render_output ──▶ shutil.copy2 → final/video.mp4
       │
       ▼
  vm_ratify_render_package ──▶ ratify_render_package
       │                              │
       │                       [ffprobe missing?] ← GAP
       │                       [video duration outside band?] ← rejected ✅
       ▼
  workflow_status = COMPLETED
```

### Interaction edge cases (new ones)

| Interaction | Edge case | Handled? | How? |
|---|---|---|---|
| User rejects script, asks for rewrite | producer starts run-2 | Y | retry_count + new run_dir |
| User edits script.md manually then re-runs ratify | Y | ratify reads from disk | OK |
| User clicks "approve" twice in web-UI | `vm_start_build_scenes` called twice | Partial | second call lands on already-started build_scenes; status check is `script.status == COMPLETED` ✓; but creates run-2 silently — should noop with a warning |
| Render fails halfway, user retries | `vm_start_render_package` called again | Partial | creates run-2; stale `remotion-project/node_modules` reused (good); doesn't clear `out/` from previous attempt |
| ffmpeg-only host without Remotion | golden playable smoke works; full render fails | Y | clear "ffmpeg required" message ✓ (verified in test failure earlier) |
| 16:9 vs 9:16 aspect mismatch between goal and remotion composition | Producer relies on subagent to honor goal | N | no automated check — ratify_build_scenes doesn't enforce composition dimensions; ratify_render_package only checks duration |

### Recommendations
- Add "approve clicked twice" test; make `vm_start_build_scenes` idempotent when current run is already in progress.
- Add composition-dimension sanity check to `ratify_build_scenes` (parse package.json's compositions or read Remotion's metadata if cheap).

---

## Section 5: Code Quality Review

**Strengths**
- Clean package boundary intact. `__init__.py` re-exports stable surface.
- Per-milestone helpers (`start_X_milestone`, `build_X_task_description`, `ratify_and_update_X`) follow a consistent shape. Pleasant.
- `RatifyCheck`/`RatifyResult` continues to do the right thing. Each new milestone (`ratify_build_scenes`, `ratify_render_package`, `ratify_source_manifest`) follows the pattern.
- Error messages frequently include "Fix:" hints (`source_flow`, `script_flow`, `build_render_flow`, `start_build_scenes_milestone`). Real DX improvement. Standardize this across all tool errors.

**Issues**

- **Q1. 14-kwarg fan-out across 5 tools.** Worsened. See A5.
- **Q2. `build_render_flow.py` is 514 LOC and does three jobs.** Render subprocess execution, packaging, publish-readiness. Split into `render_runner.py` + `publish_readiness.py` + keep the milestone helpers in `build_render_flow.py`. Reduces the biggest file by ~50%.
- **Q3. `langchain_tools.py` _with_ui_state vs middleware._attach_ui_state duplication.** Both project ui_state. The tool-level one runs first (returns payload with `video_maker` key), then the middleware projects again from disk. Pick one — middleware is the more correct location (single concern) and the tool-level helper can be deleted.
- **Q4. Hand-rolled YAML still in place.** ~120 LOC of risk. PyYAML is in deps. The prior-review fix is now *more* valuable because ratify payloads embed JSON inside YAML strings.
- **Q5. State schema has no `version` field.** Adding audio milestone will require migration; today there is no hook.
- **Q6. Producer prompt language.** Need to re-verify — Chinese mixed with English in the prompt is fine if the team's working language is Chinese, but pick a convention and stick.
- **Q7. Dead `tavily-python` dep.** Still in `pyproject.toml`. Drop.
- **Q8. `_to_virtual_path` still in two places.** Move to a single helper.
- **Q9. `_run_command` 1800s hardcoded.** Make it goal-aware or parametric.

---

## Section 6: Test Review

### Coverage assessment

19 v2 test files under `tests/deepagents_video_maker/` + 11 evals under `tests/evals/`. **84 of 85 tests pass** when ffmpeg is absent; with ffmpeg installed (as CI is configured), the golden playable smoke completes and the suite is 85/85.

**Existing tests that earn their keep**
- `test_artifact_gates.py` — milestone-by-milestone ratify negative/positive cases.
- `test_golden_demo_smoke.py` — end-to-end deterministic golden demo, requires ffmpeg.
- `test_tool_call_dropout_detection.py` — exists for source_intake.
- `test_build_render_flow.py` — exists and covers the new flow.
- `test_ui_state.py` — new, covers projection.
- `test_windows_path_normalization.py` — net-new, addresses a real production failure from May 9.
- `test_script_flow.py`, `test_session.py`, `test_state_store.py` — round-trip.

### Gaps

- **T1. Tool-call dropout symmetry across milestones.** `test_tool_call_dropout_detection.py` covers source_intake; add cases for script, build_scenes, render_package. Will go red until the controller is generalized.
- **T2. Adversarial goal.yaml round-trip.** Chinese topics with embedded quotes / backslashes / multi-line. Will demonstrate why PyYAML matters.
- **T3. Session-init collision.** Two `init_video_session` calls with same timestamp; assert no silent overwrite.
- **T4. Render subprocess failure modes.** With `_run_command` mocked: pnpm missing → FileNotFoundError → clean error; timeout → clean error with log path; nonzero exit → log tail returned.
- **T5. Middleware UI projection error path.** Inject a projection that raises; assert tool result unchanged AND that a `projection_error` field is present AND that the log captured the exception.
- **T6. `script_approved=False` after script ratify pass.** Already in test_build_render_flow? — verify; if not, add.
- **T7. `vm_start_build_scenes` idempotency.** Calling twice in a row when build_scenes is already in progress.
- **T8. Composition-id injection.** Try `vm_render_remotion_project(composition_id="--help")` and assert validation rejects.

### Flakiness risk
None visible. `test_golden_demo_smoke.py` depends on `ffmpeg` availability, which is environment-dependent but deterministic.

### Test ambition checks (per CEO mode)
- "Ship at 2am Friday" test: golden smoke is the right shape (✅), with composition-id validation (T8) layered in.
- "Hostile QA" test: adversarial topic round-trip (T2), CRLF script.md, manifest with `target_scene_count={}`, package.json without `name`.
- "Chaos test": inject a `<sop_invocation>` text into the LLM stub's response and assert `block_if_tool_call_dropout` fires on each milestone (T1 superset).

---

## Section 7: Performance Review

LLM latency dominates; render time dominates the rest.

- **P1.** Render is a 30-min hard cap. For longer videos this is tight. Make timeout `goal.duration`-aware.
- **P2.** Subprocess output buffered in memory. For 8-minute renders with verbose logs, this is hundreds of MB. Stream.
- **P3.** `pnpm install` per session = heavy. Add an opt-in workspace-cache mode (`--frozen-lockfile`, shared `node_modules` via pnpm's content-addressable store).
- **P4.** `ui_state.build_video_maker_ui_state` reads from disk on every tool call (middleware wraps every `vm_*`). Synchronous filesystem reads on every tool call. With small per-session state this is fine; if `state.yaml` ever grows beyond 50 KB or ratify history accumulates many runs, add a memoization layer keyed on `output_dir` mtime.
- **P5.** N+1, indexes, caching: not applicable.

**No blocking issues — but P1 and P2 ride alongside the user UX (see Section 4).**

---

## Section 8: Observability & Debuggability Review

### Findings

- **O1. No structured logging yet.** One `logging.exception` call. No module-level loggers, no INFO event stream for milestone transitions. **Same as prior review** — and now matters more because subprocess runs are the new failure-prone surface. Default `logging.basicConfig(level=INFO)` in the CLI entry point. Module-level loggers. Log every milestone transition (`{milestone, run_number, status, retry_count}`), every subprocess invocation (`{command, cwd, exit_code, duration_ms}`), every dropout block, every middleware projection.
- **O2. Render logs are lost.** Subprocess stderr is held in the returned tool payload only. Write per-run logs to `logs/<milestone>-run-N.log`. Reference the log path in the structured error.
- **O3. UI projection silent on failure.** Section 1 A2 / Section 2 #1. Fix.
- **O4. Per-session timeline aggregator missing.** Same as prior review. A small `vm_session_summary` that walks `ratify/*.json` + `logs/*.log` and returns a chronological event list would make debug 10× faster.
- **O5. LangSmith trace ID surfacing.** Not visible — verify, document.
- **O6. Runbooks.** None yet. Two highest-leverage runbooks now:
  - `docs/runbooks/render-failed.md` — what to do when `vm_render_remotion_project` returns non-zero.
  - `docs/runbooks/script-approval-blocked.md` — what `script_approved=False` means and how to proceed.

### Debuggability check

If a user reports "session XYZ rendered a 2-second video instead of 60 seconds" three weeks post-run, can the team reconstruct what happened?
- ✅ `state.yaml` + `ratify/*.json` + (if implemented) `logs/*.log` + Remotion's `out/` artifacts.
- ❌ No record of which model version, which Remotion version, which `pnpm` lockfile was active. Add to `state.yaml`: `commit`, `model`, `producer_prompt_hash`, `remotion_version`, `node_version`, `pnpm_version`.

---

## Section 9: Deployment & Rollout Review

- **D1. Versioning.** `pyproject.toml` still `version = "0.1.0"`. No `CHANGELOG.md`. No release tag. Same gap.
- **D2. Dependency pins.** `deepagents>=0.5.3` and `langchain*>=0.3.0` still unbounded above. New: implicit dep on `pnpm@9.15.0` (good — pinned in `package.json:packageManager`). Implicit dep on Remotion (whichever version `remotion-builder` writes into per-session `package.json`). **The Remotion version is now a moving production dependency** — pin it in the remotion-builder skill's reference template.
- **D3. Node lockfile.** `pnpm-lock.yaml` committed. ✓
- **D4. CI.** Now includes ffmpeg (`93bf38a`). ✓
- **D5. Migration safety.** State schema has no version. Same as prior review. Add now, before audio milestone arrives.
- **D6. Feature flags.** `eval_mode` field in goal.yaml is the closest. The new `script_approved` parameter is the right shape for a "halt to user" flag — keep the pattern.
- **D7. Smoke tests post-deploy.** `pnpm golden:playable` is the canonical local smoke. ✅ Document it in README as the "first thing to run after install."
- **D8. NEW — Optional dependency surface.** `faster-whisper` is in `optional-dependencies.transcription`. Good shape. Apply the same pattern when Audio milestone lands (TTS provider client as opt-extra).

---

## Section 10: Long-Term Trajectory Review

### Tech debt — carried, paid down, accrued

| Item | Prior review | Today |
|---|---|---|
| Hand-rolled YAML (~120 LOC) | flagged | **carried + grew in risk** (ratify scalar JSON-in-YAML) |
| 14-kwarg fan-out | 13×4 | **worsened** (14×5) |
| Dead Windows-only code | flagged | **partially paid down** (`82cf0c5` removed hardcoded path) |
| Aspirational SKILL.md gap | flagged | **closed** ✅ |
| No state schema version | flagged | **carried** |
| Dropout only handles one milestone | flagged | **carried** |
| No CHANGELOG / no release tags | flagged | **carried** |
| Reflexion references | flagged | **closed** (removed from v2 skill) ✅ |
| Render subprocess in-memory logs | NEW | accrued |
| Subprocess argv injection on composition_id | NEW | accrued |
| `pnpm install` postinstall trust | NEW | accrued |
| Middleware silent projection failure | NEW | accrued |

Net: **2 closed, 4 carried (some worsened), 4 new.** Velocity is real; debt is climbing.

### Reversibility ratings (refreshed)

| Decision | 1 (one-way) → 5 (reversible) |
|---|---|
| Controller-only architecture | 3 — same as before; held under wider load |
| v2 as canonical (v1 dropped) | 4 — could re-enable v1, but tests/docs are now v2-only |
| Remotion as the rendering toolchain | 3 — swapping out would require new remotion-builder + render runner; the per-session project pattern survives |
| Subprocess execution for pnpm/Remotion | 4 — swappable for any other CLI |
| Goal.yaml as source of truth | 4 — same as before |
| Script approval as a hard gate | 5 — pure parameter |
| Hand-rolled YAML | 5 — same as before |
| Middleware ui_state projection | 5 — opt-in via agent factory |

### Path dependency

- `run-N` convention — locked in by ratify regex.
- `script-contract.json` is the new public contract per-script-run. Versioning it now (add `"version": 2` — wait, it already has `"version": 2` in `_write_script_contract`! ✅).
- `script.md` schema (`## Scene N` blocks with bare `type:`/`scene_intent:`/`content_brief:` keys) is now load-bearing for `ratify_script`. Document it in `docs/manifest-schema.md` or `docs/script-md-schema.md`.
- Remotion composition contract (`composition_id`, props) is implicit — the subagent decides. Tighten this when audio lands.

### The 1-year question

If a new engineer joins in 12 months and reads this repo cold, do they understand it?
- README + CLAUDE.md + AGENTS.md + golden-demo doc + v2 skill = strong onboarding ✅
- 17 typed tools with 14-kwarg fan-out = confusion ❌
- No structured logs to follow a session post-mortem = real friction ❌
- No CHANGELOG = "what changed between v0.1.0 and now?" gets an empty answer ⚠️

---

## Section 11: Design & UX Review

The branch *does* touch UX surfaces — the web-UI projection middleware and the publish-readiness checklist are user-facing. The Stage-1 skill task breakdown at HEAD is a planning artifact rather than a UX change. Not deeply audited here; flagged for review when implementation lands.

### Findings

- **U1. Script approval is the right gate at the right place.** The producer presents three options (Continue / Provide feedback / I edited manually). This pattern should be reused for build_scenes → render_package: today, that transition is implicit. **Recommendation:** add an explicit `render_approved=False` parameter on `vm_start_render_package` mirroring `script_approved`. The render is the expensive step; making the user say yes once explicitly is cheap insurance.
- **U2. `vm_websearch` as a distinct, visible step.** Strong UX call — users see what was retrieved before the manifest is written. Keep this pattern for any future external-fetch step.
- **U3. publish-readiness as a *checklist* not a *review*.** Today the user fills in `decision`, `notes`, and a per-dimension checklist. Without an agent review, this is just self-attestation. Approach C (Section 0C-bis) is the upgrade path.
- **U4. "Approve" double-click.** Section 4 — make `vm_start_build_scenes` idempotent.
- **U5. No "abort the render" path.** Section 1 A1.

---

## Required Outputs

### NOT in scope

| Item | Why deferred |
|---|---|
| Generate Audio milestone | Per SKILL.md; recommended next via Approach B |
| Reviewer / Editor subagents | Prompts on disk, not wired |
| GAN Evaluator | Implicitly dropped from v2 |
| Reflexion lessons | Implicitly dropped from v2 |
| Production deploy | Dev-only by design |

### What already exists (and is reused)

| Sub-problem | File | Reused? |
|---|---|---|
| Milestone state machine | `models.MilestoneState`, `session.DEFAULT_MILESTONES` | ✅ |
| Run-N convention | `session.create_milestone_run` | ✅ |
| Ratify pattern | `ratify.py`, `*_flow.ratify_and_update_*` | ✅ all 4 milestones |
| Subagent skill loading | `agent.build_subagents` | ✅ |
| Tool-call dropout detection | `controller.block_if_tool_call_dropout` | ⚠️ source_intake only |
| Path virtualization | `script_flow._to_virtual_path` | ⚠️ duplicated 2× |
| UI state projection | `ui_state` + `middleware` | ✅ new |
| Goal.yaml as SoT | `_goal_from_inputs_or_goal_file` | ✅ but kwargs explosion |
| Script approval gate | `start_build_scenes_milestone(script_approved=...)` | ✅ |

### Dream state delta

This branch moves the project **forward by three operational milestones** (source intake, build scenes, render package) and the script approval gate. It does **not** advance the quality/observability axis — that work is identical to what the prior review flagged. Velocity on pipeline scope is high; velocity on hardening debt is roughly zero. **Conscious decision required.**

### Error & Rescue Registry

Six critical gaps (Section 2):
1. Middleware silent UI-projection failure.
2. `init_video_session` overwrite without warning.
3. Dropout uncovered on script / build_scenes / render_package.
4. Render subprocess output is in-memory only — failure messages are unactionable.
5. Hand-rolled YAML corrupts ratify scalar on adversarial topics.
6. Missing `pnpm`/`ffprobe` not converted to clean errors.

### Failure Modes Registry

| CODEPATH | FAILURE MODE | RESCUED? | TEST? | USER SEES? | LOGGED? |
|---|---|---|---|---|---|
| `middleware._attach_ui_state` | projection raises | partial (silent) | N | nothing | N — **CRITICAL** |
| `init_video_session` | output_dir collision | N | N | nothing | N — **CRITICAL** |
| `block_if_tool_call_dropout` | script/build_scenes/render_package | N | N | wrong reason | N — **CRITICAL** |
| `_run_command` (render) | nonzero exit, 100 MB stderr | partial | partial | giant string in chat | N — **CRITICAL** |
| `load_state_yaml` | corrupt ratify scalar | partial (drops to `{}`) | N | silent ratify history loss | N — **CRITICAL** |
| `render_remotion_project` | pnpm/ffprobe missing | N | N | FileNotFoundError | N — gap |
| `vm_render_remotion_project` | composition_id with `--flag` | N | N | possibly mis-rendered | N — gap |

**Critical gaps total: 5.**

### TODOs proposed (priority order, ready for `TODOS.md`)

| # | Title | Priority | Effort (CC) | Carries / New |
|---|---|---|---|---|
| 1 | **PyYAML migration for `state_store`** | P1 | S | carries (prior #1) |
| 2 | **Generalize `block_if_tool_call_dropout` to all milestones** | P1 | S | carries (prior #3) |
| 3 | **Output-dir collision guard in `init_video_session`** | P1 | XS | carries (prior #4) |
| 4 | **Stream render subprocess output to `logs/<milestone>-run-N.log` + return last N lines and log path on failure** | P1 | M | NEW |
| 5 | **Log + surface middleware UI-projection failures** | P1 | XS | NEW |
| 6 | **Add `state_schema_version` to state.yaml + migration helper** | P1 | S | carries (prior #9) |
| 7 | **Slim typed-tool kwargs surface (keep on `vm_init_video_session` only)** | P1 | M | carries (prior #7, worsened) |
| 8 | **Validate `composition_id` against strict regex before subprocess splat** | P1 | XS | NEW |
| 9 | **Add `--ignore-scripts` (or equivalent) to `pnpm install` in render runner** | P1 | XS | NEW |
| 10 | **Configure structured logging (module-level loggers + INFO events for milestone transitions, subprocess invocations, dropout blocks)** | P2 | S | carries (prior #10) |
| 11 | **`shutil.which` precheck for `pnpm` and `ffprobe`; convert to named errors** | P2 | XS | NEW |
| 12 | **Idempotency for `vm_start_build_scenes` when run-N is already IN_PROGRESS** | P2 | XS | NEW |
| 13 | **Adversarial goal.yaml round-trip tests** | P2 | S | carries (prior #14) |
| 14 | **Tool-call dropout symmetry tests across milestones** | P2 | S | NEW |
| 15 | **Render-failure unit tests (pnpm missing, timeout, nonzero exit, log capture)** | P2 | M | NEW |
| 16 | **Pin upper bounds on `deepagents`, `langchain*`** | P2 | XS | carries (prior #11) |
| 17 | **Pin Remotion version in remotion-builder template** | P2 | XS | NEW |
| 18 | **Split `build_render_flow.py` → `render_runner.py` + `publish_readiness.py`** | P2 | S | NEW |
| 19 | **Consolidate `_to_virtual_path` into one helper (`paths.py`)** | P2 | XS | carries (prior #6) |
| 20 | **Drop unused `tavily-python` dep** | P3 | XS | carries (prior #12) |
| 21 | **Add `render_approved=False` parameter on `vm_start_render_package`** | P3 | XS | NEW |
| 22 | **`CHANGELOG.md` + v0.1.0 tag** | P3 | XS | carries (prior #17) |
| 23 | **`docs/script-md-schema.md` and `docs/runbooks/{render-failed,script-approval-blocked}.md`** | P3 | S | NEW |
| 24 | **Path-confinement check on `local_file` / `excalidraw_file`** | P3 | S | carries (prior #18) |
| 25 | **Composition-dimension check in `ratify_build_scenes` (16:9 vs 9:16 etc.)** | P3 | S | NEW |
| 26 | **Add commit/model/remotion/node/pnpm provenance to state.yaml** | P3 | S | NEW |

### Diagrams produced
1. ✅ Component dependency graph (Section 1).
2. ✅ Build → render data flow (Section 4).

### Diagrams missing
- Milestone state machine (4 milestones with retry / blocked / script-approval transitions).
- Render subprocess sequence diagram (pnpm tsc → render → still → ratify).
- Failure-mode flowchart per milestone.

### Stale diagram audit
No ASCII diagrams currently live in source files. The prior review's diagrams are correctly archived in `cc_ceo_reviews/`.

---

## Outside Voice (skipped)

Single-pass written review per the user's request. If wanted, pipe this report to a different model and ask "what did this miss?".

---

## Completion Summary

```text
+========================================================================+
|        CEO PLAN REVIEW — COMPLETION SUMMARY (2026-05-14)               |
+========================================================================+
| Mode selected         | EXPAND SCOPE (cautiously) — quality push next |
| System Audit          | All 4 milestones operational; +47 commits     |
| Step 0                | Approach A→B recommended; Approach C deferred |
| Section 1  (Arch)     | 8 issues found (A1-A8)                        |
| Section 2  (Errors)   | 21 paths mapped, 6 CRITICAL GAPS              |
| Section 3  (Security) | 3 new threats; subprocess + composition_id    |
| Section 4  (Data/UX)  | 7 edge cases mapped, 3 partially handled      |
| Section 5  (Quality)  | 9 issues found (Q1-Q9)                        |
| Section 6  (Tests)    | 8 gaps; render-failure suite is the big miss  |
| Section 7  (Perf)     | 5 notes, 2 user-impacting                     |
| Section 8  (Observ)   | 6 gaps; structured logging still missing      |
| Section 9  (Deploy)   | 8 risks; Remotion version now load-bearing    |
| Section 10 (Future)   | Debt: 2 closed, 4 carried, 4 new              |
| Section 11 (Design)   | 5 UX notes; render_approved gate recommended  |
+------------------------------------------------------------------------+
| NOT in scope          | 5 items                                       |
| What already exists   | 9 items mapped                                |
| Dream state delta     | pipeline axis only — quality axis flat        |
| Error/rescue registry | 21 methods, 6 critical gaps                   |
| Failure modes         | 7 entries, 5 CRITICAL                         |
| TODOS proposed        | 26 items (10 carried, 16 new)                 |
| Scope proposals       | 0 (HOLD on pipeline scope until A is done)    |
| CEO plan persisted    | this file                                     |
| Outside voice         | skipped                                       |
| Diagrams produced     | 2                                             |
| Stale diagrams found  | 0                                             |
| Unresolved decisions  | 1 (see below)                                 |
+========================================================================+
```

### Unresolved decisions (require user input)

1. **Approach A (hardening), then Approach B (Generate Audio)?** The recommendation is to do Approach A first — close the 6 critical gaps, slim the kwargs surface, add structured logging, ship v0.1.0 with a CHANGELOG — *before* starting the Audio milestone. If user value pressure dictates Audio first, the absolute minimum prerequisite from A is items #1-#9 in the TODO table (silent-failure surfaces + composition_id validation). Without those, the Audio milestone will add another silent failure surface on top of three existing ones.

---

## Verdict

**The project has materially advanced.** All four milestones run, the script approval gate works, golden playable smoke produces a real MP4, the web-UI has a live state projection, and the v2 skill matches what is wired. The architectural bet (controller-only DeepAgents Producer with skills-based progressive disclosure) **held under load** — going from 2 milestones to 4 did not require introducing a LangGraph DAG layer. That is a real validation of the prior-review trip-wire (no new pseudo-tool-call failure modes; new subagent surface is clean).

**Five critical silent-failure gaps remain or have appeared.** Three carried from the prior review (output-dir collision, dropout-only-on-one-milestone, hand-rolled-YAML corruption). Two are new from the render surface (middleware silent projection failure, render subprocess output trapped in memory). All have small fixes.

**The 14-kwarg fan-out is the only thing that got worse.** It is also the easiest material refactor — strip the goal-shaped kwargs off every tool *except* `vm_init_video_session`. Saves 70 redundant parameters, removes a class of LLM tool-call drift errors, and is < 1 day of work with CC.

**Strategic call:** do Approach A (hardening + quality push) before Approach B (Generate Audio). The quality debt the prior review flagged is the same debt today; the per-render subprocess surface multiplied the cost of silent-logging by a lot. Tag v0.1.0 at the end of A, with a CHANGELOG, and ship it as "all-four-milestones working, narrated audio next." That is a defensible release.

**Engineering preference compliance:** DRY violations remain (path virtualization 2×, kwargs fan-out 5×) — flagged. Tests grew handsomely; render-failure suite is the big remaining gap. Observability is still the weakest dimension — no structured logging today, and now there are subprocess runs that need it. Security posture for a dev-only tool is adequate; subprocess composition_id splat and `pnpm` postinstall trust are the two new items.

**Recommended next steps in order:**
1. Close the 6 critical gaps (TODOs 1-6). ~1.5 days with CC.
2. Slim the kwargs surface (TODO 7). ~0.5 day.
3. Composition-id regex + pnpm `--ignore-scripts` (TODOs 8-9). ~0.5 day.
4. Structured logging + render log streaming (TODOs 4, 10). ~1 day.
5. Tag `v0.1.0` with `CHANGELOG.md` (TODO 22). ~0.5 day.
6. Then Approach B: Audio milestone.

— end of review —
