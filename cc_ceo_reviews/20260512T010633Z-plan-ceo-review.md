# CEO Review — deepagents-video-maker

- **Date:** 2026-05-12 01:06:33 UTC
- **Branch:** `claude/gracious-gates-5F4bT`
- **HEAD:** `9380e5d` — feat(skill): implement Stage 1 plan for video-maker skill with detailed task breakdown and acceptance criteria
- **Reviewer skill:** `gstack/plan-ceo-review` v1.0.0 (https://github.com/garrytan/gstack.git), adapted for **non-interactive written delivery** — the skill's interactive `AskUserQuestion` ceremonies are converted to written recommendations the user can react to. The CEO posture, Prime Directives, Cognitive Patterns, 11-section framework, and required outputs are preserved.
- **Mode selected:** **HOLD SCOPE with one strategic decision pending.** The branch under review hardened v2 (timeline interrupted state, ratify serialization, websearch grounding, README rewrite) and *also* landed a written Stage-1 spec that proposes deprecating `video-maker-v2` (Remotion route) in favor of a new `video-maker` (Web/Playwright recording route). Hardening is HOLD; the deprecation proposal is a **Scope Inversion** that I am surfacing as the central CEO decision rather than absorbing or rejecting silently. Per skill §0F, this gets called out explicitly: **the team is one click away from invoking Permission #9 ("scrap it and do this instead") on the entire v2 Remotion path right after the playable golden tier just landed.** That decision is irreversible enough to warrant a stop-and-think.
- **Posture:** Rigorous reviewer. Zero silent failures. Every error has a name. Diagrams mandatory. Permission #9 is on the table.

---

## 0. Pre-Review System Audit

### Repository state

- **Branch:** `claude/gracious-gates-5F4bT`, working tree clean, HEAD `9380e5d`.
- **Tests:** 86 passed / 1 failed (`test_golden_playable_smoke_produces_probeable_mp4` — fails because `ffmpeg` is not installed in the *review sandbox*; the test itself is correct, CI installs ffmpeg in `.github/workflows/ci.yml:24-27`).
- **Python source:** 18 modules, ~2,872 LOC (`src/deepagents_video_maker/`). Up from ~1.7k LOC at the 2026-05-09 review — the delta is build/render flow, source flow with Tavily caching, UI state projection, and middleware.
- **Tests:** 17 test files, 87 collected. Coverage spans agent factory, artifact gates, build/render flow, controller, golden demo smoke, langchain tools, params, prompts, ratify, research_flow (legacy hygiene), script_flow, session, skill files, state store, tool-call dropout, UI state, and Windows path normalization.
- **Tool surface:** 17 typed `vm_*` tools across the full Source Intake → Script → Build Scenes → Render Package → Publish Readiness pipeline. Build Scenes and Render Package are now wired with real `pnpm exec remotion render` / `remotion still` commands.
- **Web UI:** 12 React components (~3,349 LOC TSX/TS combined), including `VideoProductionTimeline.tsx` which renders milestone state from `stream.values.video_maker`.
- **Specs / plans:**
  - `docs/plans/20260507-220336-p0-p1-video-productization-plan.md` — the P0/P1 productization plan that this branch executes.
  - **NEW:** `specs/video-maker-web-port/stage-1-skill/{requirements,design,tasks}.md` — 3,465 lines of new spec proposing the Web-recording pivot.
  - `specs/video-maker-v2-harness-upgrade/*.deprecated.md` — already marked deprecated.

### What changed since the last CEO review (2026-05-09 09:06 / branch `claude/integrate-better-harness-optimization`)

Five commits land between the last CEO review and this one. Reading them in chronological order:

1. **`6a49197`–`93bf38a`** (CI + Windows path normalization + .gitignore + build-ui script) — finishes the productization plan's tail end and stabilizes CI.
2. **`82cf0c5` + `a446705` + `26975a7` + `7d896d4`** (assorted script_flow / contract / Windows-path / merge) — closes the script-contract write-on-start vs write-on-task race that previously clobbered run-1 contracts.
3. **`3b719dd`** (one-line fix) — `data_card_grounding` regex now accepts indented `items:` under `data_semantic:`. **Worth its own mention in this review:** the bug caused infinite script-ratify loops on any data_card scene. That is exactly the kind of silent-failure-by-loop the skill's Prime Directive #1 forbids; the fix is right, but the fact that this regressed past test coverage tells me the ratify suite is happy-path heavy. See §6.
4. **`7b61660`** — Tavily depth bumped to `advanced`, snippet capped at 2000 chars (was 240), `vm_websearch` exposed as a separate typed tool that caches `websearch-results.json` so `vm_ratify_source_intake` reuses one API call. Scriptwriter prompt now has an explicit two-step grounding check and a `websearch`-specific rule that says "if the note doesn't contain the number, the number doesn't exist." **This is exactly the right CEO move** — fabrication guards belong upstream of the scriptwriter, not in post-hoc ratify.
5. **`17c032e`** — Timeline `interrupted` state now renders with `PauseCircle` + amber (was rendering as pending — a UI lie). Artifact card labels are now human-readable. `ui_state` projection failures are logged instead of swallowed. `milestone.ratify` now serializes/deserializes through `state.yaml` (was silently dropped on round-trip — a state-store correctness bug). RuntimeError messages now include `Fix:` guidance. README Quick Start leads with `pnpm golden:playable`.
6. **`0b6f3f7`** — VSCode launch / task configs; non-load-bearing.
7. **`9380e5d`** — the **Stage-1 spec landing** discussed above.

Net assessment: the M2 ratify/UI work is real progress on operator trust. Then the team landed a spec that proposes throwing away the entire v2 surface (skill, agents, references, Remotion) and replacing it with a Web+Playwright skill. **That's the central decision now.**

### Recently touched files (signal: where attention is going)

`source_flow.py`, `langchain_tools.py`, `producer.md`, `scriptwriter.md`, `ratify.py`, `state_store.py`, `build_render_flow.py`, `VideoProductionTimeline.tsx`, then `specs/video-maker-web-port/stage-1-skill/*`. Attention shifted in the last two commits from "make v2 trustworthy" to "design v2's replacement." Both are happening on the same branch.

### Design / spec docs check (skill PRE-REVIEW system audit)

- **`docs/golden-demo.md`** — current source of truth for the local demo ladder (script checkpoint → simulated render → playable MP4). Referenced by README and AGENTS.md.
- **`docs/plans/20260507-220336-p0-p1-video-productization-plan.md`** — P0/P1 plan that defined the work this branch executes.
- **`specs/video-maker-web-port/stage-1-skill/{requirements,design,tasks}.md`** — the new web-port spec. 75 tasks across T0–T8, ~28–32 working-day budget. Requirement 0 alone removes `harness/`, `runs/`, `harness:*` package scripts, and marks `skills/video-maker-v2/` as `[DEPRECATED]` in its frontmatter.

### Existing review log

- `cc_ceo_reviews/20260509T012631Z-plan-ceo-review.md` — pre-v2-pivot CEO review of the previous branch.
- `ceo_reviews/20260509-090645-ceo-review.md` — most recent automated CEO review. Verdict was `issues_open`: playable golden tier is good; live UI proof and production `pnpm ui:build` were unresolved. Both remain open in this run.

### Retrospective check

Recurring problem areas:
1. **Windows production `pnpm ui:build` (`spawn EPERM`)** — still flagged in the 2026-05-09 review; no commit on this branch claims to fix it.
2. **Live UI proof of a real LangGraph thread driving the timeline** — still no captured browser-side evidence.
3. **`workflow-contract.md` audio milestone** — referenced by the v2 SKILL.md as optional but no native audio milestone exists; the new web-port spec moves audio into a `narrations.ts` single-source-of-truth model (Stage 1) but doesn't yet specify how Stage 2 will reconcile.

These three are architectural smells. (1) and (2) are operator-trust gaps; (3) is a scope-clarity gap. The pivot decision interacts with all three.

---

## Step 0: Nuclear Scope Challenge + Mode Selection

### 0A. Premise Challenge — is this the right problem?

The implicit premise of the project, restated honestly:

> "Build a DeepAgents-native Producer that drives a Source-Intake → Script → review → Build → Render → Publish-Readiness pipeline, with deterministic ratify gates and a chat-UI timeline, so one operator can produce one publishable short video from a topic and source material."

The new spec adds a second, *incompatible* premise:

> "The Remotion route is too brittle / too low-leverage; instead, generate a Vite + React + TypeScript single-page presentation, drive auto-advance from `narrations.ts`, record it with Playwright, and produce the same publishable MP4."

Three premises worth challenging at the CEO level:

1. **"Remotion is the right rendering substrate."** The v2 path bet on Remotion because it gives programmable composition, declarative scene durations, and `npx remotion render` as a deterministic CLI. Reality: the team has now built `remotion-project/` scaffolding, audio-driven scene-duration rules in `remotion-builder.md`, mandatory subtitle overlays in the Builder prompt, and is wrestling with Windows `spawn EPERM` issues even before the visual layer is hardened. The new spec's framing is essentially "Remotion is high-ceiling but high-tax; web recording is lower-ceiling but the tax is near-zero because you're shipping a webpage that humans already know how to inspect and theme." **That's a real bet, not a fashion choice.** But the data point that should actually drive the decision is missing: *has anyone shipped a credible publishable video through the current Remotion path on a real story, not the golden demo?* Until that exists, both paths are speculation. The team should not abandon v2 on aesthetic grounds. If the answer is "no, the golden playable is the only thing rendered," then v2 hasn't proven itself, and pivoting is rational. If the answer is "yes, we made an internal explainer last week," then deprecating v2 right after it proves itself is premature subtraction.

2. **"Stage 1 ships as a Python-free, DeepAgents-free, distributable skill — and Stage 2 will adapt the Python tools later."** This is the spec's most aggressive premise. It says the new `skills/video-maker/` must be installable by *any* Claude Code / Cursor / Codex user with no Python and no DeepAgents. **That decouples the skill from the project's reason to exist.** This project is `deepagents-video-maker`. Its differentiator is the controller-only DeepAgents producer + typed tools + ratify gates + UI timeline. A skill that runs fine without any of that is not the project; it's a *separate skill that happens to live in the same repo until Stage 2.* Two ways this can go: (a) the pivot is genuinely a "rebuild from the skill outward, then re-wire Python" plan and Stage 2 is real and dated, or (b) Stage 2 quietly never happens because the standalone skill is sufficient and the DeepAgents project withers. **The CEO should force a date and a definition of done for Stage 2 *before* T0 of Stage 1 is merged.** Without that, the standalone skill becomes the artifact and DeepAgents becomes legacy.

3. **"Better-harness should be removed because its signal is disconnected."** Requirement 0 of the new spec deletes `harness/`, `runs/`, and `harness:*` package scripts on the grounds that the 7 `[[cases]]` are synthetic ratify/existence tests that don't invoke the LLM, so the optimizer iterates in a vacuum. **This premise is correct and well-evidenced.** If the cases don't actually exercise `scriptwriter.md`, optimizing it on those cases is theatre. Remove it. The only caveat: archive the harness config somewhere visible (`docs/archive/`) so future contributors don't reinvent it. Don't just `rm -rf`.

**Verdict on premises:** premise (3) is right and should ship regardless. Premise (1) needs an evidence test (has v2 produced *any* real video yet?) before deprecation lands. Premise (2) is the dangerous one — it can quietly turn this project into a host for a standalone skill rather than the agent it advertises. Force the Stage 2 dating before T0.

### 0B. Existing Code Leverage — what already partially solves this?

| Sub-problem | Existing code | Reused by web-port pivot? |
|---|---|---|
| Milestone state machine | `models.MilestoneState` + `state_store.save/load_state_yaml` | Stage 2 only |
| Artifact gate validation | `ratify.ratify_script`, `ratify.ratify_source_manifest`, `build_render_flow.ratify_*` | Partially (script ratify schema may carry over; Remotion ratify is dead in the web-port world) |
| Tool-call dropout detection | `artifacts.detect_tool_call_dropout`, `controller.block_if_tool_call_dropout` | Yes if Stage 2 reuses the DeepAgents producer |
| Path virtualization | `script_flow._to_virtual_path` (also referenced from `build_render_flow.py:20`) | Yes if Stage 2 reuses |
| YAML I/O | Custom `state_store.py` (~177 LOC, quoted-string protocol) | Yes if Stage 2 reuses |
| UI state projection | `ui_state.build_video_maker_ui_state*` (already correct shape for the timeline) | Yes if Stage 2 reuses |
| Source intake (folder/websearch/local-file/manual) | `source_flow.py`, `vm_websearch` typed tool, Tavily cache | Yes, all of this carries over |
| Scriptwriter dispatch | `script_flow.build_scriptwriter_task_description` + `scriptwriter.md` agent prompt | **Open question** — the new spec replaces `scriptwriter.md` with a different role definition |
| Renderer | `build_render_flow.render_remotion_project` + `package_render_output` | **No** — replaced by Playwright + `record-with-playwright.ts` |
| Publish-readiness checklist | `build_render_flow.build_publish_readiness_report`, 5-dim checklist | Yes, carries over unchanged |

**The single biggest leverage:** the entire Source Intake / Script / Publish Readiness pillar carries over. The web-port pivot only replaces Build Scenes + Render Package, plus the visual contract that scriptwriter writes. **That is a much smaller blast radius than the spec implies** — it is not "rebuild the whole project," it is "replace the renderer and the visual side of the script contract." Framing the pivot as a Stage-1-from-scratch skill obscures this leverage. **CEO recommendation: re-scope the pivot from "new skill, decoupled from Python" to "replace the renderer; everything else stays."** That preserves 5 milestones, 17 tools, ~2.5k LOC of Python, 87 tests, and 1 UI timeline component for free.

### 0C. Dream State Mapping

```
  CURRENT STATE                  THIS BRANCH                   12-MONTH IDEAL
  ─────────────                  ─────────────                  ──────────────
  Source Intake → Script         Hardens timeline,              One operator opens
  → Build → Render →             ratify serialization,          web-ui, types a
  Publish Readiness              websearch grounding,           topic, watches
  runnable end-to-end            interrupted state UI,          Source→Script→
  via DeepAgents Producer        README rewrite.                Build→Render→
                                                                Publish complete
  Remotion golden:playable       Lands Stage-1 spec for         in one thread,
  produces 65s probeable MP4     a Web/Playwright skill         downloads MP4,
                                 that proposes deprecating      and the timeline
  v2 SKILL.md, 4 subagent        v2 (Remotion) entirely.        artefact links
  prompts, 17 typed tools,                                      open the actual
  86/87 tests green                                             files.
  (1 ffmpeg-env fail)
                                                                Renderer: either
                                                                Remotion-stable
                                                                OR Web/Playwright,
                                                                but ONE choice,
                                                                end-to-end tested.

                                                                Observability:
                                                                ratify JSONs +
                                                                structured logs +
                                                                live UI timeline
                                                                with no swallowed
                                                                exceptions.
```

The hardening in this branch moves toward the ideal on the **operator-trust** axis (timeline correctness, error guidance, README clarity, fabrication guards). The Stage-1 spec moves *sideways* on the renderer axis — it proposes a different renderer, not a better one. **Sideways moves on the renderer axis are expensive** because the renderer is half the perceived product. They are worth it only if the current renderer has been proven inadequate against a real video, not against a golden demo.

### 0C-bis. Implementation Alternatives (MANDATORY)

For the central decision — *do we deprecate `video-maker-v2` and adopt `video-maker` (Web/Playwright)?* — three plausible shapes:

```
APPROACH A: Land Stage-1 spec as written. Deprecate v2 today.
  Effort: ~28-32 working days (per tasks.md). T0 deletes harness/, runs/, marks v2
          [DEPRECATED]. T1-T8 build the new skill.
  Pros:
   - Removes the Remotion tax (Windows EPERM, browser/ffmpeg dependency, Chromium
     install in Render Package).
   - Web recording is a tool everyone in the team can read/inspect — Vite + React
     + TS + Playwright is mainstream.
   - 5 themes + narrations.ts single-source-of-truth is a tighter creative
     contract than "Remotion builder has creative freedom within boundaries."
   - Skill is installable standalone (Cursor, Codex, Claude Code).
  Cons:
   - Throws away v2 right after the golden playable proved it.
   - Stage 2 (Python re-wire) is undated and undefined; risks orphaning DeepAgents.
   - The pivot rebrands the project's North Star from "DeepAgents-native video
     producer" to "skill that records a webpage."
   - 28-32 days during which the existing v2 path is in deprecation limbo —
     contributors won't know which branch to harden.
   - "Publish-readiness" semantic in the new world is unclear: is the criterion
     "MP4 plays" or "the underlying webpage is presentation-correct"?

APPROACH B: Re-scope the pivot to "replace the renderer; keep everything else."
  Effort: ~12-16 working days estimated. Replace remotion-builder.md with
          web-recorder.md, replace build_remotion_task / render_remotion_project /
          package_render_output with their Playwright equivalents, keep
          Source Intake / Script / Publish Readiness, keep the 17-tool surface
          minus 3, keep the timeline.
  Pros:
   - Keeps the project's North Star (DeepAgents-native producer) intact.
   - Preserves ~2.5k LOC of Python, 87 tests, the UI timeline, the ratify
     framework.
   - Forces an honest test: replace ONLY the renderer; if the result is
     materially better in operator trust + visual quality, the bet was right.
   - Stage 2 is no longer a future promise — it's the same project.
  Cons:
   - The "standalone, no-Python skill" property goes away. (Honest cost: is that
     property actually a goal, or just a side effect of choosing Stage 1
     boundaries?)
   - You give up the standalone-skill distribution channel (other Claude Code
     users).
   - Requires honest assessment of whether v2 has actually failed.

APPROACH C: Keep v2 as-is. Add the new skill as a SECOND renderer option.
  Effort: ~16-20 working days. Both renderers live in the repo. The producer
          chooses renderer based on a goal.yaml field (`renderer: remotion |
          web-playwright`). Build Scenes / Render Package have two
          implementations.
  Pros:
   - No deprecation. No regret risk.
   - A/B comparison becomes structural — same script.md, two renderers, compare
     output.
   - Each renderer earns its place on operator trust.
  Cons:
   - Doubles the maintenance surface.
   - "Engineered enough" → over-engineered. Two paths is one path too many for a
     pre-product project.
   - Will probably collapse into "everyone uses one, the other rots" within
     6 months anyway — so you're just deferring the choice.

Recommendation: B is the right shape for a pre-product project that has
already paid the cost of building Source Intake / Script / Ratify / Timeline
once. Cut the renderer cleanly without throwing away the rest. Only choose A
if v2 has been proven inadequate on a real (non-golden) story. Avoid C —
it is the comfortable answer that defers the decision and doubles cost.
```

### 0D. Mode-Specific Analysis (HOLD SCOPE on hardening; STRATEGIC PROPOSAL on the pivot)

**On hardening (the 5 commits before `9380e5d`):** the work in this branch is on-scope, well-targeted, and has the right discipline: each commit fixes a specific failure-class (silent state-loss, lying-UI status, swallowed exceptions, fabrication risk, infinite ratify loop). Prime Directive #1 violations are being repaired. Holding scope here is the right call.

**On the pivot:** I am not silently absorbing this scope expansion. The Stage-1 spec is 3,465 lines of design; it is *not* a fait accompli just because it landed on this branch. The CEO decision (A vs B vs C above) should happen *before* T0.1 runs `rm -rf harness/`. Once T0 commits, v2 is marked `[DEPRECATED]` in its own frontmatter and the deprecation is harder to unwind than to land. **STOP point** in skill terms: do not execute T0 until the renderer question (premise 1 above) has a written answer with evidence.

### 0E. Temporal Interrogation (5-10 year arc)

- **Year 1:** does this project credibly ship one publishable video to one channel (YouTube Shorts, internal Slack, conference talk)?
- **Year 3:** is the differentiator "the agent decides composition" or "the agent decides editorial"? The Remotion path bets on the former. The Web/Playwright path bets that composition is solved-enough by templates and themes, so the agent only needs to be editorial. **Both are defensible. Pick one explicitly.**
- **Year 5:** AI video generation (Sora-class, Veo-class) keeps compressing. Does a *composition agent* still matter when the same prompt produces a 30s clip with native audio? The honest answer is: only if the agent's value is editorial accuracy + source-faithfulness + iterative review, not raw pixel synthesis. **That should sharpen scope further:** ratify gates and `data_card` grounding are the moat, not the renderer.

If the moat is editorial accuracy, the renderer choice matters less than the strength of `ratify_script` + `data_card_grounding` + reviewer agents. Both A and B preserve the moat. The pivot's strongest argument is that the simpler renderer frees more attention for the moat work.

### 0F. Mode Selection

**HOLD SCOPE on this branch's hardening.** Land what's already here; it's clean.

**SCOPE INVERSION DECISION PENDING on the v2 → web-port pivot.** The CEO call should be made before T0 of the new spec executes. My recommended posture: **Approach B (replace the renderer only), not Approach A (full skill pivot).** But this is your call, not mine.

---

## Review Sections

### Section 1. Architecture Review

```
                ┌─────────────────────────────────────────────┐
                │ web-ui (Next.js 15 + LangGraph dev server)  │
                │  ChatInterface → VideoProductionTimeline    │
                │  reads stream.values.video_maker            │
                └────────────────────┬────────────────────────┘
                                     │ LangGraph thread state
                                     ▼
                ┌─────────────────────────────────────────────┐
                │ DeepAgents Producer (controller-only)        │
                │  prompts/producer.md → ONE tool call/step    │
                │  + VideoMakerUiStateMiddleware injects       │
                │    video_maker payload after every vm_* call │
                └────────────────────┬────────────────────────┘
                                     │ typed tools (17)
                                     ▼
   ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
   │ source_flow.py   │  │ script_flow.py    │  │ build_render_    │
   │ vm_start_source_ │  │ vm_start_script,  │  │ flow.py           │
   │ intake,          │  │ vm_build_         │  │ vm_start_build_   │
   │ vm_websearch,    │  │ scriptwriter_     │  │ scenes,           │
   │ vm_ratify_       │  │ task,             │  │ vm_build_remotion │
   │ source_intake    │  │ vm_ratify_script  │  │ _task,            │
   │                  │  │                   │  │ vm_render_        │
   │                  │  │                   │  │ remotion_project, │
   │                  │  │                   │  │ vm_package_       │
   │                  │  │                   │  │ render_output,    │
   │                  │  │                   │  │ vm_ratify_render_ │
   │                  │  │                   │  │ package,          │
   │                  │  │                   │  │ vm_build_publish_ │
   │                  │  │                   │  │ readiness_report  │
   └────────┬─────────┘  └─────────┬─────────┘  └─────────┬────────┘
            │                      │                       │
            ▼                      ▼                       ▼
   artifacts/source/      artifacts/script/        remotion-project/
   source-manifest.md     run-N/script.md          src/index.ts
                          run-N/script-            final/video.mp4
                          contract.json            final/thumbnail.jpg
                                                   ratify/render-package.json
                                                   final/publish-readiness.md
                                                   ratify/publish-readiness.json
            │                      │                       │
            └─────────── ratify/*.json + state.yaml ────────┘
                                     │
                                     ▼
                          state_store.save_state_yaml
                          (custom YAML, quoted strings,
                           ratify JSON-blob-in-line)
```

**What's good (architecturally):**
- Controller-only Producer is honestly enforced: `prompts/producer.md` says "make ONE tool call at a time" and the producer's allowed-tools list is explicit.
- `VideoMakerUiStateMiddleware` (`middleware.py:27`) wraps every tool call and re-projects UI state after — single source of truth for the timeline.
- Ratify gates are deterministic Python; no LLM in the gate.
- Build / Render Package were genuinely added since the prior review and now include real `pnpm exec remotion render` invocations with audio-driven scene-duration rules captured in `agents/remotion-builder.md`.

**What needs surfacing:**

1. **Custom YAML still in `state_store.py`** (1.7k → 2.9k LOC growth and `state_store.py` still hand-rolls `_scalar()` / `_unquote()` / line-splitting). The skill's `Permission #9` applies: `PyYAML` is already a transitive dependency through LangChain; emitting `yaml.safe_dump(asdict(state))` and reading with `yaml.safe_load()` removes ~120 LOC of bespoke string-handling and removes a class of escaping bugs (the `ratify` field is *serialized as a JSON string inside a quoted YAML scalar* in `_serialize_ratify`, then re-parsed on load — this is exactly the kind of nested escape protocol that fails on Unicode quote characters or embedded backslashes in `blocking_reason`). **Not on the critical path; flag for cleanup.**

2. **`_to_virtual_path` lives in `script_flow.py:90` and is imported into `build_render_flow.py:20`.** That's one of two — the prior CEO review found three. Reduced, not eliminated. Pull into `serialization.py` (which already exists and has only 23 LOC). 15 minutes of work.

3. **`session.DEFAULT_MILESTONES = ("source_intake", "script", "build_scenes", "render_package")` does not include `publish_readiness`.** The UI timeline (`ui_state.MILESTONE_LABELS` and `VideoProductionTimeline.ORDERED_MILESTONES`) treats Publish Readiness as a fifth milestone. So the *UI shows five* but `state.milestones` carries only four. The publish readiness state is read from a separate JSON via `_read_publish_readiness()` rather than from `state.milestones`. This is a deliberate choice (publish readiness is advisory, not a milestone state machine entry) but it means UI consumers have to know to look in two places. **Not a bug. Worth one comment in `ui_state.py:81` clarifying the split.**

4. **`controller.py` (60 LOC) is referenced by tests but not by the Producer wiring** in this branch. `langchain_tools.py` does not import `block_if_tool_call_dropout`. Check whether the controller dropout guard is actually active end-to-end, or whether it's only exercised in unit tests. If it's dead in production, that's a Prime Directive #1 problem (silent failure: the dropout would never be caught at runtime). See §2.

5. **Subagent skill wrappers in `.deepagents/skills/video-maker-v2-{scriptwriter,remotion-builder}/`** are thin pointers to `skills/video-maker-v2/agents/*.md`. This is the right shape, but the wrapper README only says "Source of truth lives in: /skills/video-maker-v2/agents/scriptwriter.md" — there is no automated check that the wrapper points to a real file or that the pointer survives the impending `[DEPRECATED]` mark. Add a `test_skill_files.py` assertion that the wrapper resolves.

### Section 2. Error & Rescue Map

Every error in the runnable pipeline, named, with rescue:

| Exception / failure | Triggered by | Caught by | User-visible | Tested? |
|---|---|---|---|---|
| `RuntimeError: cannot start build_scenes ... script status=<X>` | `vm_start_build_scenes` before script ratify completed | Tool returns `{"error": ...}` dict, never raises out of LangGraph | Yes (chat surface) | Implicitly via `test_build_render_flow.py` |
| `RuntimeError: cannot start build_scenes without script_approved=True` | Producer calls `vm_start_build_scenes(script_approved=False)` | Same | Yes | Yes |
| `ValueError: topic is required when structured inputs are provided` | `vm_init_video_session` partial inputs | Propagates (not caught) | Yes via traceback | `test_params.py` |
| `ValueError: prompt or structured inputs are required` | Same as above, fully empty | Propagates | Yes | Yes |
| `ValueError: goal.yaml missing topic: ...` | `load_goal_yaml` on corrupt file | Propagates | Indirect (tool fails) | Indirect |
| `KeyError: unknown milestone: <id>` | `state.milestone("publish_readiness")` (no entry) | Propagates | Indirect | Not directly |
| `json.JSONDecodeError` on `state.yaml` ratify scalar | Corrupted state file | `state_store.py:158` catches, sets `ratify = {}` | Silent | No |
| `subprocess.TimeoutExpired` on `pnpm exec remotion render` | Hung render | Not caught — `subprocess.run(timeout=1800)` will raise | Yes (traceback) | No |
| `FileNotFoundError` on `pnpm` not in PATH | Missing Node toolchain | Not caught — `subprocess.run` raises `FileNotFoundError` | Yes (traceback) | No |
| `SystemExit: ffmpeg is required` | `run_golden_playable_smoke` without ffmpeg | Raises out of test | Yes (CI installs ffmpeg) | Yes (test_golden_demo_smoke.py:54 — fails in sandbox-without-ffmpeg) |
| `tavily.TavilyClient` import missing | No `tavily` package installed | `source_flow.py:200` — `try/except Exception` around `from tavily import TavilyClient` returns error-item | **Silent-ish** — manifest has a single ERROR item; ratify catches `has_no_error_items` | Indirectly |
| Tavily 401 / network failure | Bad API key or offline | `source_flow.py:206` `except Exception as exc` → error-item | User sees `websearch failed: <exc>` in manifest | No direct test |
| Ratify infinite-loop on `data_card_grounding` regex bug | Pre-`3b719dd` bug; fixed | `3b719dd` fix | (Was silent — milestone retried 0+1 forever) | Bug was uncaught; fix is now in code. **No regression test for "ratify must eventually terminate" was added.** |
| UI state projection failure | `build_video_maker_ui_state` raises | `middleware.py:38` `try/except` silently swallows + logs in `langchain_tools.py:454` | Silent (logged) | Indirectly |
| Tool-call dropout (LLM emits `<task>` literal instead of real tool call) | Model error | `controller.block_if_tool_call_dropout` — but **never imported by `langchain_tools.py` or `agent.py`** | **Currently unwired in production** | Tested in `test_tool_call_dropout_detection.py` (unit only) |
| Build Scenes runner missing `pnpm exec remotion` | No Remotion in `remotion-project/` | Render command captures non-zero exit, `passed=False`, returns; not a raise | Yes via `render-command.json` | Partially via `test_build_render_flow.py` |

**Critical findings from this table:**

1. **The Tavily silent-import is partially fixed** (the manifest carries an ERROR item, and `ratify_source_manifest` now checks `has_no_error_items`), but the producer prompt doesn't *tell* the producer that `source=websearch` requires Tavily. The first-time user with `source: websearch` and no Tavily will hit a Source Intake `BLOCKED` state without context. **Recommendation:** `vm_init_video_session` should reject `source=websearch` without `TAVILY_API_KEY` at parse time with a named error. Cost: 5 LOC.

2. **Controller dropout guard is not wired into production.** `controller.block_if_tool_call_dropout` exists, has tests, and is never imported by the agent factory. Either wire it into `VideoMakerUiStateMiddleware` (add a pre-call check) or delete it as dead code. Right now it is the textbook "looks safe but doesn't run" trap. Prime Directive #1.

3. **No "ratify must terminate" property test.** The `3b719dd` infinite-loop bug should have been caught by a test that says "for any script.md / contract.json, `ratify_script` returns within K checks or returns `next_action='block_for_user'` after `max_retries`." This is now an absent regression net for a class of bugs that already bit once. Add one property test using Hypothesis or a tight bounded loop.

4. **`subprocess.run(timeout=1800)` for Remotion render** can raise `TimeoutExpired` and `FileNotFoundError`; neither is caught in `render_remotion_project`. Wrap in try/except, return structured `{"passed": False, "error_class": "...", "error_message": "..."}` so the producer (and the UI) can show a named failure mode instead of a bare traceback.

### Section 3. Security & Threat Model

The project is local-dev today (no auth, no multi-tenant, no public endpoints), so the threat surface is narrow. Still worth naming:

1. **Tavily API key leakage.** `source_flow._tavily_api_key()` reads from env or repo `.env`. The `.env` file is in `.gitignore` (verified). The cached `websearch-results.json` does NOT contain the key — only results. Good.

2. **Arbitrary file read via `source: folder`.** `_manifest_items` walks any folder the user names. If this is ever exposed to a remote operator (Stage 2 hosted), arbitrary path traversal is the trivial attack. Currently local-dev, so flagged but not critical. Mitigation when hosted: confine to a sandbox root and reject absolute paths or `..` segments.

3. **`subprocess.run(["pnpm", ...], cwd=project)`** — command list is fixed (no shell), no user input flows into the command list. Safe.

4. **`vm_websearch` topic input flows into `TavilyClient.search(query=topic)`.** Tavily is the trust boundary; no injection concern on our side.

5. **`render_remotion_project`'s `composition_id` is a tool argument** that flows directly into the `remotion render` command line. It is not validated. A producer-side prompt-injection could theoretically pass a malformed `composition_id` like `Foo --output=/etc/passwd`. Mitigation: validate against `[A-Za-z0-9_-]+` before passing. 3 LOC.

6. **Web UI** — Next.js 15 dev server on localhost. No security surface today. Stage 2 hosted would need auth, CSRF, and rate-limiting on the LangGraph endpoint. Out of scope now.

**Threat model verdict:** Local-dev posture is reasonable. Add `composition_id` validation (cheap, defensive). Defer multi-tenant concerns until Stage 2.

### Section 4. Data Flow & Interaction Edge Cases

Trace the happy path for one new flow — `vm_websearch` cache reuse:

```
vm_websearch(output_dir, topic="X")
  → run_websearch_and_cache(topic, output_dir)
    → _websearch_items(VideoMakerGoal(topic, source="websearch"),
                       cache_path=output_dir/artifacts/source/websearch-results.json,
                       force_fresh=True)
      → TavilyClient.search(...) → 8 results
      → write cache JSON
      → return items
  → return {status, item_count, items, cache_path}

[later]
vm_ratify_source_intake(output_dir, ...)
  → ratify_and_update_source_intake(state, goal)
    → write_source_manifest(goal, state)
      → _manifest_items(goal, state=state)
        → _websearch_items(goal, cache_path=..., force_fresh=False)
          → cache exists? read it. ← reuses one Tavily call ✓
```

Happy path is correct. Now the four shadow paths:

| Path | What happens | Verdict |
|---|---|---|
| **nil input** | `topic=None` to `vm_websearch` | `vm_websearch(output_dir, topic=None)` — type signature says `str`, but Python doesn't enforce. `TavilyClient.search(query=None)` would raise `TypeError` at the API. **Add validation: `if not topic: return {"status": "error", ...}` at the top of `vm_websearch`.** 2 LOC. |
| **empty input** | `topic=""` | Same as above — Tavily call fails. Same fix. |
| **upstream error** | Cache exists but is corrupt JSON | `_websearch_items` catches `Exception` in cache-load branch and falls through to a fresh fetch. ✓ |
| **partial state** | Cache has items but Tavily key removed | `force_fresh=False` reads cache. ✓ Cache wins. If cache is stale, the user only gets new results by deleting `websearch-results.json` — there is no expiry. Document this or add a TTL. |

Trace one more flow — `vm_ratify_script` retries:

```
vm_ratify_script(output_dir, run_number=1)
  → ratify_and_update_script(state, goal, run_number=1)
    → ratify_script(script_path, contract_path)
      → returns RatifyResult(passed=False, issues=[...])
    → milestone.retry_count += 1  # was 0, now 1
    → if retry_count > max_retries (2):
        → status = BLOCKED, next_action = block_for_user
      else:
        → status = IN_PROGRESS, next_action = retry_milestone
    → write ratify/script-run-1.json
    → return result
```

**Edge case:** `run_number` differs from `milestone.current_run`. The function honors the caller's `run_number` arg over the milestone's `current_run`. That means a producer that calls `vm_ratify_script(output_dir, run_number=2)` while `current_run=1` will ratify run-2 (which may not exist) without complaint. **Add an existence check** at the top: if the script path doesn't exist for `selected_run_number`, return a named error. The current behavior is that `ratify_script` will return `script_exists=False` and fail the gate, which is *eventually correct*, but the named error is faster and clearer.

**Interaction edge cases** the chat UI needs to handle:

- **User double-clicks "Approve script."** The current model assumes the producer drives `vm_start_build_scenes(script_approved=True)` exactly once. If the UI calls it twice, the second call returns the same RunInfo (because `create_milestone_run` creates a new `run-N` directory each call). **Bug:** repeated approval creates `remotion-project` collisions? No — `start_build_scenes_milestone` calls `create_milestone_run("build_scenes")` which makes `artifacts/build_scenes/run-1`, `run-2`, etc. But `remotion-project/` is a fixed path, not run-numbered. **Race:** if the user double-approves quickly, two `task(remotion-builder)` dispatches will both write into the same `remotion-project/`. Mitigation: idempotency check in `start_build_scenes_milestone` — if `current_run` is set and `build_scenes` is already `IN_PROGRESS`, return the existing RunInfo instead of creating a new one.
- **Navigate away mid-render.** Renders take >1 minute. If the user closes the tab, the `subprocess.run` in `render_remotion_project` keeps running but the LangGraph thread loses its handler. Either the next thread resume re-attaches, or the render orphans. This is the operator-trust gap the prior review flagged. **Recommendation:** Run renders via a thread-local job table with `state.yaml` reflecting `render_status: queued | running | succeeded | failed` and a `render_log_path`. Not for this PR; flag for the live-UI proof work.
- **Slow connection during script generation.** Subagent dispatches via the DeepAgents runtime; LangGraph handles back-pressure. No specific concern here unless we add SSE-token streaming to the UI later.
- **Back button during build approval.** The interrupted state now renders correctly (`17c032e`). Good.

### Section 5. Code Quality Review

Read-pass impressions:

**Strong:**
- Dataclasses + StrEnum throughout `models.py`; clear types.
- `script_flow.py` and `build_render_flow.py` have small, named helpers (`_payload`, `_result`, `_write_ratify`) rather than inlined dicts.
- Comments where they earn it: e.g., `script_flow.py:32-35` explaining why the contract write is guarded.
- `ratify.py` has explicit named checks (`RatifyCheck(id=..., passed=..., message=..., metadata=...)`) — making the gate output legible without an external decoder.

**Weak (call-out list):**

1. **`langchain_tools.py:67-202`** — `vm_init_video_session`, `vm_ratify_source_intake`, `vm_build_scriptwriter_task`, `vm_ratify_script`, `vm_build_remotion_task` all take the same 14-parameter signature. That signature is repeated ~5 times. **Pull `GoalInputs` into a `TypedDict` or dataclass** and accept that one argument plus `prompt`. Cost: 30 LOC saved per tool × 5 tools = ~150 LOC reduction. Readability win even bigger.

2. **`build_render_flow.py:65-111`** — `build_remotion_builder_task_description` is a 47-line f-string with 7 path interpolations. Same shape as `build_scriptwriter_task_description` in `script_flow.py:42-87`. Both are descriptions assembled from a template + goal/state. **Pull templates into `prompts/dispatch/{scriptwriter,remotion-builder}.md.tmpl` and use `string.Template` or jinja2.** Keeps the descriptions reviewable as text. Cost: ~20 LOC saved + much easier to A/B prompt versions.

3. **`state_store.py:120-159`** — the load loop hand-parses each line. State of the art is "load with PyYAML, validate via dataclass init." See §1 Architecture Review #1.

4. **`source_flow.py:106-139`** — `_manifest_items` is a 33-line dispatch on `goal.source`. Five conditional branches, each ~5 lines. Three of them call `_error_item(...)`. **Pull source-type handlers into a registry: `{"folder": _folder_items, "websearch": _websearch_items, ...}`** and dispatch by key. Cleaner extension point for the next source type. Cost: same LOC, much higher legibility.

5. **`agent.py:96-101`** — `_subagent_description` has descriptions for `evaluator`, `reviewer`, `editor`, `scene-batch-generator`, `scene-patch-generator` that **are never registered as subagents** (`SUBAGENT_NAMES = ["scriptwriter", "remotion-builder"]`). Dead descriptions. **Either register them and back them with prompts, or delete them.** This is exactly the "skeleton implies more than the bones support" smell the prior review called out — three commits later, the leftover skeleton is still there.

6. **`build_render_flow.py:241-274`** — `package_render_output` does silent partial-success (sets `copied_video = False` if source file doesn't exist, doesn't raise). The caller has to inspect `copied_video` / `copied_thumbnail` to know. Either raise on `copied_video=False` (since render-package can't proceed without a video) or surface the named issue in `next_action`. Right now this is a Prime Directive #1 smell: missing video is detected and *silently encoded as a Boolean.*

7. **Dead code:** `agent.py:43-46` mentions `evaluator`, `reviewer`, `editor`, `scene-batch-generator`, `scene-patch-generator` — neither registered in `SUBAGENT_NAMES` nor surfaced anywhere. Same with the `scene-batch-generator.md` and `scene-patch-generator.md` files in `skills/video-maker-v2/agents/` — referenced in the SKILL.md as part of the v2 contract but not dispatched by the producer.

### Section 6. Test Review

**87 tests collected; 86 pass in this sandbox.** The 1 failure (`test_golden_playable_smoke_produces_probeable_mp4`) is a sandbox-env issue (no ffmpeg) — the CI workflow installs ffmpeg explicitly. **Not a code defect.** Should still call out that the test is environment-coupled: when ffmpeg is missing, the test should `pytest.skip` with a clear reason, not fail. **Fix:** add `@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg required for playable smoke")` to the test. 3 LOC.

**Coverage shape (by domain):**

| Domain | Test files | Test count | Verdict |
|---|---|---|---|
| Agent factory | 1 | ~3 | Adequate |
| Artifact gates | 1 | ~10 | Strong — explicit happy and failure cases |
| Build/render flow | 1 | ~10 | Adequate — simulated runner |
| Controller dropout | 1 | 3 | **Unit-only — not wired into producer** |
| Golden demo smoke | 1 | 3 | Strong — script checkpoint + simulated render + playable |
| Langchain tools | 1 | ~10 | Adequate — covers registration + happy paths |
| Params | 1 | ~5 | Strong |
| Prompts | 1 | ~3 | Adequate |
| Ratify (script) | 1 | ~10 | Strong — multiple scene-rule cases |
| Research flow (legacy) | 1 | ~3 | **Vestigial — purpose unclear post-v2** |
| Script flow | 1 | ~5 | Adequate |
| Session | 1 | ~3 | Adequate |
| Skill files (presence) | 1 | ~6 | Strong — asserts wrapper files exist |
| State store | 1 | ~5 | Adequate |
| UI state | 1 | 3 | Adequate but lean |
| Windows path | 1 | 1 | Single-case; fine for what it's testing |

**Gaps the data shows:**

1. **No property test for ratify termination.** The `3b719dd` infinite-loop bug should have been caught. Add: "for any script.md and contract, after N retries, ratify returns BLOCKED, not IN_PROGRESS." This is the regression net the bug exposed.

2. **No test for `controller.block_if_tool_call_dropout` being *wired into the producer*.** The function works in isolation. The integration that protects production is untested.

3. **No test for UI state projection failure recovery.** `middleware.py:38` and `langchain_tools.py:454` both swallow exceptions and continue. There is no test that says "if `build_video_maker_ui_state` raises, the tool result is still returned and the failure is logged." If that branch ever stops returning the tool result, it would be silently miscompiled into the chat surface.

4. **No test for `vm_websearch` cache reuse.** `vm_ratify_source_intake` is supposed to reuse the cache; no test asserts "vm_websearch then vm_ratify_source_intake hits Tavily exactly once." This is exactly the assertion the optimization claims to provide.

5. **`test_research_flow.py` is from the legacy `video-maker` (research-first) era.** v2 has no research milestone. If this test is still meaningful, rename. If not, delete. The producer prompt says "no `research.md`" — the test name should reflect that.

6. **No test for `_to_virtual_path` cross-platform behavior beyond `test_windows_path_normalization.py`'s one case.** Add a parameterized test covering Linux absolute, Windows backslash, Windows drive letter, and UNC path inputs. Cost: ~15 LOC.

7. **No end-to-end web-UI test.** Per the 2026-05-09 review and reaffirmed here: there is no captured browser proof that the timeline renders milestone state from a real LangGraph thread. The Stage-1 spec exists but no live-UI smoke does. **This remains the most CEO-relevant test gap.**

### Section 7. Performance Review

Low concern; this is a CLI / dev workflow, not a hot path:

- Each `vm_*` tool call: O(1) file I/O for state.yaml + ratify JSON. Fast.
- `_manifest_items` for `source=folder` walks `path.rglob("*")` and slices `[:200]`. Fine for tens-of-thousands-of-files folders; the 200-cap is the right shape.
- `_websearch_items` with `max_results=8` + cache. One Tavily call per session. Fine.
- `render_remotion_project` is the only heavy operation: typecheck + `remotion render` + `remotion still`. Bounded by Remotion itself (~minute per scene for 1-3min videos). Timeout is 1800s (30min). Reasonable.

**One concrete concern:** `build_video_maker_ui_state(output_dir)` is called on **every tool call** by both the middleware AND inside `_with_ui_state`. Each call reads `state.yaml` from disk via `load_state_yaml`, iterates milestones, stats artifact files. For a session with 5 milestones × 10 artifact paths = 50 `stat()` calls per tool call. Probably 10ms but it's pure waste if the in-memory state is already known. **Recommendation:** when `state` is already in memory (the typical case — every tool already loaded it), pass it through to `build_video_maker_ui_state_from_state` and skip the disk re-read. The `_with_ui_state` helper already prefers the in-memory variant, but `middleware.py:_attach_ui_state` always goes through the disk variant. **30-LOC refactor.**

### Section 8. Observability & Debuggability Review

**What exists today:**
- `ratify/*.json` written for every gate decision (source-intake, script-run-N, build-scenes, render-package, publish-readiness).
- `render-command.json` captures full stdout/stderr (last 4000 chars each).
- `state.yaml` is the canonical milestone state. Round-trips correctly post-`17c032e` (was previously dropping `ratify` field — that was a real observability bug).
- `print` statements in scripts; structured Python logging in `langchain_tools.py:454` for UI projection failures.

**What's missing:**

1. **No session-scoped trace ID.** Each session is identified by `output_dir` (timestamped path). That works for filesystem inspection but not for log correlation. **Recommendation:** generate a UUID at `init_video_session` time, write it into `state.yaml`, and include it in every log line.

2. **No structured logger config.** `logging.getLogger(__name__)` is used twice. Default formatter, no handler set up explicitly. **Recommendation:** add `src/deepagents_video_maker/logging_setup.py` with a `setup_logging()` that emits JSON-line logs to stderr. 30 LOC. The chat-UI doesn't need this, but the moment this project runs on a server, it does.

3. **No timeline event log.** `state.yaml` has the current state but not the history. When a milestone goes `IN_PROGRESS → BLOCKED → IN_PROGRESS → COMPLETED` (which is what retries do), only the final state is recorded. **Recommendation:** append-only `events.jsonl` with `{ts, milestone, from_status, to_status, run_number, reason}`. Cheap, makes "why did this take 4 retries" a one-grep answer.

4. **Render stderr is captured but not surfaced in the UI.** `ratify/render-command.json` has the failure detail; the UI timeline shows "render_package: blocked." The operator has to know to open the JSON. **Recommendation:** when `blocking_reason` is set, also include `blocking_details_path` in the UI state pointing at the most relevant ratify JSON. The timeline component already has the artifact-link UI; this is a 3-line change to feed it.

### Section 9. Deployment & Rollout Review

This project does not deploy yet. The deployment-relevant concerns are local-dev concerns:

1. **`pnpm ui:build` still flaky on Windows** per the 2026-05-09 review. Not fixed on this branch. **CRITICAL for "ship-readiness":** if a contributor or stakeholder on Windows can't produce a UI build, the live demo is broken. The `scripts/build-ui.mjs` wrapper exists; it doesn't fully resolve the `spawn EPERM` issue. **Recommendation:** capture a reproducer (env, Windows version, Node version) and attack root cause. If it's truly `corepack pnpm` re-extracting on every invocation, set `COREPACK_HOME` to a stable path in the wrapper. If it's `TEMP` permission, set `TEMP=C:\tmp` in the wrapper script.

2. **Node + Python dual stack.** First-time-contributor friction is high: `uv sync`, `pnpm install`, `corepack enable`, `ffmpeg`, `pnpm exec remotion render` requires Chrome/Chromium for headless rendering. Document the full toolchain prerequisites in `docs/golden-demo.md` (partially done) and add a doctor script: `scripts/doctor.py` that checks `which uv`, `which pnpm`, `which ffmpeg`, `which ffprobe`, and reports missing pieces. Cost: ~50 LOC. Pays for itself the first time someone hits "ffmpeg required" cryptically.

3. **CI installs ffmpeg, runs pytest, runs CLI sanity check.** It does NOT run `pnpm golden:playable` (the playable smoke). **Recommendation:** add it to the CI workflow as a separate job. It's only ~30s and proves the golden ladder on every PR. Currently the playable test runs through pytest indirectly, so this might already be covered — verify.

4. **No release artifact.** This project has no `pyproject.toml` `[project]` version bump cadence, no `CHANGELOG.md`. Deferred until productization, fine.

### Section 10. Long-Term Trajectory Review

This is the section the pivot decision lives in. Restated as 6-month and 12-month projections:

**If the team chooses Approach A (full pivot to Web/Playwright skill):**
- Month 1-2: Stage 1 ships. Standalone skill is distributable. v2 is `[DEPRECATED]`. Python tooling untouched.
- Month 3-4: Stage 2 begins (or doesn't — risk #1). Python tools must adapt to web-port. Build Scenes + Render Package replaced. Tests rewritten.
- Month 6: either Stage 2 ships and the project is now a Web/Playwright agent, or Stage 2 stalls and `skills/video-maker/` is used by external installs while DeepAgents wrappers point at the deprecated v2. Project identity blurs.

**If the team chooses Approach B (replace renderer only):**
- Month 1-2: `remotion-builder.md` and `vm_*remotion*` tools are replaced by `web-recorder.md` and `vm_*web_recording*` tools. Tests rewritten in place. Producer prompt updated. Single PR (large, but bounded).
- Month 3-4: production-quality recording (subtitles overlay, audio sync, theme polish).
- Month 6: same project, different renderer, real demo.

**If the team chooses Approach C (two renderers):**
- Month 1-3: both renderers exist. Goal.yaml has `renderer:` field.
- Month 6: one renderer rots. Probably Remotion, given the spec's framing. Maintenance debt accumulated.

**My honest assessment:** Approach B is the lowest-risk path to a real product. Approach A risks project identity drift. Approach C is the comfortable defer.

**Trip-wire I would set regardless of choice:** by 2026-08-01, this project should have produced *one publishable video* — not the golden demo, but a real piece (an internal explainer, a conference promo, a tutorial video). If by then no real video has been produced through either path, the renderer choice is the wrong question. The right question becomes "is the editorial moat (ratify + grounding) strong enough that we're optimizing the wrong axis?"

### Section 11. Design & UX Review

UI scope is in: `web-ui/src/app/components/VideoProductionTimeline.tsx` was added in P1 (`docs/plans/20260507-220336`). I have not run the UI in this review (no live-UI proof captured in the prior review either). What I can see in the source:

- 5-milestone timeline (`source_intake`, `script`, `build_scenes`, `render_package`, `publish_readiness`).
- Status icons: `Circle` (pending), `Clock` (in_progress), `PauseCircle` (interrupted, amber) — `17c032e` fix, **good**.
- Artifact links per milestone via `ARTIFACT_HINTS` regex matching.
- Current-blocker callout and next-actions list.

**Design hygiene per skill cognitive patterns:**

1. **Hierarchy as service:** what does the user see first? Per `ChatInterface.tsx` (639 LOC), the timeline is one of several panels. Verify the timeline is visible *during* a long render, not just at the end. If it's collapsed by default, demote it to "expand by default during in_progress" — operator trust hinges on visibility.

2. **Edge case paranoia:**
   - Empty session (no `video_maker` state): timeline must not render misleading "all pending" — verify the component returns null when state is absent.
   - Long output paths (Windows `E:\workspace\deepagents-video-maker\output\20260508-010000-video-ai-agent-intro\artifacts\source\source-manifest.md` is 100+ chars): need truncation with full path on hover/click.
   - Failed render with multi-line stderr in `render-command.json`: the timeline shows "blocked"; the user has no in-UI way to view the stderr. Per §8, surface the relevant ratify JSON path.

3. **Design for trust:**
   - "Publish Readiness: not_reviewed" should never look complete. Verify the timeline's completion icon is reserved for `status === 'published_ready'` or `published`, not for any of {`not_reviewed`, `needs_revision`}. The five readiness states are: `not_reviewed`, `needs_revision`, `publish_ready`, `published`, `failed` (per the productization plan §Phase 2). Make sure the UI distinguishes these.

4. **Subtraction default:** the `SubAgentIndicator` (60 LOC) and `ThinkingBlock` (122 LOC) components add chrome. Verify they don't compete with the timeline for visual hierarchy during a long-running session.

5. **Live-UI proof:** I cannot verify any of the above without running the UI. **CEO recommendation:** before the pivot decision, capture *one* screencast / GIF / set of screenshots showing the golden demo path advancing the timeline through Source Intake → Script. That artifact alone reduces the operator-trust gap by 80%.

---

## Outside Voice — Independent Plan Challenge (skill §Outside Voice)

The skill recommends getting an independent challenger view on the plan. The two prior CEO reviews on this repo (`ceo_reviews/20260509-090645-ceo-review.md`, `cc_ceo_reviews/20260509T012631Z-plan-ceo-review.md`) provide that. Their consistent findings, re-checked:

| Prior finding | Status today |
|---|---|
| Tavily silent-import — "every error has a name" violation | **Partially fixed** (manifest carries ERROR item; producer prompt does not yet refuse `source=websearch` without `TAVILY_API_KEY`). |
| Custom YAML in `state_store.py` | **Not fixed.** Same hand-rolled protocol, plus a new ratify-JSON-in-quoted-scalar nesting. |
| `_to_virtual_path` duplicated | **Reduced from 3× to 2×.** Still not consolidated. |
| Skeleton implies more than the bones support (5 unused subagent descriptions in `agent.py`) | **Not fixed.** Same dead descriptions. |
| Windows `pnpm ui:build` `spawn EPERM` | **Not fixed.** Wrapper exists; root cause not identified. |
| Live UI proof missing | **Not fixed.** Same gap. |
| Controller dropout guard wired? | **Not fixed.** Still unit-only. |
| Tests don't prove ratify terminates | **Not fixed.** `3b719dd` exposed the bug; no regression test added. |

Eight prior findings, three commits between reviews focusing on what they did fix (timeline correctness, Tavily depth/grounding, README, ratify serialization). The rest still open.

This is not a criticism of velocity. It's a signal that the project has a pattern: hardening sweeps focus on one axis at a time (this branch: ratify+UI; previous: golden demo ladder; before that: web UI). Each axis improves; the prior findings accumulate. **Recommendation:** carve one branch per quarter for "prior-review hygiene": deliberately attack the open findings, not new scope.

---

## CEO Scorecard

| Dimension | Score | Rationale |
|---|---:|---|
| Product direction | 7/10 | Coherent pipeline; the pending renderer pivot creates ambiguity until decided. Down 1 from prior because the pivot is unresolved. |
| Demo credibility | 7/10 | Playable MP4 still works (in ffmpeg-equipped envs). Real-story video not produced. Same as prior. |
| Operator trust | 7/10 | Up 1 from prior — timeline interrupted state, README rewrite, error guidance, fabrication guards all improve operator clarity. Live UI proof still absent. |
| Engineering confidence | 8/10 | Tests green (modulo env), source flow + ratify + state_store hardened. Down nothing from prior. |
| Ship readiness | 6/10 | Same as prior. UI build still flaky on Windows; no real-story video produced. Pivot decision adds uncertainty. |

---

## Critical Gaps & Required Outputs

### Critical Gap 1: Pivot decision is unmade, but spec is already merged-ready

**Impact:** T0 of `specs/video-maker-web-port/stage-1-skill/tasks.md` will, on its first commit, mark `skills/video-maker-v2/SKILL.md` as `[DEPRECATED]` and delete `harness/`. That's a *visible-to-the-codebase* commitment to Approach A before the alternatives (B or C above) have been evaluated.

**CEO recommendation:** Before T0 runs:
1. Write a one-page "Pivot decision record" at `docs/decisions/2026-05-12-renderer-pivot.md` answering: (a) has v2 produced a real video yet? (b) what evidence do we have that Web/Playwright will be better? (c) is the standalone-skill distribution channel a goal or a side effect? (d) what is Stage 2's date and definition of done?
2. If after writing it the team still wants Approach A, ship it with eyes open.
3. If the team chooses Approach B (renderer-only swap), update `specs/video-maker-web-port/stage-1-skill/{requirements,design,tasks}.md` to reflect that scope, before any T0 commits land.

### Critical Gap 2: Controller dropout guard is dead code in production

**Impact:** `controller.block_if_tool_call_dropout` is a Prime-Directive-#1 safety check that runs only in unit tests. The producer in production has no guard against the LLM emitting `<task>` literals or other pseudo-tool-call patterns.

**Recommendation:** Either wire it into `VideoMakerUiStateMiddleware.wrap_tool_call` as a pre-call check, or delete it as dead code. Either is fine; the current state — exists, claims protection, doesn't run — is the worst option.

### Critical Gap 3: Ratify-termination property is untested

**Impact:** `3b719dd` was a one-line regex fix for a bug that caused infinite ratify loops. The fix is correct; the absence of a regression test is the problem. The same class of bug can re-emerge.

**Recommendation:** Add a property test asserting: "for any (script.md, contract.json) pair, calling `ratify_and_update_script` repeatedly converges to either COMPLETED or BLOCKED within `max_retries + 1` iterations." 20-30 LOC.

### Critical Gap 4: Live UI proof remains missing

**Impact:** Reaffirmed from the 2026-05-09 review. Operators judge this project through the chat UI. Without a captured browser-side proof, "the timeline works" is an assertion, not evidence.

**Recommendation:** Add `scripts/smoke_ui_thread.sh` (or `.ps1` for Windows) that starts `pnpm agent:dev`, starts `pnpm ui:dev`, hits a fixed thread URL, runs the golden prompt, and captures screenshots at Source Intake completion and Script completion. Even a non-headless Playwright script that emits 2 PNGs is enough.

### Critical Gap 5: Windows `pnpm ui:build` `spawn EPERM` not root-caused

**Impact:** Same as Gap 4 — operator-trust gap. Cannot ship a Windows demo if the production UI build doesn't reliably succeed.

**Recommendation:** Capture one full failure log on a fresh Windows runner, root-cause it (likely `corepack` cache or `TEMP` directory permission), and fix in `scripts/build-ui.mjs`. The current wrapper hides the symptom in some runs but not all.

### Failure Modes Registry

| Failure | Detection | Recovery | Visible? |
|---|---|---|---|
| Tavily not installed | Manifest ERROR item + `has_no_error_items` ratify check | Re-run after install | Yes |
| Tavily quota / 401 | Same path | Re-run after fix | Yes |
| Script ratify regex bug (class) | None today (regression test gap) | None — silent loop | **No** |
| Tool-call dropout | Unit test only; not wired | Unknown — guard doesn't run | **No** |
| Render subprocess timeout | Raises uncaught | Manual retry | Partial (traceback) |
| Render subprocess missing binary | Raises uncaught | Manual install | Partial (traceback) |
| UI state projection raise | `try/except` + log | Tool result still returned | Logged-only |
| Windows `spawn EPERM` (production build) | Manual via `pnpm ui:build` | Unknown (workaround partial) | Yes (cryptic) |
| Render package missing video | `package_render_output` returns `copied_video=False`; ratify catches `final_video.mp4` absence | Re-run | Partial |
| State.yaml ratify scalar corrupted | `state_store.py:158` catches, sets `ratify={}` | Silent recovery | **No** — silent data loss |

### TODOS.md updates

The repo has no `TODOS.md`. The skill expects one. **Recommendation:** create `TODOS.md` with the following items (numbered, dated):

1. `[2026-05-12]` Wire `controller.block_if_tool_call_dropout` into producer middleware or delete as dead code. (Gap 2)
2. `[2026-05-12]` Add ratify-termination property test for `ratify_and_update_script`. (Gap 3)
3. `[2026-05-12]` Add `scripts/smoke_ui_thread.*` for captured live-UI proof. (Gap 4)
4. `[2026-05-12]` Root-cause Windows `pnpm ui:build` `spawn EPERM`; fix in `scripts/build-ui.mjs`. (Gap 5)
5. `[2026-05-12]` Replace custom YAML in `state_store.py` with PyYAML. (~120 LOC reduction)
6. `[2026-05-12]` Consolidate `_to_virtual_path` (currently in `script_flow.py:90`, imported by `build_render_flow.py:20`) into `serialization.py`.
7. `[2026-05-12]` Delete unused subagent descriptions in `agent.py:96-101` (evaluator, reviewer, editor, scene-batch-generator, scene-patch-generator).
8. `[2026-05-12]` Add `composition_id` validation in `vm_render_remotion_project` (regex `[A-Za-z0-9_-]+`).
9. `[2026-05-12]` Add `pytest.mark.skipif` to `test_golden_playable_smoke_produces_probeable_mp4` when ffmpeg is missing.
10. `[2026-05-12]` Wrap `subprocess.run` in `render_remotion_project` with named-exception handling for `TimeoutExpired` and `FileNotFoundError`.
11. `[2026-05-12]` Add `vm_websearch` cache-reuse test (one Tavily call across `vm_websearch` + `vm_ratify_source_intake`).
12. `[2026-05-12]` Document the renderer pivot decision in `docs/decisions/2026-05-12-renderer-pivot.md` BEFORE any T0 commit of the web-port spec.
13. `[2026-05-12]` Either register or delete `tests/deepagents_video_maker/test_research_flow.py` post-v2 cleanup.
14. `[2026-05-12]` Add session UUID to `state.yaml` and to log lines for trace correlation.

### Diagrams

ASCII diagrams are in §1 (architecture) and §4 (data flow). Additional ones below.

**Pivot decision tree (forced choice before T0):**

```
                 ┌─────────────────────────────────────┐
                 │ Has v2 produced a real (non-golden) │
                 │ publishable video?                  │
                 └──────────────────┬──────────────────┘
                                    │
                  ┌─────────────────┴─────────────────┐
                  │                                   │
                YES                                  NO
                  │                                   │
                  ▼                                   ▼
       ┌──────────────────────┐         ┌──────────────────────┐
       │ v2 has earned its    │         │ v2 is speculative.   │
       │ keep. The pivot      │         │ Pivot is rational    │
       │ argument weakens.    │         │ on engineering tax   │
       │                      │         │ grounds.             │
       │ → Approach B         │         │                      │
       │   (renderer-only     │         │ Now ask: is the      │
       │   swap)              │         │ standalone-skill     │
       └──────────────────────┘         │ property a goal?     │
                                        └──────────┬───────────┘
                                                   │
                                  ┌────────────────┴────────────────┐
                                  │                                 │
                                YES                                NO
                                  │                                 │
                                  ▼                                 ▼
                       ┌──────────────────────┐         ┌──────────────────────┐
                       │ Stage 1 first, then  │         │ Project identity     │
                       │ Stage 2 with         │         │ stays DeepAgents.    │
                       │ DATED def-of-done.   │         │                      │
                       │                      │         │ → Approach B         │
                       │ → Approach A         │         │                      │
                       └──────────────────────┘         └──────────────────────┘
```

**Renderer-only swap (Approach B) blast radius:**

```
                  KEEP                 REPLACE              DELETE
                  ────                 ───────              ──────
        source_flow.py            build_render_flow.py     scene-batch-
        script_flow.py            (rename Remotion-        generator.md
        ratify.py (mostly)        specific helpers to      (unused)
        state_store.py            web-recording)
        session.py                                         scene-patch-
        ui_state.py               agents/remotion-         generator.md
        middleware.py             builder.md →             (unused)
        models.py                 agents/web-recorder.md
        controller.py             OR keep both with
        artifacts.py              `renderer:` switch
        params.py
        serialization.py          7 of 17 vm_* tools       harness/
        prompts.py                (vm_*remotion*,          runs/
        Producer prompt           vm_render_*,             evaluator/
        UI timeline               vm_package_*,            reviewer/
        17 → 14 typed tools       vm_build_publish_*       editor stubs

        87 → ~75 tests            ~12 tests rewritten      ~5 tests deleted

        ESTIMATED EFFORT: ~12-16 working days vs ~28-32 for full Approach A
```

### Stale Diagram Audit

- `docs/golden-demo.md` has the canonical full-product-path diagram. It is correct for v2 today. If Approach A or B lands, update.
- `AGENTS.md` lists native tool order. Correct for v2 today.
- `skills/video-maker-v2/SKILL.md` references workflow contract. Correct for v2. **Will go stale the moment T0 of the web-port spec runs.**

### Completion Summary

**What's good now (vs 2026-05-09):**
- Tavily search is deeper, cached, and called via an explicit `vm_websearch` tool — visible in the UI timeline.
- Scriptwriter has a hard `data_card_grounding` rule with named fabrication examples.
- Ratify `data_card_grounding` no longer infinite-loops on indented `items:`.
- `state.yaml` round-trips the `ratify` field correctly.
- Timeline renders `interrupted` state with `PauseCircle` + amber instead of pending.
- Error messages in `build_render_flow.py` and `langchain_tools.py` include `Fix:` guidance.
- README leads with `pnpm golden:playable` and lists prerequisites.

**What's open (in priority order):**
1. **Pivot decision** (Gap 1) — must precede T0 of the web-port spec.
2. **Controller dropout wiring** (Gap 2) — Prime Directive #1.
3. **Ratify-termination property test** (Gap 3) — regression net.
4. **Live UI proof** (Gap 4) — operator trust.
5. **Windows `pnpm ui:build`** (Gap 5) — ship readiness.
6. **Cleanup debt** (TODOS 5-10) — engineered-enough hygiene.

**CEO recommendation for the next branch:**

Carve `claude/<next>` as "renderer pivot decision + critical-gap sweep." Land in this order:

1. Write `docs/decisions/2026-05-12-renderer-pivot.md`.
2. Either (a) commit to Approach B and rescope the web-port spec, or (b) commit to Approach A and date Stage 2's definition of done.
3. Wire or delete `controller.block_if_tool_call_dropout`.
4. Add ratify-termination property test.
5. Add live-UI smoke + capture artifact.
6. Root-cause + fix Windows `pnpm ui:build`.

Stop short of (5) and (6) if the renderer pivot moves them — but (1)-(4) are independent of the renderer choice and should land regardless.

---

## Unresolved Decisions

1. **Renderer:** A / B / C. Recommend B; team decides.
2. **Stage 2 date and DoD** (only if Approach A is chosen).
3. **Standalone-skill distribution as a goal vs a side effect** (only if Approach A).
4. **Whether to delete `scene-batch-generator.md` / `scene-patch-generator.md` / evaluator/reviewer/editor descriptions, or to register them properly.**
5. **Whether `test_research_flow.py` should be renamed or deleted** post-v2 cleanup.

---

## Review Log

- 2026-05-12 01:06:33 UTC — `gstack/plan-ceo-review` v1.0.0 (non-interactive adaptation), HEAD `9380e5d`, branch `claude/gracious-gates-5F4bT`. Reviewed 18 Python source files (~2,872 LOC), 17 test files (87 tests, 86 pass / 1 env-skip), 17 typed tools, 12 React components, P0/P1 productization plan, Stage-1 web-port spec (3,465 lines), prior CEO reviews (`cc_ceo_reviews/20260509T012631Z`, `ceo_reviews/20260509-090645`). Posture: Rigorous reviewer + Strategic call-out on the renderer pivot.

— End of review —
