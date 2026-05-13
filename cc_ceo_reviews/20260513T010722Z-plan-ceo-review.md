# CEO Review — deepagents-video-maker

- **Date:** 2026-05-13 01:07:22 UTC
- **Branch:** `claude/gracious-gates-yVhq9`
- **HEAD:** `9380e5d` — `feat(skill): implement Stage 1 plan for video-maker skill with detailed task breakdown and acceptance criteria`
- **Reviewer skill:** `gstack/plan-ceo-review` v1.0.0 (https://github.com/garrytan/gstack), adapted for **non-interactive written delivery** — the skill's interactive AskUserQuestion ceremonies are rendered as explicit "Decision needed" blocks the user can react to. CEO posture, prime directives, cognitive patterns, and required outputs are preserved.
- **Mode selected:** **HOLD SCOPE on v2 + PREMISE CHALLENGE on the proposed pivot.** The newest commit on this branch lays a 28-32-day plan to deprecate the canonical `video-maker-v2` (Remotion) skill and rebuild as a parallel `video-maker` (Vite/React + Playwright) skill. The CEO move here is **not** to silently accept that pivot or silently reject it — it is to surface it as a discrete one-way-door decision, force a written premise challenge, and only then let scope expand. Until that decision lands, current v2 hardening is the right default.
- **Posture:** Rigorous reviewer. Zero silent failures. Every error has a name. Inversion reflex on every architectural choice. Permission #9 ("scrap it and do this instead") is on the table — but in this case, it is being *invoked by the codebase* against the codebase, and the CEO's job is to interrogate it before it becomes inertia.

---

## 0. Pre-Review System Audit

### Repository state

- Working tree **clean** on `claude/gracious-gates-yVhq9`. HEAD = `9380e5d`.
- Most recent commits (top of branch):
  1. `9380e5d` Stage 1 plan for new `video-maker` skill (3,465 insertions, no production code yet — only `specs/video-maker-web-port/stage-1-skill/{requirements,design,tasks}.md`)
  2. `17c032e` UI timeline interrupted state, error guidance, ratify serialization, README Quick Start
  3. `7b71660` Deepen websearch, guard `data_card` fabrication, expose `vm_websearch` tool
  4. `3b719dd` Allow indented items in `data_card_grounding` ratify check
  5. `0b6f3f7` VSCode launch/task configs, agent:dev script
- The branch has been steadily hardening the v2 Remotion path; the Stage 1 spec commit is a sharp directional turn at the very top of that branch.

### Evidence run

| Check | Result | Notes |
|---|---:|---|
| `uv run python scripts/deepagents_video_maker.py --check` | **PASS** | All v2 skill files present (`SKILL.md`, `workflow-contract.md`, `scriptwriter.md`, `remotion-builder.md`, both wrapper skills). |
| `uv run pytest tests/deepagents_video_maker -q` | **86/87** | Only failure is `test_golden_playable_smoke_produces_probeable_mp4` — fails because `ffmpeg` is not installed in this sandbox, **not a regression**. Re-ran deselecting that test: 86/86 green. |
| Recent test count vs. prior CEO review | **+14** | 72 → 86, 19 % growth driven by golden-demo, UI state, websearch ratify, build/render flow, ratify-script coverage. |
| `git status` | clean | No uncommitted scar tissue. |
| `git stash list` | empty | No hidden work. |

### Code shape

- Production Python: 18 files, ~2,872 LOC.
  - Largest: `langchain_tools.py` (554), `build_render_flow.py` (514), `source_flow.py` (293).
- Tests: 17 v2 files (`tests/deepagents_video_maker/`) + 9 legacy `tests/evals/` (research-era; no longer wired into the default test path per `pyproject.toml` `testpaths`).
- Skills:
  - **Canonical:** `skills/video-maker-v2/` (active, runtime-wired, eng-review `resolved_verified`).
  - **New:** `skills/feature-pipeline/SKILL.md` — added recently; orchestrates plan → design → implement → verify → ship using gstack-style sub-skills. Distinct from the v2 pipeline; **this is a meta-skill, not a video skill.**
  - **Proposed:** `skills/video-maker/` — does not yet exist on disk; spec only.
- TODOS/FIXME: 0 in active source tree (clean signal). Legacy evals tests still reference research-era contract; they are not loaded by default but they are not deleted either.

### Recently touched files (signal: where attention is going)

`script_flow.py` (data-card guardrails), `build_render_flow.py` (build/render ratify), `ui_state.py` (UI projection), `web-ui/**` (timeline interrupted state), `skills/video-maker-v2/agents/scriptwriter.md` (harness target), `specs/video-maker-web-port/**` (new pivot).

**Signal:** the team is simultaneously *hardening* v2 and *planning to retire* v2. That is a coherent story only if the pivot is committed to with eyes open.

### Prior review continuity

- Last CEO review (`ceo_reviews/20260509-090645-ceo-review.md`, 2026-05-09) scored v2 **7.5 / 10**. Three CEO findings:
  1. UI timeline state must become authoritative (critical gap).
  2. Watchable end-to-end video proof missing.
  3. `next build` `spawn EPERM` on Windows.
- **Status of those findings on this HEAD:**
  | Prior finding | Status now |
  |---|---|
  | Authoritative `video_maker` UI state | **RESOLVED.** `src/deepagents_video_maker/middleware.py` projects `state.yaml` + ratify artifacts into LangGraph thread state via `VideoMakerUiStateMiddleware`. UI is no longer guessing. |
  | Watchable golden video | **RESOLVED.** `scripts/run_golden_playable_smoke.py` + `pnpm golden:playable` exists; `test_golden_playable_smoke_produces_probeable_mp4` is in CI when ffmpeg is present. |
  | `next build` `spawn EPERM` | **RESOLVED.** `scripts/build-ui.mjs` is the Windows-safe wrapper; `pnpm ui:build` uses it. |
- Last engineering review (`eng_reviews/20260509-093401-plan-eng-review.md`) closed as `resolved_verified`.

**Therefore:** v2 cleared every flagged CEO finding from the prior cycle. The very next commit then proposed deprecating it. That is the central narrative tension this review must resolve.

### Design / spec docs in flight

- `specs/video-maker-web-port/stage-1-skill/{requirements.md, design.md, tasks.md}` — the proposed pivot. Comprehensive (~1,700 lines), in Chinese, references methodology from `ConardLi/garden-skills/skills/web-video-presentation` (fork-and-rewrite, not direct fork).
- `specs/video-maker-v2-harness-upgrade/*.deprecated.md` — already shelved by prior decision.
- `docs/plans/20260507-220336-p0-p1-video-productization-plan.md` — the P0/P1 plan that produced the golden demo + UI timeline + publish-readiness work. Largely **delivered**.

---

## Step 0: Premise Challenge + Mode Selection

### 0A. Premise Challenge — is this the right problem to solve?

The new commit's spec opens with this premise, which I'll quote and challenge:

> "better-harness signal is broken because the 7 `[[cases]]` reference ratify unit tests that don't call the LLM and don't read `scriptwriter.md`. Therefore the optimizer iterates in a vacuum. The path forward is to rebuild as a Web 录屏 (web screen-recording) skill."

This is **two premises stapled together.** Let me separate them.

**Premise A — better-harness is broken signal.** Likely correct. If the only optimization surface is a prompt and the cases never actually load the prompt, the optimizer is doing gradient descent on nothing. Delete the harness or fix the loop; both are defensible. Spec correctly flags this.

**Premise B — therefore rebuild the skill as Vite + React + Playwright.** **This does not follow from Premise A.** Premise A is about better-harness, not about Remotion. The conflation is the largest premise error in the spec. Better-harness is a 200-line wrapper plus a `.toml`; Remotion is a 4-week-old production pipeline with passing CI, a playable golden smoke, an authoritative UI projection, and ratify gates. Deleting better-harness is a one-day refactor. Rebuilding the skill is a **5-6.5-week** (per spec's own estimate) rewrite.

If the real motivation is *"Web recording is a better product surface than Remotion"*, the spec should say that **on its own merits** — not smuggle it in behind a broken-harness argument. Specifically I want clearly stated:

1. Why is Vite + React + Playwright a better video output medium than Remotion?
2. What concrete user-visible capabilities does Web recording unlock that Remotion blocks?
3. What does Remotion do well today that Web recording will give up?
4. Who is the user? Cursor/Codex users have OPUS-level CLI agents *and* Anthropic API access — is the target audience really "non-DeepAgents" Skill consumers? The spec asserts this implicitly but doesn't quantify the audience.

Three CEO-level premises worth challenging:

1. **"Skill-self-contained, dependency-free" as a product virtue.** The new spec frames "any Claude Code / Cursor / Codex user can install and run" as a marquee benefit. **But this repo is `deepagents-video-maker`** — its core value proposition is the *DeepAgents orchestration*, not Skill-portability. Optimizing for "runs in Codex" deprioritizes the differentiating asset. If skill-portability is genuinely the strategic goal, *that should be the title of the repo and the README*. As is, this looks like scope drift toward the easier-to-evangelize artifact.

2. **"Web recording = product simplicity."** Vite + React + Playwright is **more** moving parts than Remotion, not fewer. Remotion: one renderer, one CLI. Web recording stack: Vite dev server + browser + Playwright + ffmpeg encoder + display config + audio sync layer + CI headless dance. The spec acknowledges this implicitly by introducing `narrations.ts` as the "single source of truth" for `step count × subtitles × audio synthesis`. That's *new* infrastructure. The simplification is **author-side ergonomics for the Skill consumer**, not pipeline-side.

3. **"Throwing away v2 is cheap because AI compresses LOC."** Boil-the-lake reasoning is correct *for new work*. It is wrong for **deletion-and-rebuild** when the existing code has earned scar tissue around real failure modes. The 86 passing tests are *contract knowledge*: "data_card scenes need a `data_semantic`," "render package needs ffprobe duration," "tool-call dropout looks like X." That knowledge does not transfer to a Web/Playwright pipeline for free. **The rebuild starts from zero scar tissue and will spend 2-4 weeks rediscovering the same edge cases.**

**Verdict on premises:** problem framing is mixed. The better-harness deletion is correct (Premise A). The Remotion-to-Web pivot is **a separate, much larger strategic claim that has not been argued on its own merits.** Currently it reads as: "the harness is broken, and while we're cleaning up let's also rewrite the skill." That is **classic two-week refactor turning into a five-week pivot** — Munger inversion warning.

> **Decision needed [DEC-PIVOT]** — Before any T0 task in `specs/video-maker-web-port/stage-1-skill/tasks.md` is touched: write one page titled *"Why Web recording beats Remotion for this product, on its own merits"* and put it next to the spec. If you cannot fill it convincingly in 60 minutes, the pivot is premature.

### 0B. Existing Code Leverage — what already partially solves the new spec?

| New-spec sub-problem | What v2 already has | Reuse path |
|---|---|---|
| Single-source-of-truth narration → subtitle → audio | `script.md` Scene schema with `narration:` field; `audio-contract.md`; `qwen3_tts_scene.py`; `whisper_to_json.py`; scene-duration measurement | `narrations.ts` is the same idea in TypeScript. The contract translation is mechanical, not novel. |
| Scene-by-scene authoring (Chapter 1 baseline + iterate) | `scene-batch-generator.md`, `scene-patch-generator.md` subagents; iterative ratify loop | Direct conceptual ancestor of the spec's "3 modes (A 逐章 / B 顺序 / C 并行)". |
| 5-in-1 Checkpoint (script + outline + theme + assets + dev-mode) | `script-contract.json` + `source-manifest.md` + user script-review checkpoint | The "5-in-1" is an expansion of v2's checkpoint to include theme and dev-mode. Add 2 fields to `script-contract.json`. |
| Reviewer / Layer 2 quality | `ratify/{source,script,assets,assembly}-rules.md` exist; Layer 2 was scoped out historically | The "三层降级 Reviewer" (Agent Teams → subAgent → self-check) is the same pattern the v2 SKILL describes in §"Reviewer agent". |
| Theme system | None. Genuine new ground. | Net new — 5 themes × CSS tokens × primitive components. |
| Auto-recording (Playwright) | None. Genuine new ground. | Net new. |
| Vite/React project scaffold | None — Remotion is the renderer. | Net new. |
| End-to-end "watchable video" proof | `pnpm golden:playable` + `final/video.mp4` ratify | Already shipped. |

**Read:** roughly 60% of the new spec is *re-packaging conceptual primitives that already exist in v2*. About 30% is genuine new infrastructure (themes, Playwright, Vite scaffold). About 10% is gravy (more elaborate review chain, more elaborate audio pipeline). **That ratio does not justify deprecating v2 and starting over.** It justifies *extending* v2 with a theme system and a Playwright output mode.

> **Decision needed [DEC-COEXIST]** — Could the same user-visible product surface be achieved by adding to v2 (`scripts/render-playwright.mjs` + `themes/` directory + `narrations.ts` adapter) instead of forking? Estimate of effort under that framing: **8-12 working days**, not 28-32. Most of v2's ratify gates and tests would survive.

### 0C. Dream State Mapping

```
  CURRENT (HEAD = 9380e5d)              THIS BRANCH'S PROPOSAL             12-MONTH IDEAL
  ────────────────────────              ──────────────────────              ──────────────
  v2 runs end-to-end (Remotion)         Deprecate v2.                       One coherent video product:
  Golden playable smoke ✓               Rebuild as Web/Playwright           - One Skill (portable)
  Authoritative UI state ✓              skill from scratch.                 - One DeepAgents Producer
  86 tests green                        ~28-32 working days.                  (orchestrated)
  Publish-readiness gate ✓              Stage 2 (Python integration)        - Multiple render backends
  v2 marked DEPRECATED on the same      explicitly deferred.                  (Remotion + Playwright)
   branch where last week's Stage 1                                         - Theme system, decoupled
   spec was finalized.                  Better-harness deleted.             - Audio is first-class
  Better-harness is dead signal.                                            - Skill is dogfood-able
                                                                             outside DeepAgents
```

**The 12-month ideal is *both* skill-portable *and* DeepAgents-orchestrated. The current proposal optimizes only for portable and explicitly puts orchestrated integration in Stage 2.** That's a sequencing argument, not a destination argument — and it's the right time to challenge whether sequencing the right way is "extend v2 to be portable" (8-12 days, keep DeepAgents working throughout) vs "build new skill, then integrate" (28-32 days + Stage 2 of unknown duration, DeepAgents-integrated path goes dark in the interim).

### 0C-bis. Implementation Alternatives (MANDATORY — at least 2, 3 preferred)

I'm treating "the strategic question" as the plan to review here, not any single small change. The three approaches:

```
APPROACH A: HARNESS DELETION + V2 CONTINUATION (minimal viable)
  Summary: Execute T0 from the new spec (delete better-harness + harness/),
           STOP. Spend the next 2-3 weeks polishing v2: more end-to-end demos,
           a real Anthropic-blog input run, manual taste-review tightening.
  Effort:  S (3-5 days for T0; weeks of incremental v2 polish are already
           the de-facto workstream)
  Risk:    LOW — keeps shipping code intact, no contract churn.
  Pros:    - Preserves all 86 tests and all 2,872 LOC of scar tissue.
           - Resolves the "broken signal" pain immediately.
           - Lets the team prove product value with real video runs before
             committing to a rewrite.
           - Compatible with later pivot if evidence accumulates.
  Cons:    - Does not deliver Skill-portability claim.
           - "We talked about a pivot and didn't do it" can feel like
             indecision to the team.
  Reuses:  All of v2.

APPROACH B: V2-EXTENSION TO MULTI-BACKEND (recommended, ideal architecture)
  Summary: Delete better-harness. Keep v2 as-is. Add three things on top:
           1. `skills/video-maker-v2/themes/` (5 theme tokens)
           2. `scripts/render-playwright.mjs` as a second renderer behind the
              same `vm_render_remotion_project`-style gate
              (rename → `vm_render_video` with `renderer={remotion|playwright}`).
           3. `narrations.ts` adapter that reads from existing
              `script.md`/`audio-manifest.json`.
  Effort:  M (8-12 working days for the additive surface; existing tests
           untouched, plus ~10 new tests).
  Risk:    MEDIUM — touches the renderer abstraction, but does not break
           current users since Remotion remains the default.
  Pros:    - Delivers Skill-portability *and* DeepAgents integration in one
             pass; no Stage 2 latency.
           - Keeps the 86 tests as a regression net throughout.
           - Themes and `narrations.ts` are genuinely valuable additions to
             v2 even if Playwright is never enabled.
           - Honors the "Boil the Lake" principle: complete the v2 surface.
  Cons:    - Requires honest abstraction work on the renderer interface;
             tempting to skip and leave both renderers as parallel branches.
           - Forces the team to argue both backends' value publicly.
  Reuses:  All of v2 + most of the spec's theme/narrations/Playwright work.

APPROACH C: FULL PIVOT (the current spec)
  Summary: Execute the full Stage 1 plan as written. Deprecate v2.
           28-32 days. Stage 2 (DeepAgents re-integration) deferred.
  Effort:  XL (5-6.5 weeks documented; realistically 7-9 weeks with
           rediscovered scar tissue).
  Risk:    HIGH — gives up working code; no DeepAgents integration during
           Stage 1; no fallback if the Playwright approach has unforeseen
           ceilings (audio sync, frame timing, headless display quirks,
           CI flakiness, fonts in headless Chromium).
  Pros:    - Cleaner code surface at the end.
           - True skill-portability without orchestration coupling.
           - Forces a complete rewrite, which sometimes resolves accumulated
             debt better than refactor.
  Cons:    - The 28-32 day estimate is the spec author's own number; the
             gstack methodology (which this very spec invokes) warns that
             rebuilds from-zero routinely run 1.5-2.5x the estimate.
           - Two contradictory commits on the same branch in 7 days
             (UI-state landed, then "deprecate the SKILL that depends on UI-state").
           - All current users (anyone running `pnpm golden:playable`) lose
             the supported path during transition.
           - Stage 2 has no plan, no timeline, no spec. That's the actual
             integration the repo is named after.
  Reuses:  Conceptual primitives only; almost no code.
```

**RECOMMENDATION:** Choose **B (Extension)** because it (a) honors the engineering preference for the smallest diff that achieves the goal, (b) gives the team theme-system + Playwright optionality without burning the working pipeline, (c) keeps DeepAgents integration live throughout, and (d) is reversible — if Playwright proves clearly superior in 6 months, defaulting to it is a one-line config change, *not* a re-platform.

> **Decision needed [DEC-APPROACH]** — Choose A, B, or C. **Do not silently begin T0 of the current spec without choosing.** If choosing C, also commit to a written Stage 2 timeline before T1.

### 0D. Mode-Specific Analysis — HOLD SCOPE (with pivot decision pending)

While the pivot decision is pending, scope is **the current v2 polish workstream as it stood at `17c032e` (pre-pivot-spec).** That means:

**Complexity check.** The pivot spec touches everything (skill files, harness, ratify, tests, docs, CLAUDE.md). Touching everything at once on a branch that *also* contains UI-timeline polish commits is a red flag. Recommend isolating the pivot decision (DEC-PIVOT, DEC-COEXIST, DEC-APPROACH) on its own branch, separate from `claude/gracious-gates-yVhq9`. The current branch should ship the UI/script-flow improvements through master first.

**Minimum set to ship the *current* increment.** Looking at `17c032e` through `9380e5d`, the only commit that meaningfully changes scope is the spec one. The other commits are coherent v2 hardening. Recommend:
- Cherry-pick / rebase `9380e5d` (the spec commit) onto its own branch `feat/web-port-spec` for separate review.
- Ship `17c032e` and ancestors on the current branch.

**Things that could defer (TODOS.md):**
- `tests/evals/` — legacy, not loaded, not referenced. Either delete or move to `tests/_archive/evals/`.
- `harness/` — once the harness-deletion decision lands, delete the directory in one commit.
- Long-form Chinese design docs — link from `README.md` so non-Chinese-reading reviewers can navigate.

### 0E. Temporal Interrogation

- **What does this look like in 6 months under each approach?**
  - **A:** Repo is the same as today, slightly cleaner (no harness). Team has shipped 2-3 polished end-to-end videos. Decision-point about pivot is informed by evidence.
  - **B:** Repo has two renderer backends, a theme system, a `narrations.ts` adapter. Skill is portable AND DeepAgents-orchestrated. CI matrix is slightly larger but tests are mostly the same.
  - **C:** Repo has `skills/video-maker/` (web) usable as standalone skill. `skills/video-maker-v2/` is deprecated but still in `git log`. DeepAgents integration is in some state of Stage 2 progress. Two skills coexist in CLAUDE.md.
- **What does this look like in 12 months?**
  - **A:** Probably *some* pivot toward web rendering, but argued from product evidence, not architectural anxiety.
  - **B:** Probably defaulted to whichever renderer wins user preference. Theme system is mature. The DeepAgents value proposition is intact.
  - **C:** Depends entirely on Stage 2 quality. If Stage 2 is rushed, the repo's name (`deepagents-video-maker`) becomes ironic — there is no DeepAgents path. If Stage 2 is done well, parity with B at higher cost.

### 0F. Mode Selection

**Selected mode: HOLD SCOPE.** Current v2 work continues. Pivot decision is gated on three written decisions above. No expansions are silently absorbed.

---

## Review Sections

The skill specifies 11 review sections. I'm running them against the **current v2 codebase as the baseline**, not against the proposed pivot (since the pivot is not yet code).

### Section 1: Architecture Review

**Strengths:**
- **Controller-only orchestration is paying off.** `agent.py` is 102 lines. Tool routing happens in `langchain_tools.py` via 9-12 typed gated tools, not in LangGraph nodes. The "we don't hand-roll DAG transitions" bet has held.
- **Middleware-driven UI projection.** `VideoMakerUiStateMiddleware.wrap_tool_call` intercepts every `vm_*` tool result and computes `video_maker` state authoritatively from `state.yaml`. This is the right architecture — the UI is a reader, never a writer.
- **Gated milestones with explicit `script_approved=True` parameter.** `vm_start_build_scenes(script_approved=True)` makes the human-in-the-loop step a typed function argument rather than an implicit producer convention. Cannot be silently skipped.

**Concerns:**
- **`build_render_flow.py` is 514 LOC** — the largest file. Conflates Build Scenes ratify, Render Package ratify, ffprobe duration check, and Publish Readiness emit. Suggest splitting into `build_scenes_flow.py` / `render_package_flow.py` / `publish_readiness.py`. Right-sized today; will get worse with each new gate.
- **`langchain_tools.py` is 554 LOC** — partly because tool docstrings double as producer-facing docs. Consider extracting docstrings into a single `tool_docs.py` table and keeping `langchain_tools.py` to wiring only. Reduces visual noise during review.
- **`middleware.py:40` `except Exception: pass` silently swallows projection errors.** Comment explains "Never break the tool call itself because the UI projection failed." Correct policy, **wrong implementation** — silent. Add `logging.warning(..., exc_info=True)` so the failure is debuggable. Currently violates Prime Directive 1.
- **`middleware.py:51` async path has the same silent-pass.** Same fix.

```
            [LangGraph thread state]
                     ▲
                     │ video_maker={…}  (Command.update)
                     │
       ┌─────────────┴─────────────┐
       │ VideoMakerUiStateMiddleware│
       │ wrap_tool_call             │
       └─────────────┬─────────────┘
                     │ build_video_maker_ui_state(output_dir)
                     ▼
            [ui_state.py]
              reads state.yaml
              reads ratify/*.json
              reads final/publish-readiness.{md,json}
                     ▲
                     │ writes by:
                     │
       ┌─────────────┴───────────────────────┐
       │  vm_* tools in langchain_tools.py   │
       │  source_flow / script_flow /         │
       │  build_render_flow                   │
       └─────────────────────────────────────┘
```

> **Decision needed [DEC-MIDDLEWARE-LOG]** — Replace the two `except Exception: pass` blocks in `middleware.py` with explicit logging. 10-minute fix. Should land before any further middleware work.

### Section 2: Error & Rescue Map

This is the highest-leverage section per the skill priority hierarchy. I'll enumerate every error path I traced. Names matter.

| Error Name | Trigger | Catch | User-visible | Tested? |
|---|---|---|---|---|
| `MilestoneOutOfOrderError` (informal — returned dict, not raised) | Calling `vm_render_remotion_project` before `build_scenes=completed` | Returned `{"error": "..."}` from build_render_flow guard | Producer sees error string | **Yes** (prior eng review fix) |
| `RatifyFailureError` (informal) | Ratify rule violation in script/source/render | Returned dict with `passed: False`, errors list | Producer sees structured failure | Yes (`test_ratify_script.py`) |
| `ScriptApprovalMissing` (informal) | `vm_start_build_scenes(script_approved=False)` | Returned error dict | Producer must explicitly pass True | Yes (`test_build_render_flow.py`) |
| `FfprobeMissing` | `ffprobe` not on PATH | Render ratify falls back to size-only check (deliberate per workflow-contract) | Warning in ratify JSON | Partially (smoke test handles missing case) |
| `FfmpegMissing` | `ffmpeg` not on PATH | `scripts/run_golden_playable_smoke.py` raises `SystemExit` with explicit message | Test exits with clear error | Yes |
| `TavilyMissing` | `TAVILY_API_KEY` unset, source=websearch | `vm_websearch` tool error path | Tool returns failure message | Yes (test suite handles) |
| `ToolCallDropout` | Producer model emits pseudo-tool-call markers | `detect_tool_call_dropout` + `block_if_tool_call_dropout` | Producer is blocked with named error | Yes (`test_tool_call_dropout_detection.py`) |
| `UIProjectionFailure` | `ui_state.build_video_maker_ui_state` raises (corrupted state.yaml, missing field) | `middleware.py:40` swallows silently | **Silent — Prime Directive 1 violation** | No |
| `StateYamlParseError` | Custom hand-rolled YAML parser hits malformed input | `state_store.load_state_yaml` raises | Depends on caller | Partial |
| `WindowsPathSeparator` | Path comparison cross-platform | `tests/test_windows_path_normalization.py` | N/A (test only) | Yes |
| `RemotionRendererMissing` | `pnpm` / Node tooling missing or Remotion fails | Returned error dict; render-command JSON captures stderr | Producer + ratify JSON | Yes (`test_build_render_flow.py`) |
| `PublishReadinessNotReviewed` | No reviewer has filled the form | `publish-readiness.json.status = "not_reviewed"` (deliberate default) | UI shows "not_reviewed" badge | Yes (`test_artifact_gates.py`) |

**Findings:**
1. **The informal-error pattern (return error dict instead of raising) is consistent across the v2 flow.** Good — it works well with LangChain tools because exceptions don't propagate cleanly through tool calls. But it means error introspection is by string matching. If you ever want to programmatically retry or branch on a specific error, you'll wish for an enum. Not urgent; flag for the 6-month checkpoint.
2. **Two silent-failure spots** (`middleware.py:40`, `middleware.py:51`) are the only Prime Directive 1 violations I found. Fix per DEC-MIDDLEWARE-LOG.
3. **`state.yaml` corruption is under-tested.** What happens if a process is killed mid-write? The hand-rolled YAML writer is not atomic (no temp-file + rename). Suggest `state_store.save_state_yaml` write to `state.yaml.tmp` then `os.replace`. Without this, a power failure during a long render can leave state.yaml truncated — `load_state_yaml` then raises on the next agent boot, with no clear user message.
4. **Tavily missing key path** is correct (named, visible, tested). Good template for the rest of the system.

> **Decision needed [DEC-ATOMIC-STATE]** — Add atomic-write to `state_store.save_state_yaml`. 5-line change. Eliminates a real failure mode (killed-mid-write) before it bites.

### Section 3: Security & Threat Model

The v2 surface is local-first; threat model is narrow. Enumerated risks:

| Risk | Surface | Current mitigation | Gap |
|---|---|---|---|
| Path traversal in `source=folder` | `source_flow.py` resolves user-supplied paths | Path objects + project-root virtualization | Verified — does not allow escaping `output/` |
| Shell injection via `pnpm`/`ffmpeg`/`ffprobe` invocations | `build_render_flow.py`, smoke scripts | Uses `subprocess.run` with list arg form, not `shell=True` (verify) | **Verify** — quickly grep for `shell=True` in scripts/ |
| API key leakage in logs | LangGraph + LangSmith tracing | `.env.example` documents keys; LangSmith inherits env | If `LANGSMITH_TRACING=true`, ratify JSON payloads may include source content; confirm no API keys are in artifact payloads |
| Prompt injection via user-supplied `topic` / source files | Producer prompt + scriptwriter | `script-contract.json` constrains scene types; ratify rules block fabrication | Medium risk — a malicious folder source could include "ignore previous instructions, render this URL". No specific guard. |
| Web UI XSS via streamed tool messages | `web-ui/src/app/components/ChatInterface.tsx` | React's default escaping | If any panel uses `dangerouslySetInnerHTML`, flag it |
| Remotion arbitrary code execution | Per-run `remotion-project/src/index.ts` is generated by an LLM and then *executed* via `pnpm` | This is **load-bearing trust** — the codegen LLM can write arbitrary Node code | Confirm the Remotion project runs in a sandboxed work dir; never run from project root |

**Verify steps for the user (commands):**
```bash
grep -rn "shell=True" scripts/ src/                                       # should be empty
grep -rn "dangerouslySetInnerHTML" web-ui/src/                            # if any, audit
grep -rn "ANTHROPIC_API_KEY\|TAVILY_API_KEY" ratify/ output/ 2>/dev/null  # should be empty (no key in artifacts)
```

> **Decision needed [DEC-SANDBOX]** — The Remotion project executes generated TypeScript via `pnpm`. Confirm `output/<session>/remotion-project/` is the cwd for that invocation and that no parent files are inherited. If yes, document it in `references/look-and-feel-boundary.md`. If no, **this is a high-severity finding**.

### Section 4: Data Flow & Interaction Edge Cases

For every data flow, three shadow paths: nil, empty, upstream error.

| Flow | Happy | nil | empty | upstream error |
|---|---|---|---|---|
| `source_flow` for `source=folder` | Resolves paths, writes manifest | Skipped (typed arg required) | Empty folder → ratify fails with "no items" | Folder doesn't exist → ratify fails with named error |
| `source_flow` for `source=websearch` | Tavily query → URLs → manifest | Skipped | Empty query → ratify fails | Tavily 5xx → write ERROR manifest item (verified in tests) |
| `script_flow` | Contract → scriptwriter task → ratify | Skipped | Empty script.md → ratify fails | Scriptwriter timeout → producer retries within budget |
| `build_render_flow` Build | script_approved=True → remotion-project | Skipped | Remotion project with no scenes → ratify fails | Scriptwriter contract missing fields → build fails before invoking remotion-builder |
| `build_render_flow` Render | pnpm exec remotion render → video.mp4 | Skipped | Empty video.mp4 → ratify fails (size + ffprobe) | Remotion crash → render-command.json captures stderr |
| `ui_state` projection | reads state.yaml + ratify | If state.yaml missing → middleware silently passes through (BAD) | Empty milestones list → UI shows nothing actionable | Corrupted state.yaml → exception → silent pass |

**Interaction edge cases (user-visible):**
- **Double-click "Approve script"** — what happens? Need to verify `vm_start_build_scenes` is idempotent for the second call. Likely safe (gate checks state) but no explicit test.
- **Navigate-away mid-render** — render keeps going; user returns and timeline shows progress. ✓ (UI state read-only from `state.yaml`)
- **Stale state** in UI — `useChat` hook subscribes to LangGraph stream; middleware emits `video_maker` on every tool call. Latency = one tool call. Good.
- **Back button** during script review — should re-load `video_maker` from current thread state. ✓
- **Empty topic** — `params.parse_video_request` should reject. Verify in `test_params.py`. ✓

### Section 5: Code Quality Review

- **DRY:** Single largest violation surfaced in last CEO review (path virtualization in 3 places) was **resolved** in subsequent commits. ✓
- **`controller.py`** still contains `block_if_tool_call_dropout` — this is the v2 producer's load-bearing safety guard. Confirmed in tests. Good.
- **Hand-rolled YAML** — `state_store.py` is still ~193 lines of hand-rolled YAML I/O while `PyYAML` is in dependencies. **This was the #2 finding in the prior CEO review and remains unaddressed.** Recommend tackling it before the pivot decision (any pivot inherits this debt). PyYAML `safe_dump`/`safe_load` would cut this to ~30 lines.
- **Imports inside functions** (`agent.py:57` does `from deepagents import …` inside `create_video_maker_agent`). Deliberate for optional-dep handling, but worth a comment because reviewers will flag it.
- **Type hints are consistent** across the codebase. `models.py` uses dataclass+enum. Good.

> **Decision needed [DEC-PYYAML]** — Replace hand-rolled YAML in `state_store.py` with PyYAML `safe_dump`/`safe_load`. ~120 LOC reduction. Should land **before** any pivot decision so the debt does not transfer.

### Section 6: Test Review

- **86 tests, all green** (excluding the ffmpeg-dependent test in this sandbox).
- **Coverage shape:** factory, langchain tools, controller, prompts, params, session, state-store, source-flow, script-flow, build-render-flow, ratify-script, artifacts, ui-state, tool-call-dropout, windows-path, golden-demo smoke, skill-files.
- **Missing tests:**
  - `ui_state.py` projection under corrupted `state.yaml` (related to DEC-MIDDLEWARE-LOG).
  - `state.yaml` atomic-write race (related to DEC-ATOMIC-STATE).
  - Double-call idempotency on `vm_start_build_scenes` after script approval.
  - Round-trip serialization for `MilestoneState.ratify` payload (prior eng-review flagged that ratify is not persisted via `save_state_yaml`).
- **`tests/evals/` legacy directory** — 9 files referencing research-era contract. Not in `pyproject.toml.testpaths`. Recommend `git mv tests/evals tests/_archive/evals` so the rot is visible.
- **No explicit performance/concurrency tests** — acceptable for a single-user local tool. Document this consciously rather than implicitly.

### Section 7: Performance Review

- Local-first single-user pipeline; performance ceiling is dominated by LLM latency + Remotion render time, not Python.
- `state.yaml` read/write happens **per tool call** via `ui_state.build_video_maker_ui_state(output_dir)`. For a multi-minute render this is fine. For a workflow with hundreds of tool calls per session, this could be ~100ms × N. Not a problem today; flag if tool-call volume grows 10×.
- LangGraph callbacks (`LANGCHAIN_CALLBACKS_BACKGROUND=false`) — synchronous by config. Worth re-evaluating once LangSmith tracing is regularly enabled.
- ffprobe duration check is per-render, ~200ms. Negligible.

### Section 8: Observability & Debuggability Review

This is the section the codebase under-invests in.

- **No structured logging.** The middleware silently swallows exceptions (Section 1, 2). LangSmith tracing helps if enabled, but is not a substitute for service-level logs.
- **Ratify JSON is the only persistent observability artifact.** It captures the "what passed/failed at the gate" but not "what the producer attempted on the way to the gate."
- **No timing telemetry.** How long did source intake take? Scriptwriter? Build? Render? Currently inferred from tool-message timestamps in the LangGraph trace.
- **Tool-call dropout detection is excellent observability** — named, tested, blocks loudly. This is the right pattern to repeat elsewhere.

**Recommendation:** add a `logs/<session>/producer.log` (already in `.gitignore`) with INFO-level entries from each `vm_*` tool entry + exit. Cost: 1-2 hours. Benefit: every future bug report has a log to attach.

> **Decision needed [DEC-LOGS]** — Add per-session producer logs. 30-line change. Major debuggability win.

### Section 9: Deployment & Rollout Review

- This is a local CLI + local web UI. No deployment surface beyond `git pull && uv sync && pnpm install`.
- CI: GitHub Actions runs `uv run pytest`, smoke scripts, and `pnpm --filter ... lint`. ffmpeg is installed in CI per the recent fix.
- Rollback story: every change is in git. Simple.
- Feature flags: not needed at this size.
- **Risk:** the proposed pivot would create a *transition period* where v2 is deprecated but `skills/video-maker/` is incomplete. **This is a rollout concern.** Recommend the pivot, if accepted, preserve `golden:playable` and `golden:script` as green smoke checks against v2 *throughout* Stage 1 — i.e., don't delete v2 surfaces until Stage 1's web pipeline produces equivalent artifacts.

### Section 10: Long-Term Trajectory Review

**6-month view:**
- The repository name (`deepagents-video-maker`) implies "use DeepAgents to make video." That story is **strong today** (controller-only, gated milestones, ratify JSON, UI authoritative). Approach C (full pivot) puts that story on pause for 5-7 weeks while Stage 1 ships a non-DeepAgents skill. Approach B keeps it live.
- Better-harness deletion is the right move regardless of approach.
- The `feature-pipeline` SKILL is *itself* an interesting strategic asset — a meta-orchestrator that calls gstack-style sub-skills. If the team values portability, the meta-pipeline may be a better evangelism vehicle than rebuilding the video skill.

**Architectural smells, recurring:**
- Hand-rolled YAML (twice now in CEO reviews).
- Silent exceptions in middleware (new this review).
- The Producer prompt is large and growing. Eventually needs a SKILL.md routing layer separate from the `vm_*` tool guarantees.

**Strategic trip-wires (when to revisit):**
- If `block_if_tool_call_dropout` fires more than once per 10 sessions, the controller-only architecture is straining; consider thin LangGraph milestone-transition nodes.
- If users report wanting Web-recording output, **and** the gap is not closable by Playwright-as-a-second-renderer, that's the signal to pivot.
- If Stage 1 of the pivot ships and DeepAgents integration is not on a planned timeline within 30 days, expect the repo to fork de facto into two products.

### Section 11: Design & UX Review (skipped — no UI scope changes in this review)

`web-ui/src/app/components/VideoProductionTimeline.tsx` exists and per `17c032e` now handles interrupted state. Not reviewing pixel-level UX in this pass. Defer to `/plan-design-review` if the team wants it.

---

## Outside Voice — Independent Plan Challenge (synthesized)

Imagining a skeptical outside engineer reading the new spec cold:

> *"You're seven days from your previous CEO review scoring this 7.5/10 and resolving every flagged finding. The very next commit on the same branch proposes deleting the SKILL those findings improved. The spec opens with 'better-harness is broken' — fine, delete the harness. But then it pivots to 'and therefore rewrite the skill in Vite + React + Playwright' without arguing the second claim on its own merits. Five to seven weeks. Stage 2 (the part that actually integrates with DeepAgents, which is what this repo is for) is unscoped. Are you sure the harness frustration isn't bleeding into broader architectural anxiety? Be honest with yourself about which problem you're actually solving."*

That voice is essentially saying what I'm saying in DEC-PIVOT and DEC-APPROACH. Two independent reads agree.

---

## CRITICAL RULE — Decisions, not directives

Per the skill, every scope change is the user's call. The decisions are itemized below, each with a recommendation and the tradeoff.

### Decision needed [DEC-PIVOT]

**Q:** Is "deprecate v2 and rebuild as Web/Playwright" the right strategic move, or is it scope drift?

**Options:**
- **A) Recommend YES.** The Stage 1 spec is correct on its own merits; we have a written one-pager defending it. Proceed with the current spec.
- **B) Recommend NO.** Hold v2. Delete better-harness only. Revisit in 60 days with product evidence.
- **C) Defer.** Write the one-pager (60 minutes); re-decide after reading it.

