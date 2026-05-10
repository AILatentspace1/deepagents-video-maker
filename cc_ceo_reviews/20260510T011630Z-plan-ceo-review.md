# CEO Review — deepagents-video-maker (follow-up)

- **Date:** 2026-05-10 01:16:30 UTC
- **Branch:** `claude/gracious-gates-Ykdlf`
- **HEAD:** `9380e5d` (`feat(skill): implement Stage 1 plan for video-maker skill with detailed task breakdown and acceptance criteria`)
- **Reviewer skill:** `gstack/plan-ceo-review` (https://github.com/garrytan/gstack), invoked here as a written review (no AskUserQuestion ceremony) because the skill is not installed locally and the user requested a written deliverable. CEO posture, mode selection, 11-section framework, and required outputs are preserved.
- **Anchor:** prior review `cc_ceo_reviews/20260509T012631Z-plan-ceo-review.md` at HEAD `fbc0074`. Today's review is a *follow-up*: it tracks closure on the 20 TODOs from yesterday, audits new surfaces, and re-grades the project on the same 11 sections.
- **Mode selected:** **HOLD SCOPE** — but the *stated* scope changed materially in 24 hours, and the team has *also* drafted a Stage-1 spec to deprecate the v2 skill in favor of an entirely different web-recording route. This review treats the v2 pipeline as the scope-of-record and flags the pivot as the dominant strategic decision.
- **Posture:** Rigorous reviewer. Zero silent failures. Every error has a name. Diagrams mandatory. Permission #9 invoked where the v1→v2 rename and the v2→web pivot warrant a written trip-wire.

---

## 0. Pre-Review System Audit

### Repository state at `9380e5d`
- Working tree clean. Branch `claude/gracious-gates-Ykdlf` is one commit ahead of the prior review HEAD on this branch, but the diff vs. `fbc0074` is **+14,892 / −4,511** across 179 files. A single commit message belies a major refactor merged in.
- **Source code:** 19 Python files in `src/deepagents_video_maker/` totaling ~2,872 LOC (was ~1,700 — **+69%**). New modules: `build_render_flow.py` (514 LOC), `middleware.py` (115 LOC), `source_flow.py` (293 LOC), `ui_state.py` (140 LOC). Removed: `research_flow.py` (replaced by source_flow.py).
- **Tests:** 17 files / ~1,300 LOC under `tests/deepagents_video_maker/` and a new 11-file / ~1,400 LOC `tests/evals/` tree (train / holdout / scorecard tiers). Total test LOC ~2,691.
- **Test results today:**
  - `uv run pytest tests/deepagents_video_maker --tb=no` → **86 passed, 1 failed**. The single failure is `test_golden_playable_smoke_produces_probeable_mp4`, which `SystemExit`s when `ffmpeg` is missing (this is the local container; CI installs ffmpeg per `93bf38a`). **Not a regression**, but the test should `skip` rather than `SystemExit` when ffmpeg is absent — it's a hard-fail dressed as an environment skip, which is a small honesty bug.
  - `uv run pytest tests/evals` → **5 collection errors**. All five fail with `ImportError: cannot import name 'vm_ratify_research'/'vm_start_research'/'vm_build_researcher_task' from deepagents_video_maker.langchain_tools`. The `evals/` tree was committed under v1 names and was never renamed when the v1 → v2 rename landed. **The eval harness is broken at HEAD.** This is the single highest-priority finding of this review.
- **Pipeline rename:** `session.DEFAULT_MILESTONES` is now `("source_intake", "script", "build_scenes", "render_package")`. The v1 `("research", "script", "assets", "assembly")` four-tuple is gone. The web-UI timeline component lists *five* milestones (adds `publish_readiness`) — a small drift between the Python source-of-truth and the React component.
- **Skill tree:** `skills/video-maker/` (legacy) is deleted. `skills/video-maker-v2/` is now operational with `SKILL.md`, `agents/{scriptwriter, remotion-builder, scene-batch-generator, scene-patch-generator}.md`, four `ratify/*-rules.md`, eight `references/*.md`, and seven `scripts/*.{py,mjs}`.
- **Strategic pivot (drafted, not executed):** `specs/video-maker-web-port/stage-1-skill/{requirements.md, design.md, tasks.md}` lays out a **Stage-1 plan to delete `skills/video-maker-v2/` entirely** in favor of a Vite + React + Playwright auto-record skill (`skills/video-maker/` reborn). The corresponding `specs/video-maker-v2-harness-upgrade/{requirements,design}.deprecated.md` files have been renamed to `.deprecated.md`. **The v2 work this review is grading may be discarded within weeks.**

### What's already in flight
- v2 pipeline (source_intake → script → build_scenes → render_package) is wired end-to-end. `vm_render_remotion_project` shells out to `pnpm` + `ffmpeg`. Determinism via `tests/fixtures/golden_demo_*` is testable through `pnpm golden:script`, `pnpm golden:render`, `pnpm golden:playable`.
- 17 typed tools registered (was 9) — full tool list in §1.
- `VideoMakerUiStateMiddleware` projects every tool call into the LangGraph thread state for the web-UI; `web-ui/src/app/components/VideoProductionTimeline.tsx` consumes it.
- Better-harness scriptwriter optimization config exists at `harness/video-maker-minimal.toml`. The Stage-1 web-port spec (T0.1–T0.7) proposes deleting the entire `harness/` directory.

### Recently touched files (signal)
17 commits since `fbc0074`. Three themes:
1. **v1 → v2 rename + Remotion/render integration** (`9380e5d`, `26975a7`, `82cf0c5`, `0e2b75f`).
2. **Web-UI timeline + UI-state middleware** (`17c032e`, `0b6f3f7`, `7b61660`).
3. **CI hardening + Windows path normalization** (`93bf38a`, `e985ec8`, `6a49197`).

The team is shipping fast and pushing scope forward. **This is the opposite of yesterday's M1-hardening branch.** That changes the appropriate CEO posture: yesterday I recommended HOLD SCOPE + Approach C (harden first); today the team picked Approach A (push scope) without the hardening pass. That decision is reviewable on its merits in §10.

---

## Step 0: Premise Challenge + Mode Selection

### 0A. Premise Challenge — is this the right problem?

> "DeepAgents-native Producer with progressive-disclosure skills drives source_intake → script → build_scenes → render_package. Remotion is the rendering substrate. Final output is a playable MP4."

Three premises worth challenging directly:

1. **"Remotion is the rendering substrate."** The Stage-1 web-port spec (`specs/video-maker-web-port/stage-1-skill/requirements.md`) proposes pivoting to a *Vite + React + Playwright* recording approach and explicitly marks v2 as *deprecated*. The CEO question writes itself: **the team is grading two horses while sprinting on one.** If the web-port is the real plan, every commit in the last 24 hours is sunk-cost work that depreciates the moment Stage-1 lands. If the web-port is exploratory, the spec needs an explicit "DECISION PENDING" block at the top so contributors don't think v2 is doomed. **Recommendation:** the team writes a one-page "rendering-substrate decision" doc this week — Remotion vs. web-recording — with explicit kill criteria for the loser. Don't run both half-funded.

2. **"source_intake replaces research."** The rename is more than cosmetic. v1 had an LLM-driven researcher subagent that produced `research.md` from web search. v2 has *no researcher subagent* — the producer itself orchestrates `vm_websearch` + `vm_ratify_source_intake` to produce `source-manifest.md` (a list of sources with metadata, not synthesized prose). This is a **smaller-scope, less-LLM-touch design** — and it's defensible: it pushes the synthesis down into the scriptwriter where it's already happening. But it means the v1 eval harness in `tests/evals/` (which tested `vm_ratify_research`) is now load-bearing dead code. Either rename and re-land those tests, or delete them.

3. **"Controller-only DeepAgents Producer scales to 4 milestones."** Yesterday I set a trip-wire: *if the assets milestone introduces 3+ new pseudo-tool-call failure modes, add a thin LangGraph layer for milestone transitions.* In the 24 hours since, the team added **two** new milestones (`build_scenes`, `render_package`), each with 3+ typed tools and one with an LLM-driven Remotion-builder subagent. The producer prompt (`prompts/producer.md`) now enforces an 11-step controller protocol with explicit "real `task(subagent_type=...)` only — no pseudo invocations" guards. **The trip-wire was crossed.** `controller.block_if_tool_call_dropout` was generalized to all milestones (good) — but the prompt-level discipline burden has compounded, and there is no end-to-end test that exercises a real LLM against the 11-step protocol. The bet still holds *operationally* (the deterministic golden smoke tests pass), but it has not been falsified by a stub-model adversarial run. **This is the same critical-test gap I flagged yesterday, now at higher stakes.**

**Verdict on premises:** problem framing for v2 is internally consistent and the source_intake rename is a real improvement. The strategic premise (Remotion vs. web-recording) is undecided and the project is paying both bills. The architectural premise (controller-only at 4 milestones) is unproven by adversarial testing.

### 0B. Existing Code Leverage

| Sub-problem | Existing code (HEAD) | Reused / Drift |
|---|---|---|
| Milestone state machine | `models.MilestoneState` + `state_store.update_milestone_status` | ✅ reused |
| Artifact gate validation | `ratify.{ratify_source_manifest, ratify_script}`, `build_render_flow.{ratify_build_scenes, ratify_render_package}` | ✅ pattern preserved across 4 ratify points |
| Tool-call dropout detection | `artifacts.detect_tool_call_dropout` + `controller.block_if_tool_call_dropout` | ✅ now generalized (was research-only) |
| Subagent skill loading | `agent.build_subagents` | ✅ reused; subagent list rotated to `[scriptwriter, remotion-builder]` |
| Path virtualization | `script_flow._to_virtual_path`, imported by `build_render_flow` | ✅ deduplicated (was 3×); `scripts/deepagents_video_maker.to_virtual_path` still has its own copy though — **drift remains** |
| Goal parsing | `params.parse_video_request` | ✅ reused |
| YAML I/O | Hand-rolled `state_store.save_*/load_*` | ❌ **PyYAML now in deps but unused** — yesterday's TODO #1 not closed |
| UI-state projection (NEW) | `ui_state.build_video_maker_ui_state` + `middleware.VideoMakerUiStateMiddleware` | ✅ new, consumed by web-UI; clean separation |

The **single biggest leverage win** of the last 24 hours is `VideoMakerUiStateMiddleware`. It cleanly separates "what the producer is doing" from "what the web-UI shows" without requiring tools to know about the UI. That's a piece of architecture I did not flag yesterday and which I would call out as the strongest design move on this branch.

### 0C. Dream-State Mapping

```
  YESTERDAY (fbc0074)              TODAY (9380e5d)              12-MONTH IDEAL
  ───────────────────              ──────────────────           ──────────────
  research → script                source_intake →              full pipeline
  runnable.                        script →                     including audio,
                                   build_scenes →               style-direction,
  Assets/assembly:                 render_package               HITL approval,
  declared, not                    runnable end-to-end          GAN evaluator,
  implemented.                     (deterministic smoke).       reviewer subagent.

  68 tests green.                  86 main tests pass + 1       Eval harness
                                   ffmpeg-related fail; 5       extended to all
  Web-UI streams                   tests/evals collection       milestones with
  research+script.                 ERRORS (broken at HEAD).     adversarial topics.

  Quality:                         Web-UI now has               Quality:
  Layer-1 regex ratify.            VideoProductionTimeline      Layer-1 ratify +
                                   driven by middleware-        Layer-2 reviewer +
  Observability:                   projected state. Solid.      GAN contract loop.
  print + ratify JSONs.
                                   Quality: Layer-1 only.       Observability:
                                   No reviewer/evaluator/       structured logs,
                                   editor wired despite         session trace IDs,
                                   prompts on disk.             eval dashboard.

                                   Strategic pivot to           Substrate decision
                                   web-recording route          made; one route
                                   drafted (specs/.../          owned and shipped.
                                   stage-1-skill/).             Aspirational hooks
                                                                deleted, not
                                                                lingering.
```

The branch under review has **moved the pipeline forward by two milestones** and built a real UI surface. That is substantial progress vs. yesterday's documentation-only branch. The cost: the prior review's 20 TODOs were largely *not* closed (see §0D table), the eval harness was broken, and a strategic pivot was drafted in parallel without an explicit kill criterion for v2.

### 0C-bis. Implementation Alternatives

The dominant decision today is no longer "what to build next" — it's "**which substrate do we ship?**" The three plausible shapes:

```
APPROACH A: Commit to v2 Remotion route, delete the web-port spec.
  Summary: Treat the Stage-1 web-port spec as exploration. Continue
           hardening v2: close the 14 prior TODOs that remain open,
           re-land the eval harness with v2 names, harden Remotion render
           against ffmpeg/pnpm failure modes, ship v0.2 with a full pipeline.
  Effort:  M (1-2 weeks human; 3-5 days with CC).
  Risk:    Med — Remotion learning curve and per-scene loop still ahead;
           the v2 pipeline does work for the deterministic golden case.
  Pros:    - Recovers the 24-hour investment in v2.
           - The middleware/timeline UI is genuinely good and re-usable.
           - Remotion gives pixel-perfect motion control that web-recording
             cannot match.
  Cons:    - The Stage-1 web-port doc cites real complexity savings that
             this approach forfeits.
           - Per-scene asset generation (TTS/Whisper/image-gen) is still
             unimplemented and is the hard part.

APPROACH B: Commit to web-port, deprecate v2.
  Summary: Execute the Stage-1 web-port plan: delete harness/, scripts/run-
           harness.ps1, runs/, tag v2 [DEPRECATED], build the new skill.
  Effort:  XL (5-7 weeks per the spec).
  Risk:    Med-High — methodology is borrowed from web-video-presentation
           but every artifact is being re-written; the spec acknowledges
           this is a long path.
  Pros:    - One substrate, no fork-in-the-road for new contributors.
           - Web-recording skill is portable to non-DeepAgents users
             (Claude Code / Cursor / Codex); v2 is DeepAgents-locked.
           - Simpler asset pipeline (HTML/CSS instead of Remotion JSX).
  Cons:    - Discards the v2 work shipped today.
           - Web-recording can't match Remotion's animation precision.
           - Stage 2 (DeepAgents integration) is itself another XL.

APPROACH C: Run both for one decision sprint, then kill one.
  Summary: Time-box 5 working days. Hardening pass on v2 (close P1 TODOs,
           re-land eval harness). In parallel, prototype Stage-1 web-port
           T0+T1 only (delete harness, scaffold skill). After 5 days,
           decide based on which proved itself faster: end-to-end deter-
           ministic v2 render of golden topic, or end-to-end Playwright
           recording of a 3-step demo.
  Effort:  M (5 days, 2 tracks).
  Risk:    Low if disciplined; high if discipline slips.
  Pros:    - Forces a decision instead of running both half-funded forever.
           - Both tracks produce a tangible artifact in the timeframe.
           - Either way, the prior-review TODOs get closed in track 1.
  Cons:    - Splits attention for a week.

RECOMMENDATION: C, with a sharp definition of "decided."
  WHY: The team is currently paying for both substrates without committing
  to either. The 24 hours of work on v2 is real value that should not be
  thrown away on a hunch. The Stage-1 spec is a real proposal that
  shouldn't be left dangling. Five days is enough to learn what's needed
  to choose. The decision criterion: which substrate produces a finished
  60-second demo from one topic in fewer human-hours of intervention?
```

### 0D. Mode-Specific Analysis (HOLD SCOPE)

**Status of the prior review's 20 TODOs.** Audited at HEAD `9380e5d`:

| # | Title (yesterday) | Status today | Evidence |
|---|---|---|---|
| 1 | PyYAML migration | **Not done** | `state_store.py` still hand-rolled (`_scalar`, `_quote`/unquote logic at L19-L27); `PyYAML>=6.0` added to pyproject but no `import yaml` anywhere |
| 2 | Surface Tavily absence | **Partially done** | `source_flow.py:191` returns a structured error item if `TAVILY_API_KEY` is unset; `except Exception` at L207 catches `ImportError` from `from tavily import TavilyClient` and converts to a visible error item. Producer now sees a named error. **Win**, though the failure is still phrased as "websearch failed: <exc>" rather than naming the specific class. |
| 3 | Generalize tool-call dropout to all milestones | **Done** | `controller.py:18-49` accepts `expected_artifact` parameter; default targets source_intake's manifest |
| 4 | Output-dir collision guard in `init_video_session` | **Not done** | `session.py:30` still `mkdir(parents=True, exist_ok=True)` — silent overwrite path remains |
| 5 | Reconcile SKILL.md aspirational scope | **Done** | `skills/video-maker/` deleted. `skills/video-maker-v2/SKILL.md` now matches the wired pipeline. **No `## Status` block, but the surface alignment removes the original ambiguity.** |
| 6 | Consolidate `_to_virtual_path` | **Partially done** | `build_render_flow.py:20` imports from `script_flow.py:90` (was duplicated). But `scripts/deepagents_video_maker.py:111` still has its own `to_virtual_path`. **2× now, was 3×.** |
| 7 | Slim 13-kwarg fan-out | **Not done** | `vm_init_video_session` (L50), `vm_ratify_source_intake` (L123), `vm_build_scriptwriter_task` (L188), `vm_ratify_script` (L233) all retain ~13-kwarg signatures |
| 8 | Delete dead Windows code | **Worse** | `scripts/deepagents_video_maker.py:225` now *calls* `patch_deepagents_path_validation()` at import time — code that was dead before is now reachable on every CLI invocation. `execute_pwsh` and `project_glob` still defined and `@tool`-decorated but not registered. **Net: regression.** |
| 9 | `state_schema_version` field | **Not done** | No version field on state.yaml |
| 10 | Structured logging | **Token effort** | `langchain_tools.py:454-455` — one `logging.exception("ui_state projection failed")` call. Nothing else uses logging. |
| 11 | Upper bound pins on deepagents/langchain | **Not done** | pyproject still uses bare `>=` for all SDK packages |
| 12 | Drop unused `tavily-python` | **Not done** | Both `tavily-python` and `langchain-tavily` still present; `source_flow.py` imports `from tavily import TavilyClient`, so it is `tavily-python` (not `langchain-tavily`) that is actually used. **`langchain-tavily` is the unused one** — yesterday's note was inverted. |
| 13 | E2E producer-protocol stub-model test | **Not done** | No test exercises cold-start → init → source → script → build → render against a model |
| 14 | Adversarial topic round-trip tests | **Not done** | No new test for embedded quotes / multi-line / Chinese topics |
| 15 | Promote `manifest-schema.md` to `docs/` | **Not done** | Still under `skills/video-maker-v2/references/`. `references/manifest-schema.md` (123 LOC, new content) replaces the v1 file. Not promoted to public-contract status. |
| 16 | Two runbooks (research-blocked, dropout) | **Not done** | `docs/runbooks/` does not exist |
| 17 | CHANGELOG.md + tag v0.1.0 | **Not done** | No CHANGELOG; no git tags |
| 18 | Path-confinement on `local_file`/`excalidraw_file` | **Not done** | `params.parse_video_request` still doesn't validate user-supplied paths |
| 19 | Reflexion read/write decision | **Done** (by deletion) | `skills/video-maker/reflexion/*.json` deleted along with v1 skill; no v2 reflexion folder. **Aspirational hook removed.** |
| 20 | Web-UI CI step (eslint + tsc) | **Not done** | `.github/workflows/ci.yml` adds 5 lines but they're for ffmpeg installation, not Node tests |

**Closure rate: 4/20 fully done (1 by removal), 3/20 partial, 13/20 not done.** Of the **6 critical silent-failure gaps** I flagged, only 2 closed (#3 dropout-generalization, partial #2 Tavily-surface). The other four (PyYAML, session collision, ratify UnicodeDecodeError, output-dir overwrite) are unchanged.

**This is the central tension of today's review:** the team chose *push scope* over *harden first*. That was their call to make and the v2 pipeline is real progress — but the technical debt from yesterday is now larger, not smaller, and the eval harness is broken at HEAD.

### 0E. NOT in Scope

Items I explicitly will not analyze in this review (carried from prior review unless noted):

- The full Stage-1 web-port spec (`specs/video-maker-web-port/stage-1-skill/`) — this is *strategic deliberation in progress*, not committed scope. I review it as context for §0A premise 1, not as live design.
- TTS / Whisper / image-gen per-scene loop — designed in audio-contract.md and look-and-feel-boundary.md, not yet wired. Same posture as yesterday: deferred.
- Reviewer / Editor / Evaluator / scene-batch / scene-patch subagents — prompts on disk, not registered (`SUBAGENT_NAMES = ["scriptwriter", "remotion-builder"]`). Same as yesterday's gap, narrower aspirational footprint.
- HITL approval flow inside the Producer (`AskUserQuestion`) — designed in producer.md step 6 as "stop and wait for user review," not implemented as an interactive flow.
- Web-UI E2E tests — Playwright is in `web-ui/package.json` for the web-port spec but no current tests run against the existing web-UI.

---

## Section 1: Architecture Review

### Component dependency graph (current, HEAD `9380e5d`)

```
                ┌────────────────────────────────────────────────┐
                │   User / Web UI (web-ui/agent/agent.py)        │
                │   Renders <VideoProductionTimeline/>           │
                └───────────────────────┬────────────────────────┘
                                        │ stream.values.video_maker
                                        ▼
        ┌───────────────────────────────────────────────────────┐
        │  create_video_maker_agent (agent.py:43)               │
        │  ├── tools: build_langchain_tools() — 17 typed tools  │
        │  ├── subagents: ["scriptwriter", "remotion-builder"]  │
        │  ├── system_prompt: prompts/producer.md (11-step      │
        │  │                  controller protocol)              │
        │  ├── middleware: [VideoMakerUiStateMiddleware()]      │
        │  └── backend: FilesystemBackend(virtual_mode=True)    │
        └───────────────┬───────────────────────────────────────┘
                        │
       ┌────────────────┼─────────────────────────────────────┐
       │                │                                     │
       ▼                ▼                                     ▼
   typed tools       producer.md hard-rules           subagent task()
   (source_flow,     (controller protocol             scriptwriter
    script_flow,     with anti-pseudo-                  → script.md
    build_render_    invocation guards)               remotion-builder
    flow,                                               → remotion-project/
    ratify,
    session,
    state_store)
       │                                                 │
       └────────────────────────┬────────────────────────┘
                                │
                 wrap_tool_call (middleware.py:30)
                                │
                                ▼
              ┌─────────────────────────────────────────┐
              │  Filesystem (output/<session>/)         │
              │   goal.yaml, state.yaml,                │
              │   artifacts/{source_intake,script,      │
              │     build_scenes,render_package}/run-N/ │
              │   ratify/{milestone}-run-N.json         │
              │   remotion-project/, final/video.mp4    │
              └─────────────────────────────────────────┘
                                │
                                ▼
              ui_state.build_video_maker_ui_state(output_dir)
              → state.values.video_maker (consumed by web-UI)
```

### Architecture findings

**A1 — Aspirational scope tightened, but not eliminated.** The v1 SKILL.md's per-scene-loop / GAN-evaluator / reviewer aspiration was excised when `skills/video-maker/` was deleted. The new v2 SKILL.md describes only what is wired, which is a real improvement. **However:** `agents/scene-batch-generator.md` and `agents/scene-patch-generator.md` exist on disk in the v2 skill but are not registered in `SUBAGENT_NAMES`. They reference per-scene `.tsx` patching that no tool dispatches. New contributors will assume these are operational. **Fix:** either delete or move to `references/future-agents/` until wired, OR add a single `## Status: experimental — not registered` note at the top of each.

**A2 — Coupling: kwargs-flooding was not addressed and now affects more tools.** Yesterday I flagged 4 tools with 13-kwarg fan-outs. Today there are still 4 such tools (one renamed: `vm_ratify_research` → `vm_ratify_source_intake`), plus a 5th (`vm_init_video_session` with 13 params at L50). The model has to remember the same `goal`-shaped parameter list across 5 different call sites. This is *worse* tool-call-correctness ergonomics, not better. **Recommendation unchanged:** consolidate goal-shaped fields into a single `VideoMakerGoal` arg or treat goal.yaml as the only source-of-truth and require only `output_dir` on call sites. The argument that "tests pass" is correct but does not measure the LLM's tool-call-emit error rate, which is the real metric.

**A3 — The controller-only bet has crossed its trip-wire.** Yesterday: "if assets introduces 3+ new pseudo-tool-call modes, add a thin LangGraph layer." Today: two new milestones (build_scenes, render_package), both requiring 3+ typed tools and one with a new subagent dispatch. The producer prompt grew from 2 milestones × ~4 rules to 4 milestones × 11 rules including explicit anti-`<sop_invocation>` / anti-pseudo-task-invocation language. **The bet is operationally still un-falsified** because the deterministic golden smoke tests don't run a model — they call the typed tools directly. **The trip-wire condition is met. The recommendation is now: design (not necessarily build) a thin LangGraph layer for milestone *transitions* that the producer cannot skip.** Keep progressive-disclosure inside each milestone. The transition layer can be 50 LOC and prevents the entire class of "model forgot to call vm_ratify_X" failures.

**A4 — Web-UI integration is now first-class and good.** `VideoMakerUiStateMiddleware` is the cleanest design move on this branch. It fault-tolerantly attaches `video_maker` state to every tool call without coupling tools to the UI. `VideoProductionTimeline.tsx` consumes the projected state with five hard-coded milestone IDs. The timeline component lists `publish_readiness` as a fifth milestone — but `session.DEFAULT_MILESTONES` lists only four. **Drift.** Either add `publish_readiness` to the canonical list (and to `state_store`/`ratify`) or remove it from the timeline. Pick one source of truth.

**A5 — Rollback posture is unchanged and still solid.** `output/<session>/` is git-ignored, no DB, no migrations. The new `remotion-project/` and `final/` artifacts live under the same session root, so rollback is still "delete the session folder." Reversibility 5/5.

**A6 — Scaling characteristics: still single-user, but Remotion render adds a new failure surface.** `vm_render_remotion_project` shells out to `pnpm` + `ffmpeg`. The render is synchronous and blocks the agent for the duration. For a 60-second 30fps video with 8 scenes, that can be 30-90 seconds of LLM-blocking. **No timeout.** A hung pnpm install or a Remotion compile error will hold the agent indefinitely. **Add a subprocess timeout** with a structured "render-timed-out" failure path.

**A7 — Subagent skill-folder pattern is consistent.** `.deepagents/skills/video-maker-v2-{scriptwriter,remotion-builder}/` mirrors `skills/video-maker-v2/agents/{name}.md`. Loading is via the existing `prompts.load_subagent_prompt` helper. Clean.

### Required architecture diagrams produced
1. ✅ Updated component dependency graph (above).

### Diagrams missing (still owed)
- Milestone state-machine with retry / blocked transitions (now 4 milestones × retry × blocked = 12 states).
- Render subprocess timing diagram (pnpm install → remotion-cli render → ffmpeg encode → ratify probe).
- Web-UI streaming sequence (tool-call → middleware → state-projection → React rerender).

---

## Section 2: Error & Rescue Map

| METHOD/CODEPATH | WHAT CAN GO WRONG | EXCEPTION CLASS | RESCUED? | RESCUE ACTION | USER SEES |
|---|---|---|---|---|---|
| `agent.create_video_maker_agent` | DeepAgents not installed | `ImportError` → `RuntimeError` | Y | re-raise with named message | "DeepAgents runtime is required..." |
| `source_flow._run_websearch` | `TAVILY_API_KEY` missing | none | **Y, surfaced** | returns structured error item with named reason | manifest writes "websearch source intake requires TAVILY_API_KEY" — **WIN vs. yesterday** |
| `source_flow._run_websearch` | `tavily` package missing | `ImportError` | **Y, surfaced** | caught by `except Exception` and rendered as `"websearch failed: <exc>"` error item | producer sees the error string, not a silent low-quality output — **WIN** but error class name is hidden |
| `params.parse_video_request` | empty / unrecognized input | none | N | falls back to "Untitled video" | unchanged from yesterday — silent fallback |
| `params.parse_video_request` | `quality_threshold` not int | `ValueError` | N | uncaught | crash/500 — unchanged |
| `state_store.load_goal_yaml` | YAML with embedded quote/backslash mishandled by hand-rolled unquoter | `ValueError` or silent corruption | partial | only catches missing-topic; silent corruption path remains | unchanged from yesterday |
| `state_store.load_state_yaml` | malformed file from older writer | `ValueError` from `MilestoneStatus(value)` | N | uncaught | crash — unchanged |
| `session.init_video_session` | output_dir already exists | none | N | `mkdir(exist_ok=True)` silently overwrites | **silent data loss path remains** |
| `script_flow.start_script_milestone` | research not yet completed (now: source_intake not completed) | `RuntimeError` | Y | named error | "cannot start script milestone..." |
| `ratify.ratify_script` | regex misses scene with trailing whitespace in heading | none | N | silent miscount | unchanged |
| `controller.block_if_tool_call_dropout` | wrong `expected_artifact` provided | none | N | returns False, no diagnostic | dropout silently undetected — **NEW gap from generalization** |
| `build_render_flow.ratify_build_scenes` (NEW) | `remotion-project/package.json` exists but TypeScript imports are broken | none | N | only checks file existence | scene compiles fail at render time, not at ratify — **gap** |
| `build_render_flow.run_remotion_render` (NEW) | pnpm install hangs | none | N | no timeout | agent blocked indefinitely — **CRITICAL gap** |
| `build_render_flow.run_remotion_render` (NEW) | ffmpeg encoder failure mid-render | `subprocess.CalledProcessError` | Y | named error returned | producer sees error string |
| `build_render_flow.run_remotion_render` (NEW) | ffmpeg writes file but it's truncated | none | partial | `vm_ratify_render_package` does ffprobe check | depends on ffprobe rigor (need to verify) |
| `vm_websearch` (langchain_tools.py:108) | network failure during Tavily call | caught upstream as Exception | Y | structured error item | producer sees named error |
| `tests/evals/*` collection (NEW) | imports `vm_ratify_research`, etc. — names don't exist after rename | `ImportError` | N | uncaught at collection time | **eval harness broken at HEAD** — see §6 |

### Critical gaps (RESCUED=N AND silent / no-test)

1. **`session.init_video_session` overwrite without warning** — *unchanged from yesterday*. `session.py:30` still has `mkdir(parents=True, exist_ok=True)`.
2. **Hand-rolled YAML silent corruption** — *unchanged*. PyYAML in deps but unused.
3. **`build_render_flow.run_remotion_render` no subprocess timeout** — **NEW**. A hung pnpm or remotion-cli will block the agent indefinitely.
4. **`build_render_flow.ratify_build_scenes` only checks file existence** — **NEW**. TypeScript compile errors won't show up until render time.
5. **`controller.block_if_tool_call_dropout` parameterization removes safety net for non-default milestones** — **NEW (subtle)**. The old hard-coded research check always fired for the research milestone; the new generalized version requires the caller to pass `expected_artifact`. If the caller forgets, dropout is silently un-checked. Search shows only `source_intake` ever gets the default; the other three milestones rely on the caller.
6. **`tests/evals/` broken at collection time** — **NEW (highest priority)**. The eval harness was renamed in production code but not in the eval imports. Five test modules fail to collect with `ImportError`.

**Catch-all error handling:** the `except Exception: pass`-style violations from yesterday are gone. The `except Exception` at `source_flow.py:207` is named (it converts to a structured error item) — that is acceptable. The `except Exception:` at `langchain_tools.py:445` (around `_with_ui_state` projection) does swallow the exception with only a `logging.exception` — that's better than `pass` but not great; UI-state failures are rendered visible to operators only via stderr, not to the producer. Acceptable trade-off given the fault-tolerance goal.

---

## Section 3: Security & Threat Model

Threat model is largely unchanged from yesterday — single-user dev tool, no public endpoints, but with one new wrinkle: shelling out to `pnpm` and `ffmpeg`.

| Threat | Likelihood | Impact | Mitigated? | Note |
|---|---|---|---|---|
| Path traversal via `local_file`/`excalidraw_file` | Low | Med | **No (still)** | TODO #18 not done. `params.parse_video_request` does not check. |
| Prompt injection via `local_file` content | Med | Med-High | **No (still)** | Researcher subagent removed; scriptwriter now reads sources directly via the manifest. The risk shifts but does not reduce. |
| LLM-in-the-middle on `ANTHROPIC_BASE_URL` | Low | High | None (still) | Documented nowhere. |
| Secret leakage via committed `.env` | Low | High | **Mitigated** | `.gitignore` confirmed today: includes `.env` and `.env.local`. ✅ |
| Web-UI bound to public interface | Low | High | LangGraph dev defaults to localhost; documented as risk | Same as yesterday. |
| `execute_pwsh` shell injection (dead code) | Low (not registered) | High *if registered* | **NOT mitigated** — code still present | Yesterday's recommendation: delete. Status: not done. |
| **NEW: Subprocess command injection via Remotion build** | Low | Med-High | Partial | `vm_render_remotion_project` shells `pnpm` + `npx remotion` — uses argv list, not shell string, so injection through topic/goal fields is blocked. Verified at `build_render_flow.py:run_remotion_render` (subprocess.run with list args). ✅ |
| **NEW: Untrusted package install via pnpm** | Low | High | **No** | The `package.json` in `remotion-project/` is generated by the Remotion-builder subagent based on LLM output. A malicious LLM could write a dependency on a hostile package; `pnpm install` will pull it. Single-user tool so likelihood is low, but the trust boundary moved. |
| **NEW: ffmpeg input via untrusted assets** | Low | Med | partial | ffmpeg has known CVEs against malformed media. v2 only encodes Remotion-rendered frames, not user-supplied media — narrows the surface. |

### Recommendations

- **S1.** Add a path-confinement helper applied to `local_file` / `excalidraw_file` — *unchanged from yesterday*.
- **S2.** Document prompt-injection risk in README — *unchanged*.
- **S3.** Delete `execute_pwsh` and `project_glob`, and *now* delete the now-active `patch_deepagents_path_validation` call at `scripts/deepagents_video_maker.py:225`. The patch reaches into DeepAgents private internals (`middleware.filesystem._validate_path` or similar) and *is now executed at every CLI invocation* — yesterday it was dead, today it's fragile-and-running.
- **S4 — NEW.** Pin allowed packages in `remotion-project/package.json` template, or run pnpm with `--frozen-lockfile` against a project-supplied lockfile. The Remotion-builder subagent should not be free to declare arbitrary deps.

---

## Section 4: Data Flow & Interaction Edge Cases

### Data flow: source_intake milestone (renamed from research)

```
  User prompt ──▶ vm_parse_video_request ──▶ parse_video_request
       │                                          │
       │ [empty?]                          [unrecognized keys?]
       │ → "Untitled video"                → silently dropped
       ▼                                          ▼
  vm_init_video_session ──▶ init_video_session ──▶ output_dir
       │                                          │
       │ [output_dir collision?]                  │
       │ → silent overwrite ◀── SAME GAP          │
       ▼                                          ▼
  vm_start_source_intake ──▶ create_milestone_run ──▶ artifacts/source_intake/run-N
       │
       │ if goal.source == "websearch":
       ▼
  vm_websearch ──▶ run_websearch_and_cache ──▶ cache JSON
       │                       │
       │            [TAVILY_API_KEY missing?]
       │            → structured error item ◀── NEW WIN
       │            [tavily package missing?]
       │            → structured error item ◀── NEW WIN
       │            [Tavily 5xx?]
       │            → structured error item
       ▼
  vm_ratify_source_intake ──▶ write source-manifest.md + ratify_source_manifest
       │                       │
       │            [manifest has "websearch source intake requires
       │             TAVILY_API_KEY"?]
       │            → ratify still passes (error is in manifest as a
       │              source-item with type=websearch error)
       ▼            **GAP**: ratify should fail when manifest contains
                    only error-items, not pass and let scriptwriter
                    consume an empty source list.
  state.milestone(source_intake).status = completed | retry | blocked
```

**Shadow paths:**
- **Nil:** `prompt=None` and structured inputs all None → ValueError. Same as before.
- **Empty:** `topic=""` → "Untitled video". Still no warning.
- **Tavily error:** now visible in manifest, but the ratify gate doesn't fail — the producer might dispatch the scriptwriter with a manifest containing only `error` items. **NEW gap.** Add a check in `ratify_source_manifest` that at least one non-error source item exists.
- **Mixed-language topic with quotes:** unchanged risk; YAML hand-roller may corrupt.

### Data flow: build_scenes milestone (NEW)

```
  vm_start_build_scenes(script_approved=True) ──▶ artifacts/build_scenes/run-N
       │
       │ [script_approved=False?]
       │ → returns refusal (good)
       ▼
  vm_build_remotion_task ──▶ task(remotion-builder, description=...)
       │
       │ [subagent generates package.json + src/*.tsx]
       ▼
  vm_ratify_build_scenes ──▶ ratify_build_scenes
       │                       │
       │            [package.json exists but missing 'remotion' dep?]
       │            → ratify passes ◀── GAP
       │            [src/index.ts missing?]
       │            → ratify fails (good)
       ▼            [src/index.ts exists but TypeScript broken?]
                    → ratify passes; render fails later ◀── GAP
  state.milestone(build_scenes).status = completed | retry | blocked
```

### Interaction edge cases

| Interaction | Edge case | Handled? |
|---|---|---|
| User cancels mid-render | pnpm/remotion-cli orphan process | **N — NEW** |
| User aborts after script approval, restarts | resume goes to script milestone, not build_scenes | Untested |
| User runs `vm_render_remotion_project` twice in same run | overwrites `final/video.mp4` | Untested |
| Subagent (remotion-builder) emits pseudo task invocation | dropout detector catches if `expected_artifact=remotion-project/package.json` | Conditional (caller-supplied) |
| Remotion render produces 0-byte mp4 (encoder edge case) | `vm_ratify_render_package` ffprobe check should fail | Need to verify |

**Recommendation:** add a `tests/deepagents_video_maker/test_render_failure_modes.py` with three negative cases: missing package.json after build, 0-byte mp4 after render, hung pnpm (mocked). The render-package milestone is the most external-dependency-heavy and the least tested.

---

## Section 5: Code Quality Review

**Strengths**
- The new module separation (`source_flow`, `script_flow`, `build_render_flow`, `ui_state`, `middleware`) is clean. Each file owns one responsibility and dependencies fan out, not in.
- `ui_state.build_video_maker_ui_state` is small (140 LOC), pure (reads from disk, no side effects), and re-runnable. Tests for it exist (`tests/deepagents_video_maker/test_ui_state.py`, 80 LOC).
- The middleware fault-tolerance pattern (`try/except` with logged exception, return original result) is the right shape for projection middleware.

**Issues**

- **Q1. DRY:** `_to_virtual_path` is now in 2 places (was 3). `scripts/deepagents_video_maker.py:111` still has its own copy. Half-hour fix, deferred from yesterday.
- **Q2. DRY:** 13-kwarg fan-out is now in 5 tools (was 4). Same recommendation as yesterday.
- **Q3. Naming:** `local_file` vs `local-file` and `aspect_ratio` vs `aspectRatio` inconsistency persists. Add a single `_normalize_inputs` helper at the boundary; everything internal uses underscore.
- **Q4. Over-engineering:** `tools.py` still exists as a "Phase 1 placeholder" re-export. Now obsolete. **Delete or inline.** New `langchain_tools.py` is the source of truth.
- **Q5. Under-engineering:** producer.md is now 11 numbered controller-protocol rules, all in prose. The trip-wire from §0A is met; the prompt-only enforcement is fragile at this scope. **Move milestone-transition assertions into a thin LangGraph layer (50 LOC).** Keep progressive disclosure for the in-milestone subagent dispatch.
- **Q6. Cyclomatic complexity:** `build_render_flow.run_remotion_render` is the longest new function. Acceptable; it's a sequential subprocess pipeline.
- **Q7. Test honesty:** `tests/deepagents_video_maker/test_golden_demo_smoke.py::test_golden_playable_smoke_produces_probeable_mp4` `SystemExit`s with "ffmpeg required" rather than `pytest.skip`-ing. Looks like a test failure on hosts without ffmpeg. **Fix:** check ffmpeg availability and use `pytest.skip(reason=...)`.
- **Q8. Dead code regressed:** `scripts/deepagents_video_maker.py:225` now *calls* `patch_deepagents_path_validation()` — yesterday's "dead but harmless" became today's "live and reaches into private internals." **Fix:** delete `execute_pwsh`, `project_glob`, and `patch_deepagents_path_validation` together; the patch is unnecessary on Linux, fragile on every platform, and reaches into DeepAgents internals that are not promised stable.
- **Q9 — NEW. Eval harness module-rename drift.** `tests/evals/{train,holdout,scorecard}/test_*.py` import `vm_ratify_research`, `vm_start_research`, `vm_build_researcher_task` — names that no longer exist. **The harness was committed by `c3f10f2` (PR #5) before the rename and never updated.** Either rename the imports to the v2 tool names (`vm_ratify_source_intake`, `vm_start_source_intake`, `vm_build_scriptwriter_task`) or delete the entire `tests/evals/` tree. Leaving it broken on master means anyone running `uv run pytest tests/evals` sees five collection errors and concludes the project is broken. **High priority.**
- **Q10 — NEW. Two declared-but-unbuilt subagents in v2.** `agents/scene-batch-generator.md` and `agents/scene-patch-generator.md` are well-written prompts that are not registered. Add `## Status: experimental, not registered` headers, or move to `references/` until wired. Yesterday's "aspirational SKILL.md" pattern crept back in at the agent level.

---

## Section 6: Test Review

### Test landscape (HEAD `9380e5d`)

| Surface | Count | Status |
|---|---|---|
| `tests/deepagents_video_maker/*.py` | 17 files / ~88 tests | 86 pass, 1 fail (ffmpeg-missing on this host); CI installs ffmpeg per `93bf38a` so green in CI |
| `tests/evals/train/` | 5 files | **collection ERROR — broken imports** |
| `tests/evals/holdout/` | 3 files | **collection ERROR — broken imports** |
| `tests/evals/scorecard/` | 2 files | **collection ERROR — broken imports** |

**The eval harness is broken at HEAD.** This is the single highest-priority finding of this review and supersedes most other test gaps. Fix before anything else.

### Coverage assessment (working tests)

The new `tests/deepagents_video_maker/` files cover most of the new code:
- `test_build_render_flow.py` (220 LOC) — build_scenes + render_package ratify paths.
- `test_ui_state.py` (80 LOC) — projection from state.yaml + artifacts.
- `test_skill_files.py` (118 LOC) — checks v2 skill structure on disk; explicitly asserts harness/v1 references are absent.
- `test_windows_path_normalization.py` (18 LOC) — small, focused.
- `test_golden_demo_smoke.py` (73 LOC) — runs the deterministic source_intake → script smoke test against golden fixtures.

### Gaps still present (carried from yesterday + new)

- **T1. End-to-end producer-protocol test against a stub model** — *not done*. Highest-leverage missing test. The deterministic golden smoke tests bypass the LLM and call typed tools directly; they don't exercise the 11-step producer protocol.
- **T2. Tool-call dropout detection on script milestone** — partially closed (controller is generalized, but no test asserts the script milestone dropout-detection path).
- **T3. Adversarial topic round-trip** — *not done*.
- **T4. Session-init collision test** — *not done*.
- **T5. Ratify regex edge cases** — *not done*.
- **T6. Web-UI test step in CI** — *not done*.
- **T7 — NEW. Render-failure-mode tests.** Negative cases for `build_render_flow`: missing package.json, broken TypeScript imports, 0-byte mp4, hung subprocess.
- **T8 — NEW. ffprobe-skip in `test_golden_playable_smoke`.** Use `pytest.skip` instead of `SystemExit` when ffmpeg is absent.

### Test pyramid

The new `tests/evals/` layout (train / holdout / scorecard) is the *right* pyramid for a controller-driven LLM agent — but it doesn't run. **Either fix or delete.** Keeping a broken eval tree on master is worse than no eval tree.

### Test ambition checks

- "2am Friday confidence": still missing T1 (end-to-end with stub model).
- "Hostile QA engineer": render-failure modes (T7), session collision, adversarial topic — none tested.
- "Chaos test": inject `<sop_invocation>` into a stubbed model response, assert dropout fires across all four milestones — still missing.

---

## Section 7: Performance Review

Performance is still LLM-latency dominated; no DB; small artifacts. Three new wrinkles since yesterday:

- **P1 — NEW.** `vm_render_remotion_project` blocks the agent for the duration of pnpm install + Remotion render + ffmpeg encode. For a 60s clip this is ~30-90 seconds. **No timeout.** Agent will appear hung from the user's perspective if anything goes wrong upstream. **Add a timeout (suggest 5 minutes) and a structured timeout error.**
- **P2 — NEW.** Each tool call now triggers `VideoMakerUiStateMiddleware.wrap_tool_call`, which reads `state.yaml` and walks `output_dir` to project the UI state. This is `O(tool_calls × file_io)`. For a session with 50 tool calls and 4 milestones × 3 runs of artifacts each, that's ~600 file stat operations per session. Negligible today; flag for later.
- **P3.** `glob("run-*")` in `create_milestone_run` is now called for 4 milestones (was 2). Same O(N) per milestone, still fine.

No other issues.

---

## Section 8: Observability & Debuggability Review

- **O1.** Structured logging is still effectively absent (one `logging.exception` call). **Carried from yesterday with no progress.** The new render path (subprocess + 30-90s wait) makes this *more* important — without per-step logging, debugging a hung render is a guessing game.
- **O2.** Ratify JSON files now exist for 4 milestones (was 2) — auditing surface grew without effort. ✅
- **O3.** `LANGSMITH_TRACING` is still respected. Documenting how to enable it in README would still help.
- **O4 — Improvement.** `VideoMakerUiStateMiddleware` + `VideoProductionTimeline.tsx` now give the user a real-time view of session progress in the web-UI. **Major debuggability win.** Yesterday I called this out as a gap; today it's resolved for the web-UI surface (CLI users still don't have it).
- **O5.** Alerting still N/A.
- **O6.** Runbooks: still none. **Two new runbooks needed:**
  - "Render package failed: how to inspect Remotion logs, ffmpeg output, and recover" (`docs/runbooks/render-failed.md`).
  - "tests/evals collection error: rename the imports" (one-shot fix doc, can be a comment in `tests/evals/conftest.py` until fixed).

### Debuggability check

If a user reports "session XYZ failed" three weeks post-run:
- ✅ `state.yaml` final status + blocking_reason.
- ✅ `ratify/{milestone}-run-N.json` per-milestone failure.
- ✅ **NEW**: `final/` directory shows whether render succeeded.
- ❌ `remotion-project/` may have been cleaned up; no log retention policy.
- ❌ No record of model version / pnpm version / Remotion version / ffmpeg version active at run-time. **Add `state_schema_version` AND `tool_versions` to state.yaml.**

---

## Section 9: Deployment & Rollout Review

- **D1.** Versioning: still `0.1.0`, no CHANGELOG, no tags. *Carried from yesterday.*
- **D2.** Dependency pins: still no upper bounds. *Carried from yesterday.* The risk is now larger because the rendering pipeline depends on more SDKs (LangChain + DeepAgents + Remotion + ffmpeg).
- **D3.** Node lockfile: `pnpm-lock.yaml` 238KB committed, `packageManager: pnpm@9.15.0` pinned. ✅
- **D4.** CI: now installs ffmpeg (good — `93bf38a`). Still no Node-side step. **The eval harness CI gate is implicit but not actually exercised** — running `pytest tests/evals` in CI would have caught the import-rename break.
- **D5.** Migration safety: `state.yaml` still has no version field. The pipeline rename from `research → source_intake` is a **silent breaking change** for any in-flight session created against `fbc0074`. There is no migration helper. **Add `state_schema_version: 2` now** (treat the rename as v2) and write a `migrate_state_v1_to_v2(path)` helper that maps old milestone IDs to new ones.
- **D6.** Feature flags: not applicable.
- **D7.** Smoke tests: `pnpm golden:script` (deterministic, no LLM) and `pnpm golden:render` and `pnpm golden:playable` (deterministic + ffmpeg). Document them as the post-`uv sync` "first thing to run."

---

## Section 10: Long-Term Trajectory Review

### Tech debt introduced or carried

| ID | Item | Status today | Trend |
|---|---|---|---|
| L1 | Hand-rolled YAML | Unchanged | Static; PyYAML in deps but unused |
| L2 | 13-kwarg fan-out across now-5 tools | Worsened | More surfaces affected |
| L3 | Dead Windows code in `scripts/` | **Worsened** | `patch_deepagents_path_validation` now called on every CLI run |
| L4 | Aspirational SKILL.md | **Improved** (v1 deleted; v2 SKILL.md matches reality) but new aspirational artifacts in `agents/` (scene-batch, scene-patch) unwired |
| L5 | No state schema version | Unchanged | Now critical because of the source_intake rename |
| L6 | Controller dropout was research-only | **Improved** (generalized) but caller-must-pass-artifact creates a new latent gap |
| L7 | No CHANGELOG / tags | Unchanged | First external user filing an issue still has no version anchor |
| L8 | Reflexion lessons referenced but unread | **Resolved by deletion** | Aspirational hooks gone with v1 ✅ |
| L9 — NEW | tests/evals/ broken at HEAD | New | Highest-priority cleanup item |
| L10 — NEW | Two unwired v2 agents (scene-batch, scene-patch) | New | Aspirational pattern at smaller scale |
| L11 — NEW | Web-UI timeline lists 5 milestones; backend lists 4 | New | Drift between sources of truth |
| L12 — NEW | Strategic pivot drafted (specs/video-maker-web-port) without a kill criterion for v2 | New | Dominant strategic uncertainty |

### Reversibility ratings

| Decision | 1 (one-way) → 5 (reversible) |
|---|---|
| Controller-only architecture (no LangGraph DAG) | 3 — still possible to add a thin transition layer; trip-wire crossed |
| `source_intake` rename | 4 — could rename back; eval harness is in flight |
| `skills/video-maker/` deletion | 4 — recoverable from git history if pivot is needed |
| Hand-rolled YAML | 5 — switch to PyYAML still cheap |
| Remotion as substrate | **2 if pivot to web-recording proceeds** — much of the new code (`build_render_flow.py`) is Remotion-specific |
| `VideoMakerUiStateMiddleware` shape | 5 — substrate-independent, will work for any pipeline shape |

### Path dependency

- `manifest.json` schema is now `manifest-schema.md` and `source-manifest.md` schema (different files, different purposes). The script-contract → script.md → manifest.json → remotion-project chain is the v2 rendering contract. **If the team commits to v2 (Approach A in §0C-bis), promote `references/manifest-schema.md` to `docs/manifest-schema.md` and treat as a public contract.** If the pivot proceeds, this becomes moot.
- `VideoMakerUiStateMiddleware` is the keystone for any future UI surface (web, CLI, IDE). Treat as load-bearing — its shape is reversible but its `video_maker` state-key contract should be considered semi-public.
- The 11-step producer protocol prose is now load-bearing. Each new milestone added to it without supporting code in `controller.py` is a tax on the LLM's tool-call accuracy.

### The 1-year question

If a new engineer joins in 12 months and reads this repo cold, do they understand it?
- README + CLAUDE.md + AGENTS.md + 6 design docs + Stage-1 web-port spec = **strong onboarding for the conceptual landscape** but **confusing for "what is shipped today."**
- The `skills/video-maker-v2/` vs `specs/video-maker-web-port/stage-1-skill/` parallel-development is the biggest source of confusion. **Make the substrate decision and write it down.**
- The broken `tests/evals/` will read as "is this project alive?" to a new contributor. Fix this week.

---

## Section 11: Design & UX Review

Yesterday this section was skipped (no UI scope on that branch). Today there *is* UI scope: `VideoProductionTimeline.tsx` (191 LOC) is the new center of the user-facing surface.

### Findings

- **U1. Five milestones in the React component, four in the backend.** `ORDERED_MILESTONES` in `VideoProductionTimeline.tsx:19-25` lists `source_intake, script, build_scenes, render_package, publish_readiness`. `session.DEFAULT_MILESTONES` lists only the first four. `ui_state.MILESTONE_LABELS` lists all five. **Pick one canonical list** and import or re-export it everywhere else. Hard-coded duplicates of ordered lists are the most reliable source of UI drift.
- **U2. Status icons mix shadcn semantic colors with raw Tailwind colors** (`text-success/80` and `text-amber-500` in the same file). Consistency check; minor.
- **U3. Artifact-link patterns are regex-based.** `ARTIFACT_HINTS` in the same file matches by filename suffix. This works for known artifacts but won't scale to per-scene artifacts (when scene-batch / scene-patch ship). Treat as known limitation, document in the component header.
- **U4. No empty-state copy.** When `state.values.video_maker` is null (cold start, no session yet), what does the timeline show? Need to verify; if it crashes or shows a degenerate empty state, add a "no session yet — start with `vm_init_video_session`" hint.
- **U5. No "session re-entry" flow.** If the user opens a stale browser tab pointing to a completed session, the timeline shows completed for everything but offers no obvious "start a new session" affordance. Add one.

### UX edge cases not addressed (when audio milestone lands)

- "Approve" button mid-pipeline: double-click, session-disconnect-mid-approval, approval-of-stale-state — all known edges from yesterday's deferred Section 11.

---

## Required Outputs

### NOT in scope

| Item | Why deferred |
|---|---|
| Per-scene loop (TTS / Whisper / image-gen / scene-batch dispatch) | Designed in `references/audio-contract.md` and `agents/scene-batch-generator.md`, not wired |
| GAN Evaluator contract loop | Designed in v1 docs, dropped from v2; unimplemented |
| Reviewer (Layer 2) and Editor subagents | Prompts deleted with v1; unwired in v2 |
| Reflexion lessons | Removed with v1 ✅ |
| HITL approval flow as interactive AskUserQuestion | Designed in producer.md as "stop and wait", not implemented as a programmatic interrupt |
| Production deploy | Tool is dev-only by design |
| Stage-1 web-port skill | Drafted in `specs/video-maker-web-port/stage-1-skill/`, not committed |

### What already exists (and is reused)

| Sub-problem | File | Reused? |
|---|---|---|
| Milestone state machine | `models.MilestoneState`, `state_store.update_milestone_status` | ✅ |
| Run-N directory convention | `session.create_milestone_run` | ✅ extended to 4 milestones |
| Artifact ratify pattern | `ratify.py` + `build_render_flow.{ratify_build_scenes, ratify_render_package}` | ✅ extended |
| Subagent prompt loading | `prompts.load_subagent_prompt` | ✅ rotated to scriptwriter + remotion-builder |
| Tool-call dropout detection | `controller.block_if_tool_call_dropout` | ✅ generalized |
| Path virtualization | `script_flow._to_virtual_path` | ⚠️ deduplicated to 2 places (was 3) |
| UI-state projection (NEW) | `ui_state.py` + `middleware.py` | ✅ clean separation |

### Dream-state delta

This branch (`9380e5d`) **moved the pipeline forward by two milestones** and added a real UI surface. That is substantial *progress* — much more than yesterday's documentation-only branch. The cost is twofold: (1) most of yesterday's hardening TODOs were not closed, and (2) a strategic pivot was drafted in parallel without an explicit kill criterion. Net delta vs. yesterday: **strong forward motion on capability, weak motion on rigor, growing strategic uncertainty.**

### Error & Rescue Registry

Eight critical silent-failure or no-test gaps at HEAD. **Five carried over from yesterday + three new:**

1. `session.init_video_session` — silent output_dir overwrite (carried).
2. Hand-rolled YAML silent corruption on adversarial topics (carried).
3. `controller.block_if_tool_call_dropout` requires caller-supplied artifact for non-default milestones — silent miss if forgotten (NEW, side-effect of generalization).
4. `ratify.ratify_research` (now `ratify_source_manifest`) — `UnicodeDecodeError` on garbage source content (carried).
5. `state_store.{save,load}_*_yaml` — silent corruption (carried; same as 2).
6. **NEW.** `build_render_flow.run_remotion_render` — no subprocess timeout, agent hangs indefinitely.
7. **NEW.** `build_render_flow.ratify_build_scenes` — file-existence-only check, doesn't validate TypeScript.
8. **NEW.** `tests/evals/` — broken at collection time; eval harness is dead.

### Failure Modes Registry

| CODEPATH | FAILURE MODE | RESCUED? | TEST? | USER SEES? | LOGGED? |
|---|---|---|---|---|---|
| `init_video_session` | output_dir collision | N | N | nothing (silent overwrite) | N — **CRITICAL** |
| `state_store.{save,load}` | adversarial topic | N | N | crash or silent corruption | N — **CRITICAL** |
| `block_if_tool_call_dropout` | non-default milestone, caller forgets `expected_artifact` | N | N | dropout silently un-detected | N — **CRITICAL** |
| `run_remotion_render` | hung subprocess | N | N | indefinite hang | N — **CRITICAL** |
| `ratify_build_scenes` | TypeScript broken in remotion-project | N | N | render fails later, not at ratify | N — **CRITICAL** |
| `tests/evals/*` | broken imports at collection | N | N (the test infra itself is broken) | "5 errors during collection" | N — **CRITICAL** |
| `params.parse_video_request` | non-numeric quality_threshold | N | N | crash | N — gap |
| `start_research_milestone` (now source_intake) | called when already completed | N | N | silent re-run | N — gap |

**Critical gaps total: 6.** Up from 5 yesterday. **The trend is in the wrong direction.**

### TODOs proposed (carried + new, prioritized)

This is a written review, so TODOs are presented in priority order ready for `TODOS.md`:

| # | Title | Priority | Effort | Why |
|---|---|---|---|---|
| **A** | **Fix tests/evals broken imports** | **P0** | XS | Either rename to v2 tools or delete the tree. Currently 5 collection errors on master. |
| **B** | **Make the substrate decision: v2 Remotion vs Stage-1 web-port** | **P0** | M (5-day decision sprint per §0C-bis Approach C) | Dominant strategic uncertainty; team is paying for both routes. |
| **C** | **Add subprocess timeout + structured error to `vm_render_remotion_project`** | P1 | XS | Currently hangs the agent indefinitely. |
| **D** | **PyYAML migration in `state_store.py`** | P1 | S | Carried from yesterday; PyYAML in deps but unused; eliminates ~120 LOC and the adversarial-topic risk. |
| **E** | **Output-dir collision guard in `init_video_session`** | P1 | XS | Carried; silent data loss path. |
| **F** | **Add `state_schema_version` field + write a v1→v2 migration helper** | P1 | S | The `research → source_intake` rename is a silent breaking change today. |
| **G** | **Delete `execute_pwsh`, `project_glob`, `patch_deepagents_path_validation`** | P1 | XS | Carried; the patch is now executed at every CLI invocation. Worse than yesterday. |
| **H** | **Fix milestone-list drift between backend and React timeline** | P1 | XS | Single source of truth for `(source_intake, script, build_scenes, render_package, ?publish_readiness)`. |
| **I** | **Fail `ratify_source_manifest` when manifest contains only error items** | P1 | XS | Otherwise scriptwriter dispatches with empty source list. |
| **J** | **Generalize-or-test `block_if_tool_call_dropout` for all 4 milestones** | P1 | S | Add tests asserting dropout fires for script, build_scenes, render_package; verify caller passes correct `expected_artifact`. |
| **K** | **Add render-failure-mode tests** | P1 | M | Negative cases: missing package.json, broken TypeScript, 0-byte mp4, hung pnpm (mocked). |
| **L** | **Use `pytest.skip` instead of `SystemExit` when ffmpeg is missing** | P2 | XS | Honesty bug in `test_golden_playable_smoke`. |
| **M** | **Slim 13-kwarg fan-out across 5 tools** | P2 | M | Carried; affects more surfaces now. |
| **N** | **Consolidate `_to_virtual_path` into one place (still 2× today)** | P2 | XS | Carried. |
| **O** | **Pin upper bounds on deepagents/langchain** | P2 | XS | Carried. |
| **P** | **Drop the unused dep — confirmed today: `langchain-tavily`, not `tavily-python`** | P2 | XS | Yesterday's note inverted. |
| **Q** | **Add structured logging via `logging` module** | P2 | S | Carried; more important now that render path is subprocess-heavy. |
| **R** | **Tag scene-batch / scene-patch agents `## Status: experimental` or move to references** | P2 | XS | New aspirational-prompt pattern. |
| **S** | **End-to-end producer-protocol stub-model test** | P2 | M | Carried; trip-wire crossed for controller-only bet, this is now load-bearing. |
| **T** | **Adversarial topic round-trip tests** | P2 | S | Carried. |
| **U** | **Path-confinement on `local_file`/`excalidraw_file`** | P3 | S | Carried. |
| **V** | **Two runbooks: render-failed, dropout-detected** | P3 | S | Carried (renamed from research-blocked). |
| **W** | **CHANGELOG.md + tag v0.1.0** | P3 | XS | Carried. |
| **X** | **Web-UI CI step (`eslint` + `tsc --noEmit`)** | P3 | XS | Carried. |
| **Y** | **Promote `manifest-schema.md` to `docs/`** | P3 | XS | Conditional on Approach A — only if v2 wins the substrate decision. |

**P0 items are 2; P1 items are 9; P2 items are 8; P3 items are 5.** Total 24 (was 20 yesterday). The lift to close P0+P1 is ~3-4 days with CC.

### Diagrams produced

1. ✅ Updated component dependency graph (Section 1).
2. ✅ source_intake milestone data flow (Section 4).
3. ✅ build_scenes milestone data flow (Section 4).

### Diagrams missing

- Milestone state-machine (4 milestones × {pending, in_progress, completed, blocked, retry}).
- Render subprocess timing/timeout diagram.
- Web-UI streaming sequence (tool-call → middleware → state-projection → React rerender).

### Stale diagram audit

No ASCII diagrams currently live in source. None to flag.

---

## Outside Voice (skipped)

Recommended but not invoked. If the team wants a second opinion on the **substrate decision** (which is the dominant question this week), pipe `specs/video-maker-web-port/stage-1-skill/requirements.md` and `skills/video-maker-v2/SKILL.md` to GPT-5 / Gemini 2.5 / Codex with the prompt: "Given these two routes, which is more likely to ship a complete 60-second demo in 4 weeks, and why?" That's the framing that forces a useful outside read.

---

## Completion Summary

```
+========================================================================+
|       CEO PLAN REVIEW — COMPLETION SUMMARY (deepagents-video-maker)    |
|                            (follow-up @ 9380e5d)                       |
+========================================================================+
| Mode selected         | HOLD SCOPE (with C-sprint substrate decision)  |
| System Audit          | 24h leap forward; 4 milestones wired; eval     |
|                       | harness BROKEN at HEAD                         |
| Step 0                | Approach C (5-day decision sprint) recommended |
| Section 1  (Arch)     | 7 issues found (A1-A7); trip-wire crossed      |
| Section 2  (Errors)   | 17 paths mapped, 6 CRITICAL GAPS (was 5)       |
| Section 3  (Security) | 4 carried + 3 new findings                     |
| Section 4  (Data/UX)  | source_intake + build_scenes flows mapped      |
| Section 5  (Quality)  | 10 issues (Q1-Q10); Q9 (broken evals) is P0    |
| Section 6  (Tests)    | Main suite 86/87 green; evals BROKEN; 8 gaps   |
| Section 7  (Perf)     | 1 NEW: render subprocess has no timeout        |
| Section 8  (Observ)   | UI timeline shipped (win); logging still gap   |
| Section 9  (Deploy)   | state_schema_version more urgent post-rename   |
| Section 10 (Future)   | 12 debt items (was 8); reversibility avg 3.8/5 |
| Section 11 (Design)   | 5 issues found on new VideoProductionTimeline  |
+------------------------------------------------------------------------+
| Prior-review TODO closure | 4/20 fully done, 3/20 partial, 13/20 open  |
| Critical gaps (silent)    | 6 (was 5); 3 NEW from new milestones        |
| TODOs proposed            | 24 (was 20); 2 P0, 9 P1, 8 P2, 5 P3         |
| Scope proposals           | 0 new; substrate decision pending           |
| CEO plan persisted        | this file                                   |
| Outside voice             | skipped                                     |
| Diagrams produced         | 3 (component, source_intake, build_scenes)  |
| Stale diagrams found      | 0                                           |
| Unresolved decisions      | 2 (substrate; v2 hardening before v3)       |
+========================================================================+
```

### Unresolved decisions (require user input)

1. **Substrate: v2 Remotion vs. Stage-1 web-port.** Recommended: 5-day decision sprint per §0C-bis Approach C. Decision criterion: which substrate produces a finished 60-second demo from one topic in fewer human-hours of intervention?
2. **v2 hardening before next scope expansion.** 13/20 prior-review TODOs are still open. The trip-wire on the controller-only bet is crossed. **Hold scope expansion until at least P0 + P1 close** (≈3-4 days with CC).

---

## Verdict

**This is a project moving fast on capability and slow on rigor.** In 24 hours, the pipeline went from 2 milestones to 4, the v1 skill was deleted cleanly, a real web-UI timeline shipped, and the controller's dropout-detection was generalized. The architectural diff is genuinely impressive.

**But:** the eval harness is broken at HEAD (P0), the controller-only bet has crossed its trip-wire without compensating tests, and 13 of yesterday's 20 hardening TODOs are still open. The strategic pivot drafted in `specs/video-maker-web-port/` means the team is currently paying for two substrates without committing to either.

**Five critical silent-failure gaps remain from yesterday; three new ones (subprocess timeout, file-existence-only ratify, broken evals) joined them.** The trend is in the wrong direction.

**The single most important action this week** is the substrate decision (TODO B). Until that is made, every line of v2 work has discount-rate risk. The single most important action *today* is fixing the broken eval harness (TODO A) — five minutes of grep-replace and the project becomes credible to a new contributor again.

The new middleware/timeline architecture is the strongest design move on this branch and works regardless of substrate choice. Preserve it.

**Recommended next steps in order:**
1. **TODAY:** Close TODO A (fix or delete `tests/evals/`). Five minutes.
2. **THIS WEEK:** Run a 5-day substrate decision sprint (TODO B) — pick a route, write the kill criterion for the loser, archive the loser's spec. After the decision is made, commit.
3. **THIS WEEK:** Close P1 TODOs C–K (subprocess timeout, PyYAML migration, collision guard, schema version, dead-code deletion, milestone-list canonicalization, ratify-on-empty-manifest, dropout coverage, render-failure tests). 3-4 days with CC.
4. **NEXT WEEK:** Either (Approach A) commit to v2 and ship a CHANGELOG'd v0.2.0 with all P1+P2 closed, or (Approach B) execute Stage-1 T0–T2 and start the web-port build.
5. Then choose: deepen the chosen substrate (assets / per-scene loop / audio) or harden it further with the remaining P3 list.

— end of review —
