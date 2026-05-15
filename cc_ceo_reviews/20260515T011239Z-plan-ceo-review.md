# CEO Review — deepagents-video-maker

- **Date:** 2026-05-15 01:12:39 UTC
- **Branch:** `claude/gracious-gates-jttix`
- **HEAD:** `9380e5d` (feat(skill): implement Stage 1 plan for video-maker skill with detailed task breakdown and acceptance criteria)
- **Reviewer skill:** `gstack/plan-ceo-review` framework (https://github.com/garrytan/gstack.git). The local gstack install is absent (`~/.claude/skills/gstack/` not present); this review reproduces the 11-section framework, prime directives, and required outputs from memory and the prior review template (`cc_ceo_reviews/20260509T012631Z-plan-ceo-review.md`). The skill's interactive `AskUserQuestion` ceremonies are replaced with written recommendations.
- **Mode selected:** HOLD SCOPE — the pipeline has reached end-to-end runnable (source_intake → script → build_scenes → render_package) plus a deterministic playable golden demo. The right CEO move is to **harden the foundation that was deferred in the last review** before chasing new milestones (audio, HITL, evaluator). Scope expansions surface as proposals, not absorbed.
- **Posture:** Rigorous reviewer. Zero silent failures. Every error has a name. Diagrams mandatory. Permission #9 invoked where I see a fundamentally better path.

---

## 0. Pre-Review System Audit

### Repository state

- Working tree clean. Branch `claude/gracious-gates-jttix` is fresh; HEAD = `9380e5d`.
- Source surface has grown from ~1.7k LOC at the prior review to **2,872 LOC across 18 Python files**. Test surface: **17 test files, 87 tests collected**. Of those, **86 pass locally; 1 (`test_golden_playable_smoke_produces_probeable_mp4`) fails locally without ffmpeg installed** — CI installs ffmpeg (`.github/workflows/ci.yml:24`), so this is environment-conditional, not a defect on master.
- 1 outstanding `FIXME` reference remains in skill prompts (`skills/video-maker-v2/agents/scene-batch-generator.md:191`, `scene-patch-generator.md:85-87,95`). These are **intentional fallback markers**, identical pattern to the prior review.
- Hand-rolled YAML in `state_store.py` is **still in tree** (`PyYAML>=6.0` is in `pyproject.toml:12` but unused). The dependency exists; the code didn't migrate. **Money paid, debt not retired.**

### What has moved since 2026-05-09

The previous review left 20 TODOs in priority order. Current state:

| # | Item from prior review | Status today |
|---|---|---|
| 1 | PyYAML migration | **Not done** — hand-rolled YAML still in `state_store.py`; PyYAML is a paid dep |
| 2 | Surface Tavily absence to producer | **Partial** — `vm_websearch` is now a distinct typed tool; `_websearch_items` returns an explicit `ERROR: websearch source intake requires TAVILY_API_KEY` item (`source_flow.py:191-197`). Better. But `vm_websearch` itself returns `status: ok|error` without surfacing the *cause* (missing key vs Tavily 5xx vs zero URL results) to the producer in a structured form |
| 3 | Generalize `block_if_tool_call_dropout` to all milestones | **Not done** — `controller.py:29` still only handles `source_intake` (the prior `research`, renamed). Script, build_scenes, render_package have no dropout safety net |
| 4 | Output-dir collision guard in `init_video_session` | **Not done** — `session.py:33` still uses `mkdir(exist_ok=True)` and silently overwrites |
| 5 | Reconcile SKILL.md aspirational scope | **Mostly done** — `skills/video-maker-v2/SKILL.md` describes only the 4 wired milestones; designed-but-unimplemented paths (audio, GAN Evaluator, Layer 2 Reviewer) are explicitly listed under **Hard boundaries → Do not** |
| 6 | Consolidate `_to_virtual_path` | **Partial** — `build_render_flow.py:20` now imports from `script_flow._to_virtual_path` (1 implementation in src/). `scripts/deepagents_video_maker.py:141 to_virtual_path` is a second variant with Windows-extended-prefix handling. Net: 3× → 2× |
| 7 | Slim typed-tool kwargs surface | **Not done** — `vm_init_video_session`, `vm_ratify_source_intake`, `vm_build_scriptwriter_task`, and now also `vm_ratify_script` still take 11+ optional kwargs each (`langchain_tools.py:50-65, 122-138, 187-220`) |
| 8 | Delete dead Windows-only code | **Not done** — `execute_pwsh`, `project_glob`, `patch_deepagents_path_validation` are still defined in `scripts/deepagents_video_maker.py:167, 188, 213` |
| 9 | Add `state_schema_version` to state.yaml | **Not done** — milestone list changed (research/script/assets/assembly → source_intake/script/build_scenes/render_package). **There is no schema-version field today and no migration helper.** Any old `output/<session>/state.yaml` from before the rename is unreadable |
| 10 | Structured logging | **Not done** — codebase uses prints in `scripts/`; no `logging` module wiring in `src/` |
| 11 | Upper-bound pins on deepagents/langchain | **Not done** — `deepagents>=0.5.3`, `langchain>=0.3.0`, `langchain-anthropic>=0.3.0`, `langchain-openai>=0.3.0` remain open-ended |
| 12 | Drop unused tavily-python | **Inverted** — `source_flow.py:200` now imports `from tavily import TavilyClient` directly, so both `tavily-python` and `langchain-tavily` are dependencies and the latter has no caller in `src/` that I can locate |
| 13 | E2E producer-protocol stub-model test | **Not done** — no test exercises the full controller cycle against a stub model |
| 14 | Adversarial topic round-trip tests | **Not done** — `test_state_store.py` has 5 tests, none covers quoted/multiline/embedded-quote topics |
| 15 | Promote manifest-schema to `docs/` | **Superseded** — the project pivoted from `manifest.json` to `source-manifest.md` + `script-contract.json` + Remotion project. The new contract surface is described in `skills/video-maker-v2/references/`; whether it constitutes a public versioned contract is **still unresolved** |
| 16 | Runbooks for blocked-milestone / dropout | **Not done** |
| 17 | CHANGELOG.md / v0.1.0 tag | **Not done** |
| 18 | Path-confinement on `local_file`/`excalidraw_file` | **Not done** |
| 19 | Reflexion read/write | **Removed** — `reflexion/*.json` is explicitly listed under **Do not** in the v2 SKILL. Net: hook is no longer dangling. ✅ |
| 20 | Web-UI eslint/tsc CI step | **Not done** |

**Verdict:** the team chose **Approach A** from the last review (finish the in-tree pipeline) and delivered it convincingly — full source-to-MP4 path with deterministic golden smokes. **But the foundational hardening from Approach C was not done first**, so the 4-milestone pipeline is now running on the same scar tissue the prior review flagged. This is the central tension to call out.

### Recently touched files (signal: where attention is going)

The last 30 commits show: build/render flow (`build_render_flow.py`), golden:playable smoke (3 new smoke scripts in `scripts/`), README Quick Start, Remotion-builder skill, VSCode launch configs, harness wiring, gitignore for `runs/` and `logs/`, ffmpeg in CI, websearch deepening (advanced search depth, `vm_websearch` tool, data_card grounding ratify), Windows path normalization fix. **The team has been pushing the pipeline end-to-end forward and improving observability of the running session — not paying down debt.** That is a defensible bet given the milestone completion, but it does compound the foundational risk.

---

## Step 0: Premise Challenge + Mode Selection

### 0A. Premise Challenge — is this the right problem?

> "Composition-first, hatch-pet-aligned end-to-end video pipeline that delegates Remotion implementation to a subagent, validated by deterministic ratify gates and a golden-playable smoke."

Three premises worth challenging directly:

1. **"Composition-first, no `video-pipeline-cli`."** The v2 SKILL.md is forceful about *not* calling v1 CLI or v1 template mutation (`skills/video-maker-v2/SKILL.md:147-160`). This is the **right** architectural bet: the rendering toolchain is a black box owned by the Remotion Builder subagent, and Producer only validates the structural contract (`package.json`, `src/index.ts`, `out/video.mp4`). It de-risks the per-scene loop, removes scene-batch-generator from the critical path, and gives a clean handoff. **Keep this bet.** The cost is real (Remotion Builder is now load-bearing; one bad subagent run breaks the visual pipeline), and the deterministic playable smoke is the right hedge.

2. **"`script-contract.json` + `script.md` is the manifest"** — the v2 pivot replaced the prior `manifest.json` contract with a contract+narrative pair, with Remotion Builder consuming the pair to generate the project. The `script-contract.json` writer (`script_flow.py:152-190`) is now the most upstream creative-boundary file. **Is this a versioned public contract or an internal artifact?** The README and `skills/video-maker-v2/references/` describe it but there is no `version` field discipline, no `docs/script-contract-schema.md`. **If a downstream rendering tool (or future v3 producer) wants to consume this, the schema must be promoted to a versioned contract today.** Same critique as the manifest-schema item in the previous review, just renamed.

3. **"4 milestones, controller-only, all unguarded except source_intake."** `controller.block_if_tool_call_dropout` only handles `source_intake` (`controller.py:29`). When script, build_scenes, or render_package miss a real `task()` call, there is no specialized blocker — the milestone will just retry and eventually fail ratify with a generic reason. **This is the same gap as the prior review, just promoted from a 2-milestone to a 4-milestone footprint.** The cost of leaving it unaddressed is now 4× larger, because the producer has 4 dispatch points to drop tool calls on. **Fix the controller before adding audio or HITL.**

**Verdict on premises:** problem framing has improved (the v1 ↔ v2 confusion from the last review is gone). One implementation premise (the `script-contract.json` schema as informal) is wrong. The controller-only premise is right *and* the safety-net debt is now overdue.

### 0B. Existing Code Leverage — what already partially solves this?

| Sub-problem | Existing code | Reused? |
|---|---|---|
| Milestone state machine | `models.MilestoneState` + `state_store.update_milestone_status` | Yes |
| Run-N directory convention | `session.create_milestone_run` | Yes |
| Artifact gate validation | `ratify.ratify_source_manifest`, `ratify.ratify_script`, `build_render_flow.ratify_build_scenes`, `build_render_flow.ratify_render_package` | Yes |
| Tool-call dropout detection | `artifacts.detect_tool_call_dropout`, `controller.block_if_tool_call_dropout` | Yes — **source_intake only** |
| Subagent skill loading | DeepAgents `skills=` field, `.deepagents/skills/video-maker-v2-*` | Yes |
| Path virtualization | `script_flow._to_virtual_path`, `scripts/.../to_virtual_path` | Reduced from 3× to 2× |
| Goal parsing | `params.parse_video_request` | Yes |
| YAML I/O | Hand-rolled `state_store.save_*` / `load_*` | **Reinvented, despite PyYAML being a dependency** |
| Websearch + cache | `source_flow.run_websearch_and_cache` + `_websearch_cache_path` | Yes — caches to `artifacts/source/websearch-results.json`. Producer-visible step via `vm_websearch` |
| UI state projection | `ui_state.build_video_maker_ui_state` + `VideoMakerUiStateMiddleware` | Yes — clean separation, **net new and good** |

**Largest active DRY violation:** still path virtualization, plus the 11-kwarg fan-out across 4 typed tools. The dropout-detection gap is now the largest *correctness* leverage point.

### 0C. Dream State Mapping

```
  CURRENT STATE                    THIS BRANCH                   12-MONTH IDEAL
  ─────────────                    ───────────                   ──────────────
  source_intake → script           9380e5d: skill                Full pipeline:
  → build_scenes →                 plan stage 1                  source → script →
  render_package wired             (skill scope                  user review →
                                   doc work) +                   build → render →
  Deterministic golden:             prior commits                 publish + audio +
  playable smoke produces           on rendering                  HITL approval +
  real MP4                          contract,                    GAN Evaluator
                                   websearch                     contract loop
  86 tests passing                  deepening,
  (87 collected, 1                 contract                     Quality:
  ffmpeg-conditional)               overwrite guard              Layer-1 ratify +
                                                                Layer-2 reviewer
  ui_state middleware              No foundational               Observability:
  surfaces progress                 hardening                    Structured logs,
  to web UI                                                       session traces,
                                                                  eval dashboard
  Quality:
  Layer-1 ratify                                                  Schema versioned:
  + data_card                                                     state.yaml,
  grounding                                                       script-contract,
                                                                  source-manifest
  Observability:                                                  contracts
  ratify JSONs +
  ui_state                                                        Reflexion:
  middleware                                                      explicitly
                                                                  removed (✅)
  Pipeline coverage:
  end-to-end MP4
  (deterministic
  ffmpeg path)
```

This branch (`9380e5d` + ancestors) advances the project meaningfully along **two axes simultaneously**:
- *Pipeline axis:* now produces a playable MP4 end-to-end.
- *Skill axis:* SKILL.md aligned with the operational pipeline; v1 explicitly de-supported.

It explicitly **does not** advance the foundational-hardening axis. That is the call-out: pipeline progress without foundation progress will compound when audio / HITL / Layer 2 land.

### 0C-bis. Implementation Alternatives (mandatory)

The "what to build next" decision has three plausible shapes again, but the framing has shifted because the end-to-end product now exists:

```
APPROACH A: Add the next product surface (Audio milestone, or HITL approval flow)
  Summary: Implement vm_start_audio, vm_generate_audio (Tavily-free; TTS via local engine or
           external API), vm_ratify_audio with audio-manifest.json schema. Wire the
           existing audio-contract.md into a real milestone slot.
           Or: implement the user-script-checkpoint as a true HITL pause (LangGraph
           interrupt + resume) instead of producer politeness.
  Effort:  M-L (human ~1-2 weeks; CC ~3-5 days)
  Risk:    Med — TTS adds external/local engine dep; HITL adds web-UI resume protocol.
  Pros:    - Closes the audio-shaped hole in the user product (silent video today).
           - HITL flips the project from "controller + politeness" to "controller + real
             pause point," which is the right product UX.
           - Either choice forces audio-manifest or interrupt-resume to become a
             tested contract.
  Cons:    - Same foundational scar tissue as today, just one milestone larger.
           - Audio engine choice (Coqui, ElevenLabs, OpenAI TTS, local Whisper-for-
             duration) is a procurement decision that hasn't been made; deferring
             until that's settled is correct.
  Reuses:  Existing milestone state machine, ratify pattern, RunInfo, ui_state.

APPROACH B: Harden the foundation before any new surface (FINISH approach C from the
            prior review)
  Summary: Close the 6 critical silent-failure gaps identified by the prior review
           and still open today: PyYAML migration, tool-call dropout generalization
           to all milestones, init_video_session overwrite guard, dead Windows-only
           code excision, structured logging foundation, state_schema_version +
           migration helper, upper-bound dep pins.
           Add the E2E producer-protocol stub-model test that asserts the controller
           protocol holds against a faked LLM.
  Effort:  S-M (human ~3-5 days; CC ~1-2 days)
  Risk:    Low — pure hardening.
  Pros:    - Eliminates the dropout footgun before it triggers on the 3 unprotected
             milestones.
           - Makes audio/HITL safe to land.
           - Pays for already-purchased dep (PyYAML) which is dead weight today.
           - Synthetic eval gives the team confidence to move faster after.
  Cons:    - Zero new user-visible product surface.
           - If left to drift again it becomes "we're always *almost* ready to
             harden."
  Reuses:  Everything currently in tree.

APPROACH C: Promote the rendering / script-contract surface to a versioned public
            contract
  Summary: Lock script-contract.json schema with a `version` field. Promote
           skills/video-maker-v2/references/{workflow-contract,scriptwriter-output-
           contract,audio-contract,scene-layout-contract}.md to docs/ and treat
           them as the public surface. Add a migration test:
           "v1 → v2 contract input still ratifies." Versioning Remotion Builder
           output contract (what files must exist under `out/` and `final/`) so
           downstream tools can consume.
  Effort:  S (human ~2-3 days; CC ~1 day)
  Risk:    Low — pure documentation + lightweight schema enforcement.
  Pros:    - Treats the contract surface as load-bearing, which it is.
           - Enables a future v3 producer or external rendering toolchain.
           - Forces a clean answer to "is script-contract.json public or
             internal?".
  Cons:    - Without B done first, schema versioning is fragile (PyYAML migration
             may force shape changes that retroactively break v1 contracts).
  Reuses:  Existing skill references and ratify gates.

RECOMMENDATION: B, then C, then A.
  WHY: Approach B is the smallest defensible pre-requisite for *anything else*. The
  prior review recommended B+C; the team chose A and built it; now A is done. The
  next sequence must close foundational debt before the audio milestone or HITL
  flow lands, otherwise the dropout safety net (which is now 4× under-protected)
  will turn into a 5× under-protected one. Approach C is the second pre-requisite
  because the script-contract schema is already the de facto public contract;
  every additional consumer (audio milestone, future renderer, evaluator) makes
  versioning more expensive. Approach A is *deferred but not killed*: pick it up
  the moment B + C are in.
```

### 0D. Mode-Specific Analysis (HOLD SCOPE)

**Complexity check:** Repo is 2,872 LOC in src/ + ~250 LOC web-ui agent + ~640 LOC scripts/. Module sizes:
- `langchain_tools.py` — 554 LOC, **largest source module**. Kwargs-fan-out across 4 tools is the dominant smell. Same critique as prior review, now amplified by 2 new typed tools (`vm_render_remotion_project`, `vm_package_render_output`, `vm_build_publish_readiness_report`) which also accept the goal-shaped surface.
- `build_render_flow.py` — 514 LOC, **second-largest**. New since last review. Contains render command wiring (`pnpm install`, `pnpm exec tsc --noEmit`, `remotion render`, `remotion still`), package step, publish-readiness JSON+MD report, ratify of build_scenes and render_package. Reasonably decomposed but **subprocess invocation is the single biggest external-failure surface** and its error-handling path (`_run_command` at `build_render_flow.py:277`) captures stdout/stderr but does not differentiate transient failures (network during `pnpm install`) from logic failures (TypeScript error). Producer sees a single boolean pass/fail.
- `source_flow.py` — 293 LOC. Manifest writer + Tavily-backed websearch + cache. Reasonable.
- `state_store.py` — 193 LOC. Still hand-rolled YAML. Same critique.
- `ratify.py` — 214 LOC. Three ratify functions (script, source-manifest, data_card_grounding by extension). Regex-based; same shape as prior review.
- `scripts/deepagents_video_maker.py` — has Windows-only code (`execute_pwsh` hardcoding `C:\Program Files\PowerShell\7\pwsh.exe`), `patch_deepagents_path_validation` reaching into DeepAgents' private `middleware.filesystem`. Both still **dead code** — defined and decorated with `@tool` but never registered in `build_native_tools()`. Carryover from prior review.

**Minimum set that achieves the stated goal (source→script→build→render):** 14 typed tools + 2 subagents + 4 ratify gates + Tavily backend + Remotion runtime. That's roughly what's wired. No further reduction is honest.

### 0E. NOT in Scope (this review respects it)

- Audio milestone — `references/audio-contract.md` exists, but no Producer/typed-tool plumbing for it. Explicitly deferred per SKILL.md §4.
- HITL approval flow — implemented as Producer politeness checkpoint, not as a real `interrupt`.
- GAN Evaluator + Reviewer + scene-batch / scene-patch generators — designed prompts on disk, explicitly disabled per SKILL.md Do-not list.
- v1 `video-maker` — explicitly desupported.

---

## Section 1: Architecture Review

### Component dependency graph (current)

```
                ┌─────────────────────────────────────────┐
                │      User / Web UI (LangGraph dev)      │
                │      (web-ui/agent/agent.py)            │
                └────────────────────┬────────────────────┘
                                     │
                          invokes via thread_id
                                     │
                                     ▼
        ┌────────────────────────────────────────────────────┐
        │   create_video_maker_agent (agent.py)              │
        │   model: anthropic|deepseek|zhipuai (resolved)     │
        │   system_prompt: prompts/producer.md (zh-en)       │
        │   tools: build_langchain_tools() (~14 typed tools) │
        │   subagents: ["scriptwriter", "remotion-builder"]  │
        │   middleware: VideoMakerUiStateMiddleware          │
        │   backend: FilesystemBackend(virtual_mode=True)    │
        └─────────────┬──────────────────────────────────────┘
                      │
       ┌──────────────┼─────────────────────────────────┐
       │              │                                 │
       ▼              ▼                                 ▼
  typed tools    producer.md                     subagent task()
  (source_       hard-rules                      scriptwriter (skill=
   flow.py,      controller                       .deepagents/skills/
   script_       protocol                         video-maker-v2-
   flow.py,                                       scriptwriter)
   build_                                        remotion-builder
   render_                                        (skill=
   flow.py,                                       .deepagents/skills/
   ratify.py,                                    video-maker-v2-
   session.py,                                   remotion-builder)
   state_store.                                   Tavily called
   py)                                            indirectly via
                                                  vm_websearch
       │                                                 │
       └────────────┬────────────────────────────────────┘
                    │
                    ▼
       ┌──────────────────────────────────────────────────┐
       │  Filesystem (output/<session>/)                   │
       │  goal.yaml, state.yaml,                           │
       │  artifacts/source/source-manifest.md,             │
       │  artifacts/source/websearch-results.json (cache), │
       │  artifacts/script/run-N/{script-contract.json,    │
       │                          script.md},              │
       │  remotion-project/{package.json, src/index.ts,    │
       │                    out/{video.mp4,thumbnail.jpg}},│
       │  final/{video.mp4, thumbnail.jpg,                 │
       │         publish-readiness.md},                     │
       │  ratify/{source-intake,script-run-N,build-scenes, │
       │           render-package,publish-readiness}.json   │
       └──────────────────────────────────────────────────┘
```

### Architecture findings

**A1 — Aspirational vs operational pipeline gap: RESOLVED.** SKILL.md describes only the wired 4-milestone pipeline; designed-but-unimplemented surfaces (audio, evaluator, reviewer) are in the Do-not list. ✅ Closes A1 from the prior review.

**A2 — Coupling: typed tools are STILL kwargs-flooded with VideoMakerGoal fields.** `vm_init_video_session` (15 params), `vm_ratify_source_intake` (14 params), `vm_build_scriptwriter_task` (~13 params), `vm_ratify_script` (~11 params). The model has to remember 11+ optional fields per call. The function bodies all funnel into `_goal_from_inputs_or_goal_file`, which supports the goal.yaml fallback. **Recommendation unchanged from prior review:** retain only `output_dir` + `run_number` on these tools after init, and require the goal to live in `goal.yaml`. Re-passing the goal invites drift between caller-supplied and persisted goals. Promote `vm_init_video_session` and `vm_parse_video_request` as the only goal-shaped surfaces.

**A3 — Tool-call dropout safety net is STILL only on source_intake.** `controller.py:29` checks `milestone_id == "source_intake"`; the other three milestones (`script`, `build_scenes`, `render_package`) have **no dropout protection**. When the model emits `<invoke name="task">` text without a real tool call, those milestones fail silently — ratify will eventually trip, but the blocking_reason will not name dropout. **Same gap as the prior review, multiplied by the pipeline's growth from 2 to 4 milestones.**

**A4 — `build_render_flow._run_command` collapses transient and logic failures.** `subprocess.run(...).returncode` is the only signal; `pnpm install` network failure looks identical to a TypeScript compile error. The retry counter on `build_scenes` and `render_package` will burn through `max_retries` (3 by default) without differentiating. Recommendation: classify exit codes / stderr patterns (`network`, `lockfile`, `tsc`, `remotion`) and surface them in `ratify_payload.metadata.failure_class`. Producer can then choose retry-with-install vs block-for-user.

**A5 — Web UI integration via `VideoMakerUiStateMiddleware` is a net positive.** `middleware.py` wraps tool calls to project `video_maker` UI state into the LangGraph top-level state. Clean separation, exception-safe (`except Exception: return result`). The producer prompt and `langchain_tools` participate via `_with_ui_state` and `build_video_maker_ui_state`. Single point of failure: the projection's `output_dir` resolution (`middleware.py:76`) silently returns `None` if the tool result has no `output_dir`, which silently drops UI state without logging. Add a debug log.

**A6 — Rollback posture (unchanged).** Reversibility 5/5 for sessions. Producer-side mid-flight LLM rollback = `state.workflow_status = blocked`. No DB migrations. Solid.

**A7 — Scaling characteristics (unchanged).** Single-user CLI / single-session web UI. `init_video_session` still uses `mkdir(exist_ok=True)` (`session.py:33`). Two `init` calls in the same second still overwrite goal.yaml/state.yaml. **Same critical gap as prior review.**

**A8 — Render-time subprocess assumes a hermetic environment.** `pnpm install --ignore-workspace` from `build_render_flow.py:185` runs against a `remotion-project/package.json` that's generated by the Remotion Builder subagent. Three failure modes: missing pnpm in PATH, npm-registry network down, `package.json` malformed. None of these surfaces a distinct error class — all become `passed: false` with truncated stdout/stderr. Not a release blocker (this is a dev-only tool), but flagged for runbook coverage.

**Required architecture diagrams produced:** 1 (above). **Diagrams missing:** state-machine for milestone transitions (especially the script-review checkpoint), render-command pipeline (subprocess chain), Remotion Builder dispatch sequence.

---

## Section 2: Error & Rescue Map

| METHOD/CODEPATH | WHAT CAN GO WRONG | EXCEPTION CLASS | RESCUED? | RESCUE ACTION | USER SEES |
|---|---|---|---|---|---|
| `agent.create_video_maker_agent` | DeepAgents not installed | `ImportError` → `RuntimeError` | Y | re-raises with clear message | "DeepAgents runtime is required to create the native video-maker agent." |
| `source_flow.run_websearch_and_cache` | TAVILY_API_KEY missing | none raised | Y | returns `_error_item` with cause | manifest item: `note: ERROR: websearch source intake requires TAVILY_API_KEY` — **better than before** ✅ |
| `source_flow._websearch_items` | Tavily 429 / 5xx | broad `Exception` caught | Y | returns `_error_item` with cause | `ERROR: websearch failed: <exc>` in manifest |
| `source_flow._websearch_items` cache read | malformed cache JSON | broad `Exception` caught | Y | falls through to fresh fetch | silent re-fetch |
| `state_store.load_goal_yaml` | YAML file with quote-in-quote handled by hand-rolled unquoter | partial | partial | `ValueError` only if topic missing | **silent corruption path still exists** for embedded backslashes/multilines |
| `state_store.load_state_yaml` | malformed file from older writer (e.g., milestone rename) | `ValueError` from `MilestoneStatus(value)` | N | uncaught | crash; **no state_schema_version field, no migration helper** |
| `session.init_video_session` | output_dir already exists (timestamp collision or re-run) | none | N | `mkdir(exist_ok=True)` silent | overwrites goal.yaml/state.yaml; **silent data loss** — unchanged from prior review |
| `session.create_milestone_run` | concurrent run-N globbing race | none | N | uncaught | duplicate run-N possible |
| `source_flow.write_source_manifest` | folder source with empty folder | none | N | `_error_item` emitted into manifest | manifest has ERROR item, ratify catches via `has_no_error_items` |
| `script_flow.start_script_milestone` | source_intake not completed | `RuntimeError` | Y | raised | `vm_start_script` catches and returns structured error (good) |
| `script_flow.ratify_and_update_script` | manifest is valid JSON but `target_scene_count` is non-dict | dict-check exists at `ratify.py:60` | Y | falls through to default 1..999 | check passes when it might not have intent |
| `ratify.ratify_script` | regex scene-block matcher misses a scene whose heading has trailing whitespace | none | N | silent miscount | scene_count_match check fails for wrong reason |
| `ratify.ratify_script` | `type:` line lives inside a fenced code block within the scene | regex still matches | N | false positive on `scene_type_required` | scene rejected for wrong reason |
| `ratify.ratify_script` data_card grounding (`data_card_grounding`) | source-manifest note text contains the number in a different language form (e.g. `三十亿` vs `30亿`) | regex literal | N | false negative | data_card incorrectly fails |
| `controller.block_if_tool_call_dropout` | only handles `source_intake` (`controller.py:29`) | none | N — **GAP** | only source_intake is protected | script, build_scenes, render_package dropouts fail silently |
| `langchain_tools.vm_build_scriptwriter_task` | `output_dir` doesn't exist | `FileNotFoundError` from `load_state_yaml` | N | uncaught | crash |
| `langchain_tools.vm_init_video_session` | both `prompt` and structured inputs missing | `ValueError` | Y | raised | "prompt or structured inputs are required" — but **the tool decorator may surface this as a tool error, not a structured error result.** Inconsistent with `vm_start_script` pattern. |
| `build_render_flow.render_remotion_project` | `pnpm` not in PATH | `FileNotFoundError` from subprocess | N | uncaught | crash |
| `build_render_flow.render_remotion_project` | tsc fails | `returncode != 0` | Y | returns `passed: false` with truncated logs | producer sees `passed: false`; **no failure-class differentiation** |
| `build_render_flow.render_remotion_project` | `remotion render` runs >1800s | `subprocess.TimeoutExpired` | N | uncaught | crash |
| `build_render_flow.package_render_output` | source video missing | none | partial | `copied_video=False` in payload | structured signal exists; producer must check it |
| `build_render_flow.ratify_render_package` | final/video.mp4 exists but is 0 bytes | size check exists? | depends | needs to verify in `ratify_render_package` (not read in this review) | likely caught by ffprobe duration check |
| `scripts/deepagents_video_maker.execute_pwsh` | non-Windows host | `RuntimeError` | Y | raised | "PowerShell 7 not found: ..." — but **tool not registered, never fires** |
| `scripts/deepagents_video_maker.patch_deepagents_path_validation` | DeepAgents internal API moved | `AttributeError` (silent via `getattr` → None) | **Y but SILENT** | `return` | no patch applied; Windows absolute paths break later with no diagnostic |
| `middleware.VideoMakerUiStateMiddleware.wrap_tool_call` | UI-state projection fails | broad `Exception` caught | Y | returns raw result | **silently drops UI state** — no log |

### Critical gaps (RESCUED=N AND silent)

1. **`controller.block_if_tool_call_dropout` covers only `source_intake`.** `controller.py:29`. Generalize to all four milestones with milestone-aware expected-artifact resolution. **Same gap as prior review #3; cost now 2× because scope doubled.**
2. **`session.init_video_session` overwrite without warning.** `session.py:33`. **Same gap as prior review #4.**
3. **`patch_deepagents_path_validation` silent no-op.** `scripts/deepagents_video_maker.py:167-185`. Delete (if `execute_pwsh` goes too) or log the failure path.
4. **State schema unversioned.** No migration helper for the rename from `research/script/assets/assembly` to `source_intake/script/build_scenes/render_package`. Existing sessions from before the rename are unreadable; any future rename has the same problem.
5. **Hand-rolled YAML silent corruption on adversarial topics.** `state_store.py:19-27,169-172`. Switching to PyYAML eliminates this entire class. PyYAML is already a paid dep.
6. **`build_render_flow._run_command` collapses error classes.** `build_render_flow.py:277-285`. Producer sees pass/fail only; cannot decide retry-with-install vs block-for-user.
7. **`render_remotion_project` 1800s timeout uncaught.** `build_render_flow.py:283`. `subprocess.TimeoutExpired` is not caught. Recommend catching and surfacing as a render failure with `failure_class=timeout`.
8. **`UnicodeDecodeError` on garbage script.md / source-manifest.md.** `ratify.py:29, 159`. Wrap with `errors="replace"` or surface as a ratify check failure rather than a crash.
9. **`middleware._attach_ui_state` silent except.** `middleware.py:40, 51, 62, 87`. Catch is correct (don't break tool call) but **add a debug log** so degraded UI state is observable.

Catch-all error handling is **not** present in `src/` (good). The bare `try/except Exception: pass` in `_websearch_items` (`source_flow.py:187`) cache-read is acceptable (legitimate fallthrough to refetch). The bare `except Exception:` in `_websearch_items` cache-write (`source_flow.py:240`) is a minor smell — failure to persist cache should at least debug-log.

---

## Section 3: Security & Threat Model

Local-only single-user tool. Surface unchanged from prior review except for the render subprocess pathway.

| Threat | Likelihood | Impact | Mitigated? |
|---|---|---|---|
| Path traversal via user-supplied `local_file=../../etc/passwd` | Low (single-user) | Med | Partial — `_ensure_under_project` exists in `scripts/deepagents_video_maker.py:102` for `cwd`, but **not** applied to `local_file` / `excalidraw_file` user inputs. |
| Prompt injection from `local_file` / source-manifest content | Med | Med-High | None. Scriptwriter reads the file and treats content as input. A poisoned PDF/markdown could redirect the script. |
| Prompt injection from Tavily web content via `note:` field | Med | Med-High | None. `_websearch_items` stores up to 2000 chars of `raw_content` into manifest `note:`. **Scriptwriter is instructed to treat manifest as authoritative.** A poisoned page could redirect script generation. **New attack surface since prior review** because the manifest now embeds 2000-char excerpts. Recommend: mark `note:` content as untrusted in the scriptwriter prompt; data_card_grounding regex on it; consider HTML/markdown stripping. |
| LLM-in-the-middle on Anthropic-compatible base URL | Low | High | None. `ANTHROPIC_BASE_URL` is honored without verification (`scripts/deepagents_video_maker.py:58`). |
| Secret leakage via `.env` accidentally committed | Med (universal) | High | `.gitignore` includes `.env` and `.env.local` ✅ |
| Web-UI bound to public interface | Low | High | LangGraph dev binds 127.0.0.1 by default. |
| Tavily API key exposed in process env | Low (local only) | Med | Standard env-var risk. `_tavily_api_key()` reads from env or `.env` file. |
| `execute_pwsh` shell injection | Low (not registered) | High *if registered* | Same as prior review. **Delete it.** |
| `render_remotion_project` runs arbitrary `pnpm exec` against subagent-generated `package.json` | Med (subagent-controlled) | High | None. A misbehaving Remotion Builder could write `package.json` scripts that get executed on `pnpm install`'s lifecycle hooks. **New threat surface.** Recommend disabling lifecycle scripts via `pnpm install --ignore-scripts` for the subagent-generated project. |

**Recommendations**

- **S1.** Path-confinement on `local_file` / `excalidraw_file` (unchanged from prior).
- **S2.** Mark scriptwriter prompt's manifest read as untrusted; data_card_grounding gate already partly handles fabrication risk.
- **S3.** Add `pnpm install --ignore-scripts` to `build_render_flow.render_remotion_project`. **Cheap fix, large defense-in-depth payoff.**
- **S4.** Delete `execute_pwsh`, `project_glob`, and (if not used in this branch) the patch.

---

## Section 4: Data Flow & Interaction Edge Cases

### Data flow: source_intake → script → build_scenes → render_package

```
  User prompt ──▶ vm_parse_video_request ──▶ parse_video_request
       │
       ▼
  vm_init_video_session ──▶ init_video_session ──▶ output_dir
       │              [collision? silent overwrite ← GAP]
       ▼
  vm_start_source_intake ──▶ create_milestone_run ──▶ run-1 dir
       │
       │ if source=websearch:
       │   vm_websearch ──▶ run_websearch_and_cache
       │     │                  └─▶ writes websearch-results.json cache
       │     │  [TAVILY_API_KEY missing? returns error_item — surfaced ✅]
       │     ▼
       │   producer sees status=ok|error, item_count
       ▼
  vm_ratify_source_intake ──▶ ratify_source_manifest
       │                       │
       │       [manifest has error items? ratify fails — surfaced ✅]
       │       [source-manifest.md is binary garbage? UnicodeDecodeError ← GAP]
       ▼
  vm_start_script ──▶ start_script_milestone (writes script-contract.json)
       │              [contract already exists? skips overwrite ✅]
       ▼
  vm_build_scriptwriter_task ──▶ task(scriptwriter)
       │              [tool-call dropout? NO PROTECTION ← GAP]
       ▼
  vm_ratify_script ──▶ ratify_script
       │                       │
       │       [data_card grounding regex on note: ← partial, language-form sensitive]
       │       [scene heading w/ trailing whitespace? silent miscount ← GAP]
       ▼
  Producer stops at script-review checkpoint
       │
       │ user approves
       ▼
  vm_start_build_scenes(script_approved=True)
       │              [no real interrupt; "approval" is producer politeness ← UX GAP]
       ▼
  vm_build_remotion_task ──▶ task(remotion-builder)
       │              [tool-call dropout? NO PROTECTION ← GAP]
       ▼
  vm_ratify_build_scenes ──▶ ratify_build_scenes (project_dir / package.json / src/index.ts)
       │
       ▼
  vm_start_render_package
       │
       ▼
  vm_render_remotion_project ──▶ subprocess: pnpm install + tsc + remotion render + still
       │              [pnpm not in PATH? crash ← GAP]
       │              [tsc fail vs network fail? same passed:false ← GAP]
       │              [>1800s? TimeoutExpired crash ← GAP]
       │              [subagent-written package.json with malicious lifecycle? RCE ← S3]
       ▼
  vm_package_render_output ──▶ copies to final/video.mp4 + final/thumbnail.jpg
       │
       ▼
  vm_ratify_render_package ──▶ ratify_render_package
       │
       ▼
  state.workflow_status = COMPLETED
       │
       ▼
  vm_build_publish_readiness_report (advisory)
```

Shadow paths summary:
- **Nil:** `prompt=None` and structured inputs all None → ValueError raised by `_goal_from_inputs`. Good.
- **Empty:** `topic=""` → "Untitled video" fallback. No warning.
- **Wrong type:** `quality_threshold="not-a-number"` → ValueError uncaught.
- **Upstream error:** Tavily 429 → producer sees `status: error` from `vm_websearch` ✅
- **Encoding edge:** Topic with mixed languages + embedded quotes → hand-rolled YAML unquoter mishandles. **Real risk** — same as prior review. Test it.
- **Subagent misbehaves:** Remotion Builder writes broken Remotion project → `ratify_build_scenes` catches missing `package.json` or `src/index.ts`, but doesn't catch e.g. `src/index.ts` with type errors (those surface later, in render).

### Interaction edge cases

| Interaction | Edge case | Handled? | How? |
|---|---|---|---|
| User issues retry after blocked | Producer re-enters milestone | Y | `vm_start_*` creates run-N+1 |
| User cancels mid-task | `task(subagent)` in-flight, no graceful cancel | N | DeepAgents owns this |
| User runs CLI twice in same second | Timestamp collision | **N — GAP** | A7 |
| Web UI session disconnects mid-stream | LangGraph dev resumes via thread_id | Likely Y | Untested |
| User supplies very long topic (>1KB) | Slug truncates to 30 chars | Y | `VideoMakerGoal.slug` |
| User supplies topic with only emoji | Slug returns "video" fallback | Y | `or "video"` guard |
| Concurrent write to state.yaml from two threads | Last writer wins | N — GAP | Single-user tool, low likelihood |
| User edits script.md between ratify passes | New ratify reads fresh file | Y | regex-based, no caching |
| User approves script but `script_approved=False` passed | `start_build_scenes_milestone` raises | Y | `RuntimeError` at `build_render_flow.py:57-61` |
| Remotion Builder writes `package.json` with malicious `postinstall` | `pnpm install` runs the hook | **N — S3** | New security gap |
| `pnpm install` succeeds but takes 25 minutes | `subprocess.run(timeout=1800)` → `TimeoutExpired` uncaught | **N — gap 7** | |

**Recommendation:** add tests for: (a) `init_video_session` collision (T-prev review #4), (b) topic round-trip with adversarial strings (T-prev #14), (c) `render_remotion_project` with `command_runner` injection returning timeout / network error / tsc error, asserting failure-class differentiation. The `command_runner` injection point already exists (`build_render_flow.py:178`) — good engineering, just no tests using it.

---

## Section 5: Code Quality Review

**Strengths**
- Package boundary remains clean. Module names match responsibilities. No circular imports.
- Typed-tool naming consistent (start_X, build_X_task, ratify_X). Pleasant to read.
- 87 tests for 2,872 LOC src/ is healthy; ratify gates have negative tests.
- `RatifyCheck`/`RatifyResult` continues to be the right abstraction.
- `ui_state.py` + `middleware.py` is a clean separation between domain state and UI projection.
- `script_flow.start_script_milestone` correctly avoids overwriting an existing contract (`script_flow.py:36-38`). Small change, big correctness win — addresses one of the recently-fixed PR findings.

**Issues**

- **Q1. DRY violation: `_to_virtual_path` still duplicated 2×.** `script_flow.py:90` (the one `build_render_flow.py` imports) and `scripts/deepagents_video_maker.py:141` (Windows-extended-prefix-aware variant). The two implementations differ in handling — one is for runtime tasks-description text, the other is for fixing DeepAgents path validation. Pull into a single `paths.py` with one `to_virtual_path(path, *, windows_aware=False)` API. Half-hour fix. (Improved from prior review's 3× to 2×, still worth closing.)
- **Q2. DRY violation: 11-kwarg fan-out across 4 typed tools.** `langchain_tools.py:50-220` and elsewhere. **Same critique as prior review Q2.** Net cost grew because more tools followed the pattern.
- **Q3. Naming inconsistency: `local_file` (Python underscore) vs `local-file` (Literal hyphen).** Same as prior review Q3. Look for `replace("_", "-")` translations sprinkled in `_goal_from_inputs`.
- **Q4. Over-engineering: `tools.py` still a placeholder.** `src/deepagents_video_maker/tools.py` (30 LOC) — re-exports. Either inline into `__init__.py` or delete.
- **Q5. Under-engineering: producer.md hard-rules are prose, not assertions.** Identical to prior review Q5. The dropout gap (Section 1 A3) is the concrete instantiation.
- **Q6. Cyclomatic complexity.** Two functions exceed comfort:
  - `ratify.ratify_script` is ~140 LOC, single function, multiple early-returns and inline conditionals. Decompose into per-check helpers (e.g. `_check_scene_canonical_fields`, `_check_data_card_grounding`).
  - `build_render_flow.render_remotion_project` is ~70 LOC and the failure-class differentiation will only grow.
- **Q7. Comment hygiene.** `prompts/producer.md` is bilingual Chinese-English. SKILL.md is English. The mix is intentional (Chinese is the team's working language) but the convention should be documented somewhere — otherwise an English-only contributor will silently rewrite or mistranslate Chinese-language hard rules.
- **Q8. Dead code STILL present.** `scripts/deepagents_video_maker.execute_pwsh`, `project_glob`, `patch_deepagents_path_validation` — 6 months running, never registered. **Delete.** Carried forward from prior review.
- **Q9. New: `state_store.py` carries a stale module docstring.** Line 1-5: "Minimal YAML writers for Phase 1 state files. … A full YAML parser can be introduced later if needed." PyYAML is now in deps. The docstring is a fossil; update or remove when migrating.

---

## Section 6: Test Review

### What this branch / recent commits introduce

| Surface | New |
|---|---|
| UX flows | Golden playable smoke (end-to-end MP4 via ffmpeg) |
| Data flows | Source-manifest write/ratify (new), build_scenes ratify (new), render_package ratify (new), publish-readiness JSON+MD (new) |
| Codepaths | `build_render_flow.py` end-to-end; `source_flow.run_websearch_and_cache` |
| Background jobs | None |
| External integrations | Tavily websearch deepened (advanced search depth, 2000-char snippet, caching) |
| Error/rescue paths | data_card_grounding ratify (new), contract overwrite guard (new) |

### Coverage assessment

17 test files, 87 tests collected (86 pass; 1 environment-conditional). Test ambition: **better than prior review.**

Strong coverage:
- `test_ratify_script.py` (12 tests) — including data_card grounding, canonical fields, max-consecutive-same-type.
- `test_script_flow.py` (10 tests).
- `test_skill_files.py` (8 tests) — keeps skill MD files honest.
- `test_state_store.py` (5 tests).
- `test_golden_demo_smoke.py` — end-to-end smoke promoted to pytest. **This is the prior review's T1, now delivered.** Significant win.

Still missing (carried from prior review):
- **T2. Tool-call dropout detection on script / build_scenes / render_package.** `test_tool_call_dropout_detection.py` covers only source_intake (3 tests). Need symmetric coverage.
- **T3. Goal-yaml round-trip with adversarial topics.** Topics with `"`, `\`, multi-line, full-Chinese-with-embedded-English-and-quote. The hand-rolled YAML *will* fail several; this test would force the PyYAML migration.
- **T4. Session-init collision test.** Two `init_video_session` with same timestamp.
- **T5. Ratify regex edge cases.** Scene heading trailing whitespace; `type:` inside fenced code block; data_card grounding with non-ASCII numeric form (`三十亿` vs `30亿`).
- **T6. Web-UI CI: still no Node test gate.**
- **T7. New: `render_remotion_project` failure-class differentiation tests.** Inject `command_runner` returning network/tsc/timeout to validate the new failure-class proposal from A4.
- **T8. New: subprocess timeout test.** Assert `render_remotion_project` surfaces `failure_class=timeout` when underlying runner raises `TimeoutExpired`.

### Test pyramid

Many unit (good). Two integration smokes now in pytest (`test_golden_demo_smoke.py`) — significant improvement. Zero E2E against a real LLM — appropriate for CI (would be flaky and expensive).

### Flakiness risk

- `test_golden_playable_smoke_produces_probeable_mp4` requires `ffmpeg` on `PATH`. CI installs it; local without ffmpeg fails. Document this in `tests/deepagents_video_maker/test_golden_demo_smoke.py` or skip-with-reason via `pytest.skip("ffmpeg not on PATH")`. Otherwise developers hit a confusing red bar on first clone.

### Test ambition checks (per CEO mode)

- "Test that would make you confident shipping at 2am Friday": **delivered** in the form of `test_golden_demo_smoke.py` ✅.
- "Test a hostile QA engineer would write to break this": adversarial-topic round-trip (T3), subagent writing malicious `package.json` (T7), data_card with `三十亿` form (T5).
- "Chaos test": stub LLM emits `<sop_invocation>` text on script milestone (extension of T2); subprocess `command_runner` returns 137 (OOM kill) (T7).

---

## Section 7: Performance Review

LLM latency still dominates. Render subprocess is the new wildcard.

- **P1.** `params.parse_video_request` regex compile: still not cached. Negligible.
- **P2.** `ratify_script` reads `script.md` once. Fine.
- **P3.** `state_store.save_state_yaml` writes full file on every milestone update. <2KB. Fine.
- **P4.** `glob("run-*")` in `create_milestone_run` O(N). Negligible for N<10.
- **P5.** `_websearch_items` 2000-char `raw_content` truncation per result, max 8 results → max ~16KB per topic stored on disk. Reasonable.
- **P6.** **New: `pnpm install` on every render run is expensive (~30-120s).** `build_render_flow.render_remotion_project` accepts `install: bool = False` (`build_render_flow.py:177`), so callers can skip when warmed. **But the golden:playable script always installs.** For repeated dev iterations, caching `node_modules` per session is left to the user. Document.
- **P7.** **New: `remotion render` is the longest path component (minutes per run).** No mitigation needed for a dev tool; flagged for documentation.

**No issues blocking. Moving on.**

---

## Section 8: Observability & Debuggability Review

- **O1. Structured logging still missing.** Same critique as prior review. The producer dispatches, ratify decisions, milestone transitions, retry counter increments, subprocess invocations — none are logged. When `render_remotion_project` fails because pnpm is missing, the operator has to read truncated `stderr` from a JSON file to figure it out. **Add `logging` module setup; default INFO.**
- **O2. Ratify JSON files are still the only post-mortem audit trail.** Now richer (per-milestone JSON files: `source-intake.json`, `script-run-N.json`, `build-scenes.json`, `render-package.json`, `publish-readiness.json`). Good but unaggregated. A `vm_session_summary(output_dir)` helper that walks all ratify JSONs and produces a timeline is still high-leverage.
- **O3. UI state middleware is a positive step.** `VideoMakerUiStateMiddleware` projects `video_maker` UI state into the LangGraph top-level state — observability win. But silent-fall-through on projection failure (`middleware.py:40, 51, 62, 87`) means the UI may degrade silently in production. **Add debug log.**
- **O4. Web UI integration depth still opaque.** Same as prior review.
- **O5. No metrics or trace IDs.** Same as prior review. LangSmith integration is enabled by env var; document in README.
- **O6. Runbooks still missing.** Three runbooks would be high-leverage now:
  - `docs/runbooks/render-failure.md` — pnpm missing, tsc errors, remotion crash.
  - `docs/runbooks/script-blocked.md` — data_card_grounding rejection, scene count out of contract.
  - `docs/runbooks/tool-call-dropout.md` — same as prior review.

### Debuggability check (3 weeks later)

If a user reports "session XYZ failed at render" three weeks later:
- ✅ `state.yaml` shows final milestone status and blocking_reason.
- ✅ `ratify/render-package.json` shows what failed.
- ✅ `final/publish-readiness.md` is advisory but readable.
- ❌ No record of model, producer-prompt hash, deepagents version, or commit at run time.
- ❌ No record of pnpm / node / remotion / ffmpeg versions.
- ❌ No state_schema_version, so a future schema rename will produce an unreadable `state.yaml`.

**Recommendation:** add a `session-meta.yaml` (or extend `state.yaml`) capturing: `commit`, `state_schema_version`, `deepagents_version`, `langchain_version`, `node_version`, `pnpm_version`, `remotion_version`, `ffmpeg_version`, `producer_prompt_sha`, `model`. Cheap on disk, priceless for triage.

---

## Section 9: Deployment & Rollout Review

Library + CLI + dev-only web UI. No production deploy.

- **D1. Versioning.** `pyproject.toml:3` still `version = "0.1.0"`. No CHANGELOG, no release tags. **Same critique as prior review.**
- **D2. Dependency pins.** Same problem as prior review:
  - `deepagents>=0.5.3` — no upper bound. Pre-1.0; minor versions break.
  - `langchain>=0.3.0`, `langchain-core>=0.3.0`, `langchain-anthropic>=0.3.0`, `langchain-openai>=0.3.0` — same risk.
  - **New:** `langchain-community>=0.4.1`, `langchain-tavily>=0.2.18` — but `source_flow.py:200` imports `from tavily import TavilyClient` directly, so the `langchain-tavily` wrapper appears unused in `src/`. If true, delete it (was prior review #12, now in a different direction — *langchain-tavily* may be the one to drop, not `tavily-python`).
- **D3. Node lockfile.** `pnpm-lock.yaml` committed, `packageManager: pnpm@9.15.0` pinned. Good.
- **D4. CI.** Added `ffmpeg` install in CI (`.github/workflows/ci.yml:24-26`). Good. Still missing: Node-side step (eslint + tsc) for web-ui.
- **D5. Migration safety.** `state.yaml` schema **changed** (milestone names) without a version field or migration. Any pre-rename `output/` is unreadable. This is the prior review's #9, *and a regression* — the schema change happened without a version field.
- **D6. Feature flags.** `eval_mode: gan|legacy|none` field exists. v2 SKILL.md explicitly disables GAN; the field is vestigial. Consider removing.
- **D7. Smoke tests post-deploy.** `--check` flag still exists. `pnpm golden:playable` is now the canonical post-deploy proof. Good. Document the install-ffmpeg prerequisite next to `pnpm golden:playable` in README.

---

## Section 10: Long-Term Trajectory Review

### Tech debt introduced or carried

- **L1. Hand-rolled YAML.** Still ~190 LOC of debt with PyYAML as paid dep. **Pay it down.**
- **L2. 11-kwarg fan-out, growing.** Now propagates to 5+ typed tools. Fix before adding audio/HITL milestones.
- **L3. Dead Windows-only code.** **Carried.** Delete.
- **L4. SKILL.md aspirational mismatch.** **Resolved.** ✅
- **L5. State schema unversioned.** **Worse than prior review** because the schema actually changed names without bumping a version. Add `state_schema_version` + migration helper.
- **L6. `controller.block_if_tool_call_dropout` covers only source_intake.** Same as prior review #6; cost doubled because pipeline doubled.
- **L7. No CHANGELOG, no release tag.** Carried.
- **L8. Reflexion lessons.** **Resolved** — explicitly removed from SKILL.md Do-not list. ✅
- **L9. New: `script-contract.json` is a de facto public contract without versioning.** Promote schema to `docs/`.
- **L10. New: Remotion Builder writes the renderable project — that contract (file layout under `out/`, `package.json` shape) is implicit.** Versioning it is the load-bearing handoff between Producer and Builder.
- **L11. New: `_run_command` failure classes.** Failure of network vs tsc vs timeout is indistinguishable today; retries will burn through.

### Reversibility ratings

| Decision | 1 (one-way) → 5 (reversible) |
|---|---|
| Controller-only architecture (no LangGraph DAG) | 3 — could add a thin LangGraph layer later |
| Subagent skill files in `.deepagents/skills/video-maker-v2-*` | 5 — paths can be moved |
| Hand-rolled YAML | 5 — swap to PyYAML, no caller breakage |
| script-contract.json as source of truth | 4 — could shift if versioned cleanly |
| Anthropic-as-default model | 5 — env var override |
| Producer prompt in bilingual Chinese-English | 4 — translatable |
| Milestone-name rename without state_schema_version | **2 — already done, already broke any pre-rename sessions** |
| 4-milestone pipeline shape | 3 — adding audio is straightforward; restructuring shape is not |

### Path dependency

Today's choices constraining tomorrow:
- `run-N` directory convention — locked-in by ratify regex; load-bearing for audio milestone too.
- `script-contract.json` schema — load-bearing for Scriptwriter + Remotion Builder. **Treat as public contract.**
- `source-manifest.md` markdown format — Scriptwriter's primary input. **Treat as public contract.**
- Remotion Builder's expected output layout (`remotion-project/{package.json,src/index.ts,out/{video,thumbnail}}`) — load-bearing for the build → render → package handoff.
- Producer.md controller-only stance — moving to LangGraph DAG later possible but invalidates SKILL.md.

### The 1-year question

A new engineer joining in 12 months and reading cold:
- ✅ README + CLAUDE.md + AGENTS.md + design docs + golden-demo.md = strong onboarding.
- ✅ SKILL.md aligned with code — much better than prior review.
- ❌ The 11-kwarg typed tools + bilingual prompt + dead Windows code remain confusing.
- ❌ The `controller.py` "only source_intake" gap is the kind of footgun that an onboarding engineer will trip over at 3am.

---

## Section 11: Design & UX Review

This review touches one user-visible UX surface: the **script-review checkpoint** (`SKILL.md` §3, `producer.md` rule #6).

Today's flow: Producer ratifies script → produces a chat message offering "Continue / Provide feedback / I edited / Stop." Then waits for user input. This is **producer politeness, not a real interrupt**.

Implications:
- ✅ Simple, no LangGraph interrupt machinery needed.
- ❌ A user who closes the browser tab and reopens has no clear "approve this script" UI; they must re-prompt Producer to continue.
- ❌ Web-UI streaming disconnects could be misread as "approval given" if the next user message is `continue`.
- ❌ `start_build_scenes_milestone` guards against `script_approved=False` (`build_render_flow.py:57-61`), but the gating is at the typed-tool layer — the model could still re-call with `script_approved=True` without real user input. **Audit the producer prompt for any path that allows `script_approved=True` without explicit user message.** Producer.md rule #7 is correct ("只有用户明确批准后") but it's prose; the model can interpret.

**Recommendation:** when audio/HITL Approach A lands, implement the script checkpoint as a real LangGraph `interrupt_on` boundary, not a prompt rule. The `interrupt_on` machinery already exists in `create_video_maker_agent` (`agent.py:79-86`) for `write_file`/`edit_file`; extend to a typed tool like `vm_request_script_approval`.

---

## Required Outputs

### NOT in scope

| Item | Why deferred |
|---|---|
| Audio milestone implementation | Designed in `references/audio-contract.md`, no Producer wiring |
| HITL approval as real interrupt | Currently producer politeness; flagged for next pass |
| GAN Evaluator + Layer 2 Reviewer | Explicitly disabled in SKILL.md Do-not list |
| Web-UI test suite | No Node test gate |
| Production deploy | Tool is dev-only by design |

### What already exists (and is reused)

| Sub-problem | File | Reused? |
|---|---|---|
| Milestone state machine | `models.MilestoneState`, `state_store.update_milestone_status` | ✅ |
| Run-N directory convention | `session.create_milestone_run` | ✅ |
| Artifact ratify pattern | `ratify.py`, `source_flow`, `script_flow`, `build_render_flow` | ✅ — extended to 4 milestones |
| Subagent prompt loading | `prompts.load_subagent_prompt` | ✅ (scriptwriter + remotion-builder) |
| DeepAgents progressive disclosure (`skills=`) | `agent.build_subagents` | ✅ |
| Tool-call dropout detection | `artifacts.detect_tool_call_dropout`, `controller.block_if_tool_call_dropout` | ✅ — source_intake only (still) |
| UI state middleware | `middleware.py`, `ui_state.py` | ✅ — net new, clean |
| Path virtualization | 2 implementations | ⚠️ duplicated (down from 3) |
| Websearch + cache | `source_flow.run_websearch_and_cache` | ✅ — first-class typed tool |
| Render subprocess + package + publish-readiness | `build_render_flow.py` | ✅ — net new |

### Dream state delta

This branch **does advance the runnable pipeline forward by two milestones** (build_scenes + render_package) and adds the golden playable smoke. That is a *real* progress commit, not a consolidation. The trade-off is that **none of the foundational debt from the prior review was paid down**, so the 4-milestone pipeline runs on the same scar tissue that protected the 2-milestone pipeline. The next reasonable step is foundational hardening (Approach B).

### Error & Rescue Registry

Consolidated table from Section 2. **Nine gaps total; seven critical (silent-failure paths):**

1. `controller.block_if_tool_call_dropout` — script, build_scenes, render_package uncovered. (CRITICAL, carryover)
2. `session.init_video_session` — silent output_dir overwrite. (CRITICAL, carryover)
3. `state_store.load_state_yaml` — no schema version; pre-rename sessions unreadable. (CRITICAL, **regression**)
4. `state_store.{save,load}_*_yaml` — silent corruption on adversarial topic strings. (CRITICAL, carryover)
5. `ratify.ratify_*` — `UnicodeDecodeError` on binary-garbage artifact files. (carryover)
6. `build_render_flow._run_command` — collapses transient and logic failures. (new)
7. `build_render_flow.render_remotion_project` — 1800s timeout uncaught. (new)
8. `scripts/.../patch_deepagents_path_validation` — silent no-op on API change. (carryover)
9. `middleware.VideoMakerUiStateMiddleware._attach_ui_state` — silent except. (new)

### Failure Modes Registry

| CODEPATH | FAILURE MODE | RESCUED? | TEST? | USER SEES? | LOGGED? |
|---|---|---|---|---|---|
| `block_if_tool_call_dropout` | script/build/render-milestone dropout | N | N | ratify error (wrong reason) | N — **CRITICAL** |
| `init_video_session` | output_dir collision | N | N | silent overwrite | N — **CRITICAL** |
| `load_state_yaml` | pre-rename milestone names | N | N | crash | N — **CRITICAL** |
| `load_state_yaml` | corrupt YAML from older writer | N | N | crash | N — gap |
| `ratify_script` / `ratify_source_manifest` | binary-garbage artifact | N | N | crash | N — gap |
| `params.parse_video_request` | non-numeric quality_threshold | N | N | crash | N — gap |
| `render_remotion_project` | pnpm not in PATH | N | N | crash | N — gap |
| `render_remotion_project` | tsc fail vs network fail | partial | N | passed:false (no class) | N — gap |
| `render_remotion_project` | timeout | N | N | crash | N — gap |
| `_attach_ui_state` | UI state projection fails | Y | N | degraded UI | **N — should log** |

**Critical gaps total: 7.** All have small, well-scoped fixes.

### TODOS proposed (would normally be one `AskUserQuestion` each)

Priority is anchored to the prior review's framing — *foundational hardening first*. Items marked with **[carryover]** were P1/P2 in the prior review and remain unaddressed.

| # | Title | Priority | Effort (CC) | Why |
|---|---|---|---|---|
| 1 | **Generalize `block_if_tool_call_dropout` to all 4 milestones** [carryover] | P1 | S | Symmetric coverage of the controller-only bet; cost grows linearly with milestones. |
| 2 | **PyYAML migration for `state_store`** [carryover] | P1 | S | Eliminates ~190 LOC of risk; PyYAML already a paid dep. Net code reduction. |
| 3 | **`state_schema_version` field + migration helper** [carryover, REGRESSION] | P1 | S | Milestone rename already broke pre-rename sessions; will recur on every schema change. |
| 4 | **Output-dir collision guard in `init_video_session`** [carryover] | P1 | S | Silent data loss path. |
| 5 | **Slim typed-tool kwargs surface** [carryover] | P1 | M | 11-kwarg fan-out, growing. goal.yaml as SoT, only `output_dir` + `run_number` on call sites. |
| 6 | **Add `--ignore-scripts` to `pnpm install` in render flow** [new, security] | P1 | XS | Defense-in-depth against subagent-written `package.json` lifecycle hooks. |
| 7 | **Classify failure classes in `_run_command` / `render_remotion_project`** [new] | P1 | M | Producer needs to differentiate retry-with-install vs block-for-user. Test via `command_runner` injection. |
| 8 | **End-to-end producer-protocol stub-model test** [carryover] | P1 | M | "Ship at 2am Friday" confidence. The golden:smoke covers typed-tools deterministically; need a stub-LLM E2E for controller protocol. |
| 9 | **Add structured logging foundation** [carryover] | P2 | S | Prerequisite for any further scope; render subprocess failures are unobservable today. |
| 10 | **Delete dead Windows-only code in `scripts/deepagents_video_maker.py`** [carryover] | P2 | XS | `execute_pwsh`, `project_glob`, `patch_deepagents_path_validation`. |
| 11 | **Consolidate `_to_virtual_path`** [carryover] | P2 | XS | 2× → 1×. |
| 12 | **Pin upper bounds on `deepagents`, `langchain*`** [carryover] | P2 | XS | Pre-1.0 SDKs break. |
| 13 | **Adversarial topic round-trip tests** [carryover] | P2 | S | Will fail today; PyYAML migration's payoff demo. |
| 14 | **Tool-call dropout tests for script/build/render milestones** [carryover→expanded] | P2 | S | Symmetric coverage for the controller-only bet. |
| 15 | **Promote contract surface to versioned `docs/`** [evolved] | P2 | S | `script-contract.json`, `source-manifest.md`, Remotion Builder output layout. |
| 16 | **Catch `subprocess.TimeoutExpired` in `render_remotion_project`** [new] | P2 | XS | Surface as `failure_class=timeout` instead of crashing. |
| 17 | **`session-meta.yaml` capturing commit/version/tooling stamps** [evolved] | P2 | S | Triage support; eats 200 bytes per session. |
| 18 | **Two runbooks: render-failure, script-blocked** [carryover→reshaped] | P3 | S | High-leverage debuggability. |
| 19 | **Wrap ratify `read_text` with `errors="replace"` or explicit ratify check** [carryover] | P3 | XS | Avoid `UnicodeDecodeError` crashes. |
| 20 | **`vm_session_summary(output_dir)` helper** [carryover] | P3 | S | Walks `ratify/*.json` → timeline. |
| 21 | **CHANGELOG.md + tag v0.1.0** [carryover] | P3 | XS | First external user filing an issue will need it. |
| 22 | **Path-confinement check on `local_file` / `excalidraw_file`** [carryover] | P3 | S | Defense-in-depth. |
| 23 | **Web-UI CI step: `eslint` + `tsc --noEmit`** [carryover] | P3 | XS | Web-UI is in the repo; treat it like one. |
| 24 | **Mark Tavily `note:` content as untrusted in scriptwriter prompt** [new] | P3 | XS | Defense against prompt injection from web sources. |
| 25 | **Promote script-checkpoint to real LangGraph `interrupt_on`** [new] | P3 | M | Required when HITL/audio lands; defer until then. |
| 26 | **Decide & remove `eval_mode` field** [new] | P3 | XS | Vestigial — `eval_mode: gan` is explicitly disabled in SKILL.md Do-not. |
| 27 | **Drop unused `langchain-tavily` dep** [carryover, direction inverted] | P3 | XS | `src/` calls `tavily-python` directly; `langchain-tavily` is unused. |

### Diagrams produced

1. ✅ Component dependency graph (Section 1).
2. ✅ Source→Script→Build→Render data flow (Section 4).

### Diagrams missing (to add when next milestone lands)

- Milestone state-machine diagram (4 milestones, retry loops, blocked transitions, script-review checkpoint).
- Render subprocess pipeline diagram (pnpm install → tsc → remotion render → still → ffprobe).
- Remotion Builder dispatch sequence.

### Stale diagram audit

No ASCII diagrams currently live in source files. No stale diagrams to flag.

---

## Outside Voice (skipped)

Skill recommends a different-model second opinion. Not invoked here (single-pass written review per user request). If the team wants this, run `/codex-review` or pipe this report to GPT-5 / Gemini and ask "what did this miss?"

---

## Completion Summary

```
+========================================================================+
|        CEO PLAN REVIEW — COMPLETION SUMMARY (deepagents-video-maker)   |
+========================================================================+
| Mode selected         | HOLD SCOPE (recommend Approach B then C then A)|
| System Audit          | Pipeline complete; foundational debt unpaid    |
| Step 0                | 20-of-20 prior TODOs: ~3 done, ~17 carryover   |
| Section 1  (Arch)     | 8 issues found (A1-A8); A1 resolved            |
| Section 2  (Errors)   | 23 paths mapped, 9 gaps, 7 CRITICAL            |
| Section 3  (Security) | 6 issues; 1 new (pnpm scripts), 1 new (manifest)|
| Section 4  (Data/UX)  | 10 edge cases; 4 unhandled                     |
| Section 5  (Quality)  | 9 issues (Q1-Q9); 1 new (state_store docstring)|
| Section 6  (Tests)    | T1 delivered (golden smoke); T2-T8 outstanding |
| Section 7  (Perf)     | 0 blockers (LLM + render subprocess bound)     |
| Section 8  (Observ)   | 6 gaps; UI middleware net positive             |
| Section 9  (Deploy)   | 7 risks; ffmpeg-in-CI win; D5 regressed        |
| Section 10 (Future)   | Reversibility avg 4.0/5; 11 debt items         |
| Section 11 (Design)   | Script-checkpoint is politeness, not interrupt |
+------------------------------------------------------------------------+
| NOT in scope          | 5 items                                        |
| What already exists   | 10 items mapped, 1 duplicated 2x               |
| Dream state delta     | pipeline axis: forward; foundation axis: flat  |
| Error/rescue registry | 23 methods, 7 CRITICAL gaps                    |
| Failure modes         | 10 entries, 3 CRITICAL                         |
| TODOS proposed        | 27 items (17 carryover, 10 new)                |
| Scope proposals       | 0 (HOLD SCOPE)                                 |
| CEO plan persisted    | this file                                      |
| Outside voice         | skipped                                        |
| Diagrams produced     | 2 (component graph, end-to-end data flow)      |
| Stale diagrams found  | 0                                              |
| Unresolved decisions  | 2 (see below)                                  |
+========================================================================+
```

### Unresolved decisions (require user input)

1. **Foundational hardening before audio/HITL: Y/N?** The prior review recommended B+C before A; the team chose A and completed it. The recommendation now is **B (hardening) → C (contract versioning) → A (audio or HITL)**. Sequence matters: the dropout-detection gap, state-schema unversioned, hand-rolled YAML, and pnpm-lifecycle security all compound when audio lands. Block on this decision before scope expansion.
2. **Is `script-contract.json` (and `source-manifest.md`) a versioned public contract or an internal artifact?** Every additional consumer (audio, future renderer, evaluator) makes the answer more expensive to defer. The technical answer is "public" because Remotion Builder is already a consumer and the audio milestone would be another. Recommend committing to a versioned schema this quarter.

---

## Verdict

**This is a small, well-tested, principled codebase that has successfully shipped its end-to-end product loop in the six days since the last CEO review.** The pipeline now produces a real, probeable MP4 from a topic and source folder, with deterministic golden smokes covering the full path. The architectural bet (controller-only DeepAgents Producer + composition-first delegation to Remotion Builder) is paying off — the previous SKILL.md aspirational-vs-operational gap is gone, the milestones are aligned with the runnable code, and the UI state middleware gives the web-UI a clean projection.

**However, the team chose to push the pipeline forward before paying down the foundational debt the prior review flagged.** Seventeen of twenty prior TODOs are carryovers. **Seven critical silent-failure gaps remain — the same six as before plus one new (state_schema_version regression).** The controller-only bet now has 4× the surface area but the same 1× of dropout protection. The hand-rolled YAML continues to be a paid-but-unused dep. The new render subprocess introduces fresh security and observability gaps (pnpm lifecycle scripts; unclassified failure modes; uncaught timeout).

**Twenty-seven TODOs are written down with priority and effort; nothing on the list is XL.** Six are P1 and small; close them first.

The biggest strategic question is **whether to land audio or HITL next, or to first generalize the dropout safety net and version the contract surface.** This review recommends **B (hardening) → C (contract versioning) → A (audio or HITL)** in that order, with item #1 (dropout generalization) and item #3 (state_schema_version) as the load-bearing pre-requisites for any further scope.

**Engineering preference compliance:** DRY violations remain (path virtualization 2×, kwargs fan-out across 5+ tools) — flagged. Tests improved meaningfully (golden:playable end-to-end smoke is a real win). Observability is still the weakest dimension — structured logging is now overdue, render-subprocess failure classes are unobservable, and there is no per-run metadata stamp. Security posture is appropriate for a single-user dev tool, but the new subagent-writes-package.json pathway needs `--ignore-scripts` as a one-line fix.

**Recommended next steps in order:**
1. Decide foundational-hardening sequence (block on this).
2. Close the 4 highest-leverage critical gaps (TODOs 1, 2, 3, 4). ~1 day with CC.
3. Add `--ignore-scripts`, classify render failure classes, catch render timeout (TODOs 6, 7, 16). ~1 day.
4. Slim typed-tool surface + structured logging (TODOs 5, 9). ~1 day.
5. Stub-LLM E2E test + dropout coverage for script/build/render (TODOs 8, 14). ~1 day.
6. Promote contract surface to versioned `docs/` (TODO 15). Half a day.
7. *Then* choose Approach A: audio milestone, or HITL interrupt.

— end of review —