**Reviewer recommendation: C, then likely B.** The pivot has not been argued on its own merits; it was packaged with a smaller, correct refactor.

### Decision needed [DEC-COEXIST]

**Q:** Could the same product surface be reached by extending v2 (themes + Playwright renderer + `narrations.ts` adapter) at ~8-12 days instead of forking at ~28-32?

**Options:**
- **A) Yes — pursue Approach B from the alternatives section.**
- **B) No — fork is required (must justify why).**

**Reviewer recommendation: A.** This is the smallest diff that achieves the goal *and* preserves DeepAgents integration throughout.

### Decision needed [DEC-APPROACH]

**Q:** Choose A / B / C from the implementation alternatives.

**Reviewer recommendation: B.**

### Decision needed [DEC-MIDDLEWARE-LOG]

**Q:** Replace the two `except Exception: pass` blocks in `src/deepagents_video_maker/middleware.py` (lines 40 and 51) with explicit `logging.warning(..., exc_info=True)`?

**Reviewer recommendation: YES.** 10-minute fix. Prime Directive 1 ("zero silent failures").

### Decision needed [DEC-ATOMIC-STATE]

**Q:** Make `state_store.save_state_yaml` write atomically (temp file + rename)?

**Reviewer recommendation: YES.** 5-line change. Eliminates a real failure mode.

### Decision needed [DEC-PYYAML]

**Q:** Replace hand-rolled YAML in `state_store.py` with PyYAML `safe_dump`/`safe_load`?

**Reviewer recommendation: YES.** Two consecutive CEO reviews have now flagged this. ~120 LOC reduction.

### Decision needed [DEC-SANDBOX]

**Q:** Confirm Remotion code generation executes in a sandboxed cwd (`output/<session>/remotion-project/`) and document it in `look-and-feel-boundary.md`.

**Reviewer recommendation: YES (verify, then document).** If executed at repo root, this is a high-severity finding.

### Decision needed [DEC-LOGS]

**Q:** Add per-session producer logs at `output/<session>/logs/producer.log`?

**Reviewer recommendation: YES.** ~30-line change. Major debuggability win, especially before any pivot decision.

---

## Required Outputs

### "NOT in scope"

- **The full pivot to Web/Playwright** until DEC-PIVOT lands.
- **Stage 2 (DeepAgents re-integration)** — has no spec, no timeline, no acceptance criteria. Cannot be in scope.
- **Better-harness "fix"** — the right action is delete, not fix.
- **Legacy `video-maker` (v1) compatibility** — already excluded by prior decisions. Keep excluded.
- **Automated taste/visual reviewer** — the current `publish-readiness.json.status` default of `not_reviewed` is correct.
- **Cloud deployment / auth hardening** — local product loop first.

### "What already exists"

- `src/deepagents_video_maker/` (18 files, 2,872 LOC) — full v2 producer + gated tools + middleware + UI projection.
- `tests/deepagents_video_maker/` — 17 test files, 86 passing tests.
- `skills/video-maker-v2/` — canonical skill, manifests, ratify rules, agent prompts.
- `skills/feature-pipeline/` — meta-orchestration skill (recent).
- `scripts/run_golden_*_smoke.py` — three golden smokes (script / render / playable).
- `web-ui/` — Next.js + LangGraph UI with timeline component.
- `docs/golden-demo.md` — canonical local demo doc.

### "Dream state delta" (12-month ideal — current = X, branch = Y, ideal = Z)

```
  CURRENT                THIS BRANCH                  12-MONTH IDEAL
  ───────                ───────────                  ──────────────
  v2 healthy             Pivot spec proposed.         Single video product:
  86 tests green         No pivot code yet.            - DeepAgents-orchestrated
  UI authoritative       v2 marked DEPRECATED          - Skill-portable
  Watchable golden       on the same branch where      - Multi-renderer
   playable smoke ✓      it just delivered three        (Remotion + Playwright)
  Better-harness         resolved CEO findings.        - Theme system
   dead signal                                         - Audio first-class
                                                       - Skill dogfood-able
                                                         outside DeepAgents
```

### Error & Rescue Registry

See Section 2 table — 12 named error paths. Two silent-failure violations remain (`middleware.py:40`, `middleware.py:51`).

### Failure Modes Registry

1. **Killed-mid-write `state.yaml`** — `state_store.save_state_yaml` is not atomic. (DEC-ATOMIC-STATE)
2. **Silent UI projection failure** — `middleware.py` swallows exceptions. (DEC-MIDDLEWARE-LOG)
3. **Tavily missing at dispatch time** — handled, but spec audit recommends fail-fast at agent boot when `source=websearch` is intended.
4. **Remotion sandbox unclear** — generated TypeScript executes in unverified cwd. (DEC-SANDBOX)
5. **Pivot half-done** — if Stage 1 ships and Stage 2 is not scheduled, the repo's value proposition forks. Cultural / strategic failure mode, not technical.
6. **Hand-rolled YAML quoting edge cases** — Chinese topics with embedded quotes, multi-line `blocking_reason`, future ratify payload nesting. (DEC-PYYAML)
7. **Double-clicked approval** — likely safe but untested.
8. **Long-running render killed by IDE / shell** — partial `final/video.mp4` could pass size check; mitigated by ffprobe duration band but worth verifying.

### TODOS.md updates (recommended)

```
- Delete `harness/` after pivot decision lands (1 commit).
- Move `tests/evals/` → `tests/_archive/evals/` (visibility for legacy).
- Replace hand-rolled YAML in state_store.py with PyYAML (DEC-PYYAML).
- Add atomic-write to save_state_yaml (DEC-ATOMIC-STATE).
- Replace `except Exception: pass` in middleware.py with logged warning (DEC-MIDDLEWARE-LOG).
- Verify + document Remotion sandbox cwd (DEC-SANDBOX).
- Add per-session producer log (DEC-LOGS).
- Translate spec headers in `specs/video-maker-web-port/stage-1-skill/*.md` to bilingual (or add English summary at top) — currently a barrier to non-Chinese reviewers.
- Re-evaluate the controller-only architecture after the next 5 sessions: count tool-call-dropout fires; if > 1, reconsider thin LangGraph nodes for milestone transitions.
```

### Scope Expansion Decisions (deferred)

Three pivot-related decisions (DEC-PIVOT, DEC-COEXIST, DEC-APPROACH) gate any scope expansion. All other proposals are improvements **within** the existing v2 scope.

### Diagrams

#### Decision tree for the pivot

```
                  Should v2 be deprecated?
                       /          \
                      /            \
        Has one-pager been         No one-pager yet
        written defending the          |
        pivot on its own              GO WRITE IT (60 min)
        merits?                        |
            /    \                     |
           YES    NO  ─────────────────┘
            |
       Read it. Convincing?
            /         \
          YES          NO
           |            \
       Approach C       Approach B
       (full pivot)     (extension)
                        ←—— recommended path
                         in most cases
```

#### Renderer abstraction (Approach B sketch)

```
   ┌─────────────────────────────────────┐
   │       vm_render_video(renderer=…)   │
   └──────────┬──────────────────────────┘
              │
        ┌─────┴─────┐
        │           │
        ▼           ▼
  renderer:    renderer:
  remotion     playwright
        │           │
        ▼           ▼
  pnpm exec    Vite+React
  remotion     served, then
  render       Playwright captures
        │           │
        └─────┬─────┘
              │
              ▼
   ratify/render-package.json
   (renderer-agnostic schema)
              │
              ▼
   final/video.mp4
```

### Stale Diagram Audit

- `docs/design/2026-04-25-deepagents-native-video-maker-implementation.md` still references the four-milestone (`research → script → assets → assembly`) state machine. The current implementation is `source_intake → script → build_scenes → render_package`. Either update the design doc or mark it `superseded-by:` `docs/golden-demo.md`. **Stale diagrams are worse than none** — Engineering Preference #11.

---

## Completion Summary

- **Mode:** HOLD SCOPE on v2 + premise challenge on the proposed pivot.
- **Premise challenges raised:** 3 (better-harness ≠ Remotion-replacement; skill-portability as product virtue; Web recording ≠ simpler).
- **Implementation alternatives:** 3 (A: harness-only delete; **B: extension to multi-renderer — recommended**; C: full pivot per current spec).
- **Architectural smells, recurring:** hand-rolled YAML (2nd review), silent exceptions in middleware (new).
- **Prime Directive 1 violations:** 2 (middleware.py:40, :51).
- **Prior CEO findings status:** 3/3 resolved.
- **Test health:** 86/87 green (1 ffmpeg-dependent skip in this sandbox).
- **Decisions pending user response:** 8 (DEC-PIVOT, DEC-COEXIST, DEC-APPROACH, DEC-MIDDLEWARE-LOG, DEC-ATOMIC-STATE, DEC-PYYAML, DEC-SANDBOX, DEC-LOGS).
- **Critical gaps:** 1 (pivot decision must be made before any T0 tasks in `specs/video-maker-web-port/`).
- **Product score:** **8.0 / 10** (up from 7.5).
  - +0.5: all three prior CEO findings resolved.
  - +0.3: middleware-driven UI projection is a strong architecture.
  - -0.3: pivot decision overhangs the codebase; hand-rolled YAML and silent middleware errors remain.

## Recommended Next Work Order

1. **Make DEC-PIVOT, DEC-COEXIST, DEC-APPROACH explicitly.** Write the one-pager. Decide on Approach A / B / C. Do not begin T0 of the current spec without this.
2. **DEC-MIDDLEWARE-LOG + DEC-ATOMIC-STATE + DEC-PYYAML.** Three small, high-leverage fixes. Land them on master regardless of pivot decision — they are improvements that any future Approach inherits.
3. **DEC-SANDBOX verification.** Important for security posture, especially if web rendering adds further codegen-and-exec surface area.
4. **DEC-LOGS.** Cheap, large debuggability gain.
5. **Move `tests/evals/` to archive.** One commit. Removes ambiguity about whether eval scripts are live.
6. **Update or supersede the stale 4-milestone design doc.**
7. **Only then, if Approach B was chosen:** start the renderer-abstraction work (themes scaffold + Playwright second renderer + `narrations.ts` adapter).
8. **Only then, if Approach C was chosen:** scope Stage 2 *before* starting Stage 1. The repo's value proposition cannot go dark without a written re-entry plan.

---

*Review produced by adapting the `gstack/plan-ceo-review` v1.0.0 skill methodology for non-interactive written delivery. All interactive AskUserQuestion ceremonies are rendered as "Decision needed" blocks above. 11-section framework, prime directives, cognitive patterns, and required outputs preserved.*
