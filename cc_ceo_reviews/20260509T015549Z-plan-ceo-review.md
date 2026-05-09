# CEO Review — deepagents-video-maker (better-harness integration pass)

- **Date:** 2026-05-09 01:55:49 UTC
- **Branch:** `claude/gracious-gates-IfRVJ`
- **HEAD:** `8742562` (Merge PR #24 — folds previous `xMpq0` branch into master, then re-branches)
- **Reviewer skill:** `gstack/plan-ceo-review` framework (https://github.com/garrytan/gstack.git). The gstack CLI is **not installed** on this host (no `~/.claude/skills/gstack`, no Bun runtime); this review reproduces the skill's 11-section framework, prime directives, and required outputs in non-interactive written form. AskUserQuestion ceremonies are replaced by written recommendations and one explicit unresolved-decision block at the end.
- **Mode selected:** **HOLD SCOPE** with a meaningful caveat. This branch *does* introduce a new capability surface (autonomous harness optimisation via `better-harness`) — but the underlying pipeline (research → script) has not advanced. The right CEO move is to ratify the harness scaffold *or* call out that it's structural debt before scope expansion.
- **Posture:** Rigorous reviewer. Zero silent failures. Every error has a name. Diagrams mandatory. Permission #9 (better path) invoked on the harness-runner missing-dependency issue.

---

## 0. Pre-Review System Audit

### Repository state

- Working tree clean. Branch `claude/gracious-gates-IfRVJ`, HEAD `8742562`.
- The previous review (`cc_ceo_reviews/20260509T012631Z-plan-ceo-review.md`) ran on the now-merged branch `claude/gracious-gates-xMpq0`. Most of that review's findings still apply — this review focuses on **what changed since** and re-rates the still-open gaps.
- **Branch diff vs `master`** (8 commits ahead):
  - `edfbb8a feat: integrate better-harness for autonomous harness optimization` (the substantive commit)
  - `9d29aa0 docs: add CEO plan review (gstack plan-ceo-review framework)`
  - `1141c51 docs: note gstack install command in CLAUDE.md`
  - merges and a "potential fix" commit
- 19 files changed, **+1951/−2 LOC** — almost entirely additive.
- New test surface: `tests/evals/{train,holdout,scorecard}` — 51 new tests (26+14+11). Combined suite **119 tests, all green** (was 68 before).
- Single outstanding `FIXME` is the same one from the prior review (`scene-batch-generator.md:196`, intentional defensive fallback). No new warnings or dead-code introductions in src/.

### What's new on this branch

| Surface | What landed | Risk |
|---|---|---|
| `harness/video-maker.toml` | 9 declared optimisable surfaces (prompts, agents, tools, agent factory, milestones, ratify rules) | Low if harness CLI works; **High** if it doesn't (see C1) |
| `tests/evals/train/` | 5 train cases (skill-md sections, tool registry, ratify pass, research/script task contracts) | Healthy |
| `tests/evals/holdout/` | 3 regression-guard cases (research ratify, script ratify, state machine) | Healthy |
| `tests/evals/scorecard/` | 2 final-validation cases (full pipeline, producer skill) | Healthy |
| `tests/evals/conftest.py` | `--model` and `--evals-report-file` pytest options + JSON reporter | Solid; no parallel safety (noted in code) |
| `package.json` | 6 new pnpm scripts (`evals:*`, `harness:validate`, `harness:run`) | Misses CI-runnable variants |
| `CLAUDE.md` | Documents harness commands, eval structure, surfaces table | Good |
| `cc_ceo_reviews/20260509T012631Z-plan-ceo-review.md` | The prior review, committed | First time the team has persisted a plan-CEO review in-repo |

### What's still in flight / outside this branch

- **Assets and assembly milestones** still declared in `session.DEFAULT_MILESTONES` but unimplemented. Unchanged from prior review.
- **Aspirational SKILL.md mismatch** — same as prior review. Per-scene loop, GAN Evaluator, HITL approval all still designed-but-not-wired. The `eval_mode == "gan"` branch in `skills/video-maker/ratify/script-rules.md` references a Phase 4 evaluator path that is documented but unwired in `create_video_maker_agent`.
- **`skills/feature-pipeline/SKILL.md`** — a new orchestrator skill describing a `/feature-pipeline` command that chains `superpowers:writing-plans → plan-eng-review → executing-plans → verification → ship`. None of those superpowers skills are installed locally either. **Adds a third aspirational layer** on top of an already aspirational SKILL.md and the gstack skills referenced in CLAUDE.md.
- **`runs/` directory** is mentioned as the harness output dir in CLAUDE.md, package.json, and the harness TOML — but **`runs/` is not in `.gitignore`** (only `output/` and `.tmp/` are). This is a slow-bleed risk: a harness run will produce hundreds of MB of artifacts that quietly get tracked.
- **`uv run better-harness ...` does not work** on this host — `better-harness` CLI is not installed. It is *not* in `pyproject.toml` dependencies. CLAUDE.md and `package.json` reference it as if it ships with `uv sync`, but it does not. **This is the central new finding of this review.**

### Recently touched files (signal: where attention is going)

Almost all changes are in `harness/` and `tests/evals/`. The team has invested in scaffolding for autonomous optimisation but has not yet *run* the optimisation loop end-to-end against this codebase. The prior review's recommendations (PyYAML migration, Tavily failure surfacing, critical gap fixes) **have not been picked up** — they remain open.

---

## Step 0: Premise Challenge + Mode Selection

### 0A. Premise Challenge — is this the right problem?

> "Integrate better-harness so an outer Deep Agent can autonomously propose edits to producer prompts, subagent prompts, tools, and ratify rules, validated against train/holdout/scorecard eval suites."

Three premises worth challenging directly:

1. **"Now is the right time to invest in autonomous harness optimisation."** The prior review identified 5 critical silent-failure gaps and ~20 TODOs of small-effort cleanup work. *None* of those have been addressed on this branch. Before paying the LLM bill to have an outer agent propose prompt edits, the inner system should be tight enough that the optimiser is optimising signal, not noise. Specifically: if `block_if_tool_call_dropout` only protects research, the outer agent will see "script milestone fails" and propose script-prompt rewrites — but the actual root cause is dropout detection coverage. *The optimiser is only as honest as its eval signal.* **This is the strongest premise to challenge.** Recommendation: close gaps #1–#5 from the prior review *before* a real optimisation run.

2. **"`better-harness` is a hard dependency, but pyproject.toml doesn't declare it."** `pnpm harness:validate` and `pnpm harness:run` both invoke `uv run better-harness …`. On a fresh `uv sync`, this fails with `error: Failed to spawn: better-harness`. The CLI lives in the deepagents repo's `examples/better-harness/` directory and must be installed separately — but neither CLAUDE.md nor README documents this, and `pyproject.toml` does not pin it. **Three options:**
   - (a) Add it to `pyproject.toml` as a `[tool.uv.sources]` git dependency targeting the upstream path.
   - (b) Document the install steps explicitly in CLAUDE.md and README.
   - (c) Both. Recommended.

   Today the harness is *advertised* but *not runnable* without out-of-band setup. That violates the "every error has a name" rule — a contributor running `pnpm harness:run` sees an opaque spawn error.

3. **"Eval suites with mocked artifacts validate the harness surfaces."** The scorecard eval (`test_full_pipeline.py`) writes `_VALID_RESEARCH` and `_VALID_SCRIPT` directly to disk and ratifies them — it never invokes the LLM. That's appropriate for a deterministic test, *but* the harness exists to optimise *prompt* surfaces. **A prompt change cannot be validated by a test that bypasses the LLM.** The current eval suite measures structural integrity (tools registered, files exist, ratify passes on known-good content) — it does not measure whether the producer's revised prompt actually drives a real model to produce that known-good content. The harness loop will iterate happily on prompt edits while the evals don't actually exercise those prompts. **This is a real premise inversion.**

   Two ways to fix: add at least one stub-model end-to-end eval that exercises `create_video_maker_agent` against a deterministic LLM stub (matches the prior review's TODO #13); or accept that this iteration of the harness only optimises the *non-prompt* surfaces (langchain_tools, agent factory, ratify rules), and explicitly document that.

**Verdict on premises:** the harness scaffold is well-built and the eval taxonomy (train/holdout/scorecard) is sound. Two implementation premises (missing CLI dependency, evals that don't exercise prompts) need to be addressed before the loop produces actual signal.

### 0B. Existing Code Leverage — what already partially solves this?

| Sub-problem | Existing code | Reused on this branch? |
|---|---|---|
| Pytest harness for unit tests | `tests/deepagents_video_maker/` (68 tests) | Reused as a pattern (eval suites copy the `_invoke(tool, ...)` helper) |
| `--evals-report-file` JSON contract | None pre-existing | New, added in `tests/evals/conftest.py` |
| Tool registry introspection | `build_langchain_tools()`, `build_native_tools()` | Reused in train/test_tool_registry.py |
| Skill-file structural assertions | `tests/deepagents_video_maker/test_skill_files.py` | Reused as a pattern in train/test_skill_md_sections.py |
| Ratify happy-path tests | `tests/deepagents_video_maker/test_ratify_research.py`, `test_ratify_script.py` | Reused as a pattern in train/test_ratify_research_pass.py and scorecard/test_full_pipeline.py |
| Pipeline state-machine test | `tests/deepagents_video_maker/test_session.py` | Pattern lifted into holdout/test_regression_state_machine.py |

The new tests largely **duplicate the structural assertions of the unit tests** at a different file location. That isn't wrong (the eval suites are run separately and their output JSON is consumed by better-harness), but it does mean a structural change that should fail one breakable assertion will fail it twice. Acceptable but worth flagging: when a unit test and a holdout regression test cover the same property, the holdout test is what the harness runner sees. Consider deduplicating or, conversely, making the holdout suite cover *strictly more* than the unit suite.

### 0C. Dream State Mapping

```
  CURRENT STATE                    THIS BRANCH                  12-MONTH IDEAL
  ─────────────                    ───────────                  ──────────────
  research → script                edfbb8a:                     Full pipeline:
  runnable via                     better-harness               research → script →
  Producer + 9 typed tools         scaffold:                    style → assets →
                                   - 9 surfaces                 assembly → final video
  Assets/assembly:                 - 51 evals (train/
  declared, not                      holdout/                   Quality:
  implemented                        scorecard)                 Layer-1 ratify +
                                   - JSON reporter              Layer-2 reviewer +
  68 tests green                                                GAN Evaluator
                                   Pipeline forward             contract loop
                                   progress: 0
                                                                Optimisation:
  Aspirational SKILL.md            5 critical gaps              `better-harness run`
  unchanged                        from prior review:           closes loop on a
                                   ALL STILL OPEN               real LLM, multi-day
                                                                runs, surface deltas
  No optimisation loop                                          merged via PR
                                   New capability:
                                   `better-harness               Test ambition:
                                    validate/run`                Stub-model E2E +
                                   (BUT CLI not                  adversarial topics +
                                    installed)                   chaos suite
```

This branch advances the project **on the tooling axis** (autonomous optimisation scaffolding) but still does not move the runnable pipeline forward by a milestone, and does not close any of the prior review's critical gaps. **Two consecutive consolidation/scaffolding branches** is now the pattern. The team should make a conscious decision on the next branch: either close the open gaps + ship v0.1 (Approach B+C from prior review), or open the per-scene loop (Approach A). **Continuing to add scaffolding without closing existing scar tissue is the failure mode to avoid.**

### 0C-bis. Implementation Alternatives (mandatory)

The "what to build next" decision is now sharper because better-harness is in. Three alternatives:

```
APPROACH X: Run the harness loop now and let the outer agent propose edits.
  Summary: `uv run better-harness run harness/video-maker.toml --max-iterations 10`
           against the current train/holdout. Accept whatever the outer agent
           proposes if scorecard passes don't regress.
  Effort:  S (run the command; review outputs)
  Risk:    HIGH — the harness CLI is not installed (must fix first); the evals
           don't exercise prompts (so prompt edits get cargo-culted by the
           outer agent without real signal); the 5 critical gaps mean the
           outer agent will likely "fix" symptoms not causes.
  Pros:    - Validates the harness end-to-end as advertised.
           - Generates real telemetry on which surfaces are amenable to
             optimisation.
  Cons:    - Probable false positives ("agent improved!", but only because
             the eval was structural, not behavioural).
           - LLM cost for an unknown payoff.
           - Compounds existing tech debt instead of paying it down.

APPROACH Y: Close the 5 critical gaps from the prior review, then run harness.
  Summary: TODOs 1-5 from prior review (PyYAML, Tavily surfacing, dropout
           coverage, output-dir collision guard, SKILL.md scope reconciliation).
           Then add the missing better-harness CLI dependency. Then run the
           harness loop against a tightened inner system.
  Effort:  M (1-2 days human, ~half day with CC)
  Risk:    LOW — pure hardening, then an end-to-end smoke test.
  Pros:    - Optimiser sees a clean signal.
           - Pays down the most expensive scar tissue.
           - Same week you can show "harness loop reduced 1 train failure".
  Cons:    - Yet another non-pipeline-forward branch.
  Reuses:  Everything currently in tree.

APPROACH Z: Pivot to v0.1 ship now, defer harness optimisation.
  Summary: Approach B+C from prior review, augmented by:
           - Treat the harness scaffold as "ready for use, not yet run."
           - Lock the manifest.json schema as a public contract.
           - Ship v0.1 of the research → script tool.
           - Run the harness loop *after* v0.1 ships, against real user data.
  Effort:  M (3-5 days with CC)
  Risk:    LOW
  Pros:    - User-visible value first, optimisation second.
           - The harness becomes useful only after real users feed real failure
             modes back. Premature optimisation is a real risk here.
  Cons:    - Defers Approach Y's cleanup unless it's bundled.

RECOMMENDATION: Approach Y → then re-evaluate Z vs the per-scene loop.
  WHY: The harness is the right long-term investment, but it's a force
  multiplier — and it multiplies whatever signal it gets. Today the signal
  is partly noise (silent Tavily, output-dir overwrite, single-milestone
  dropout coverage). Pay down those 5 things, validate the harness against
  a clean baseline (the "1 iteration, no changes" command in CLAUDE.md is
  exactly right for this), and only then commit the LLM budget for a real
  optimisation run.
```

### 0D. Mode-Specific Analysis (HOLD SCOPE)

**Complexity check:** Branch is +1951 LOC almost entirely *test* / *config* code. Source-of-record `src/deepagents_video_maker/*.py` is unchanged from prior review (no new modules, no LOC drift). The complexity surface introduced is in the eval taxonomy itself: train/holdout/scorecard distinction, JSON reporter contract, harness TOML schema. All of that is reasonable for what's intended.

**Minimum set that achieves the stated goal (working harness loop):**
- `better-harness` CLI in dependencies (currently missing).
- Working eval suites (✓).
- Configured surfaces (✓).
- *At least one* eval that exercises a prompt against an LLM (currently missing — all evals are structural).

The first and third items are the gaps to close before declaring the harness operational.

### 0E. NOT in Scope (this review respects it)

- All items from prior review that are still NOT in scope (assets, assembly, per-scene loop, GAN Evaluator, Reviewer/Editor subagents, web-UI tests, production deploy).
- Per-prompt automated A/B testing across model families — this branch enables it but does not perform it.
- Cost telemetry for harness runs — not yet wired.

---

## Section 1: Architecture Review

### Component dependency graph (current — unchanged from prior review)

The runtime architecture (Producer → typed tools → subagents → filesystem) is identical to the prior review's diagram. The new architecture surface is the **outer optimisation loop**:

```
                ┌────────────────────────────────────────────┐
                │  better-harness run (outer Deep Agent)     │
                │  - reads harness/video-maker.toml          │
                │  - reads/edits 9 declared surfaces         │
                │  - runs `uv run pytest tests/evals/<set>   │
                │      --evals-report-file <tmp>.json`       │
                │  - keeps surface edits iff combined pass   │
                │    count improves                          │
                └────────────────────┬───────────────────────┘
                                     │
                                     │  --evals-report-file
                                     ▼
              ┌──────────────────────────────────────────────┐
              │  pytest (tests/evals/conftest.py reporter)   │
              │  - emits JSON: {timestamp, model, total,     │
              │    passed, failed, results: [...]}           │
              └────────────────────┬─────────────────────────┘
                                   │
                                   ▼
              ┌──────────────────────────────────────────────┐
              │  eval suites:                                 │
              │  - train (5 cases, signal for proposals)     │
              │  - holdout (3 cases, regression guard)       │
              │  - scorecard (2 cases, final E2E gate)       │
              └──────────────────────────────────────────────┘
                                   │
                                   │  imports
                                   ▼
              ┌──────────────────────────────────────────────┐
              │  src/deepagents_video_maker/* (under test)   │
              │  - all tests bypass the LLM today;            │
              │    no agent invocation in evals               │
              └──────────────────────────────────────────────┘
```

### Architecture findings

**A1 — All findings A1–A6 from the prior review remain open.** Re-rated:

| Prior finding | Status | Notes |
|---|---|---|
| A1 aspirational vs operational pipeline gap | OPEN, **worsened** | New `skills/feature-pipeline/SKILL.md` adds a third aspirational layer. Now contributors face SKILL.md (per-scene/HITL designed), feature-pipeline SKILL.md (gstack/superpowers chained), and the actual two-milestone runtime. |
| A2 13-kwarg fan-out across typed tools | OPEN | Will compound when assets land. |
| A3 dropout detection only on research | OPEN | Even more important now: the harness will optimise script-milestone prompts in a regime where script dropout fails silently. |
| A4 web-UI integration opaque | OPEN | No new test coverage. |
| A5 rollback posture | Healthy | Unchanged. |
| A6 timestamp-collision output_dir overwrite | OPEN | Eval suite uses fixed timestamps so this doesn't bite tests, but it bites real users. |

**A7 (new) — `runs/` directory is not gitignored.** `harness:run` writes to `runs/baseline/` and `runs/optimised/`. These are build artifacts. **Add `runs/` to `.gitignore` immediately.**

**A8 (new) — Eval suites bypass the LLM.** Train/holdout/scorecard never instantiate `create_video_maker_agent` with a real or stub model. They invoke typed tools directly, write canned artifacts to disk, and assert ratify passes. This is a deliberate choice (deterministic, fast, no API key needed in CI) — but it means **the producer-prompt and subagent-prompt surfaces in `harness/video-maker.toml` are not actually exercised by the eval suite**. The outer agent can edit `skills/video-maker/SKILL.md` and the train/holdout/scorecard test count will not change at all. The eval signal is "did surface still pass structural assertions" — not "did the agent get better." Document this honestly or add at least one stub-LLM eval (TODO #13 from prior review).

**A9 (new) — `tests/evals/conftest.py` reporter is not parallel-safe.** Module-level `_RESULTS` mutated by hookimpl. Documented in the file's own docstring. Fine for serial CI, but the comment should also live in CLAUDE.md so contributors don't naively add `pytest-xdist` to evals. Not critical.

**A10 (new) — `harness/video-maker.toml` declares `langchain-tools` and `agent-factory` as `workspace_file` surfaces.** That means the outer agent can rewrite `langchain_tools.py` (410 LOC of typed-tool wrappers) and `agent.py` (the factory). Risk: a malformed edit to either file could break import, which would crash all eval suites at collection time and thus look (to the harness) like "all evals fail" — the proposal would be rejected, but the diagnostic message in the harness output may not point at the import error clearly. **Add a "smoke import" eval at the top of train/** that simply imports `agent.create_video_maker_agent` and `langchain_tools.build_langchain_tools` — if it fails, every other eval is skipped with a clear "module did not import" reason. This is a small protective change.

### Required architecture diagrams produced

1 (above — outer optimisation loop). The runtime diagram from the prior review is still current and not reproduced.

---

## Section 2: Error & Rescue Map

The prior review's table is still current. Re-rated for this branch:

| Prior gap | Status | This branch's effect |
|---|---|---|
| 1. Silent Tavily absence | OPEN | Now the outer optimiser will run `--evals-report-file` against research evals that pass structurally even when Tavily would have been needed at runtime. False green. |
| 2. `init_video_session` overwrite | OPEN | Eval-side mitigated by fixed timestamps, but unchanged in source. |
| 3. Dropout detection only research | OPEN | See A3 — script-milestone optimisation rounds will be lossy. |
| 4. `patch_deepagents_path_validation` silent no-op | OPEN | Dead code still present. |
| 5. `UnicodeDecodeError` on garbage research.md | OPEN | |
| 6. Hand-rolled YAML corruption on adversarial topics | OPEN | |

### New gaps introduced by this branch

| METHOD/CODEPATH | FAILURE MODE | RESCUED? | USER SEES |
|---|---|---|---|
| `pnpm harness:validate` | `better-harness` not installed | N | "error: Failed to spawn: `better-harness`" — opaque, no install hint |
| `pnpm harness:run` | Same | N | Same |
| `runs/` accidentally committed | `runs/` not in .gitignore | N | First contributor to run the harness will commit dozens of artifact dirs |
| Outer agent rewrites `langchain_tools.py` to a syntactically-broken state | Import collapses, all evals skip-fail | Partial | Harness sees "100% fail", rejects proposal. But the diagnostic is buried — no hint that **the proposal broke the import**, not the prompts. Add a smoke-import test to surface this clearly. |
| Eval reporter parallel race | `_RESULTS` mutation under xdist | N | Silent missing rows in JSON report |
| Eval suite emitted JSON consumed by better-harness | Schema drift between conftest.py reporter and what better-harness expects | Unknown | If schema diverges, the harness CLI fails to parse — likely with a Python traceback. **Test against an actual better-harness install to confirm contract.** |

### Critical gaps total (this branch + prior open)

- **5 still-open from prior review.**
- **3 new on this branch:** missing `better-harness` dependency, `runs/` not gitignored, eval signal does not cover prompt surfaces.

**The "missing better-harness CLI dependency" is the single highest-priority new finding** because it makes the entire branch's stated capability non-runnable from a fresh checkout.

---

## Section 3: Security & Threat Model

Threat surface unchanged. New considerations introduced by the harness:

| Threat | Likelihood | Impact | Mitigated? |
|---|---|---|---|
| Outer agent (with file-edit access via the better-harness runtime) rewrites `langchain_tools.py` to insert malicious Python that runs at import | Low (the outer agent is your own LLM, but a prompt-injected document could redirect it) | High | No. The outer agent has unconstrained edit access to declared surfaces. The "kept iff pass count improves" gate is **behavioural**, not **adversarial** — a payload that doesn't break tests but adds malicious code (e.g., exfiltrating env vars during a tool call) would be silently accepted. |
| LLM API costs from harness run-amok | Medium | Medium | Capped by `max_iterations = 10` in harness/video-maker.toml. Document the per-iteration cost ceiling in CLAUDE.md. |
| Train/holdout/scorecard sets are committed plaintext, so an attacker who understands the eval can craft adversarial inputs that pass all evals | Low (this is a single-team tool) | Medium | None. Standard goodhart-on-evals risk. Out of scope for v0.1 but worth a note. |

**Recommendations**

- **S5 (new).** Document that the outer harness agent has filesystem-edit access to declared surfaces; a hostile prompt-injection payload (e.g., from a poisoned local-file research input) could redirect the *outer* agent to introduce code. Run the harness in a **sandboxed worktree** (e.g., a git worktree on a throwaway branch) and never directly against `master`. CLAUDE.md should make this explicit.
- **S6 (new).** Add a budget cap. `max_iterations = 10` is good, but a per-run dollar budget (or token-count cap) is better. Surface it in the TOML.
- **S7 (new).** When the harness CLI is finally installed, pin its version (or git SHA) in `pyproject.toml` so a remote-side update doesn't silently change the optimiser's behaviour.

---

## Section 4: Data Flow & Interaction Edge Cases

### Data flow: harness optimisation loop

```
  outer Deep Agent (claude-sonnet-4-6)
      │
      │ reads:
      │   - harness/video-maker.toml
      │   - 9 declared surfaces (file contents)
      │   - eval failures JSON (tests/evals/<set>/<tmp>.json)
      ▼
  proposes edit (file diff against a surface)
      │
      ▼
  applies edit in-place to the surface file
      │
      ▼
  invokes:  uv run pytest <eval_set_path>
            --evals-report-file <tmp>.json
            --model <inner_model>
      │
      ▼
  reads tmp.json, computes pass-count delta
      │
      ├─ improved?  ────▶  KEEP edit, write next iteration
      │
      └─ regressed? ────▶  REVERT edit (git? or in-memory snapshot?)
                           — ❓ how the revert works is not in the TOML
                             nor documented in CLAUDE.md. Worth clarifying:
                             does it rely on git stash, or on an internal
                             snapshot? If it's git, does the harness commit
                             accepted edits or leave them dirty?
```

Shadow paths:

- **Nil:** harness CLI missing → spawn error, the user sees opaque message.
- **Empty:** evals all pass on baseline → outer agent has no signal, may propose random edits to discover gradients. Bound this with `max_iterations`.
- **Wrong type:** outer agent edits `langchain_tools.py` to a non-Python file → import fails → all evals fail → proposal rejected. Acceptable but see A10 about clearer diagnostic.
- **Upstream error:** Anthropic 429 mid-iteration → outer agent retries? aborts? — unknown. Document.
- **Encoding:** SKILL.md is mostly Chinese; outer agent edits in English may produce mixed-language artifacts. Not a failure but a code-review smell.

### Interaction edge cases

| Interaction | Edge case | Handled? |
|---|---|---|
| User runs `pnpm harness:run` for the first time | better-harness CLI missing | **N — spawn error** |
| User runs `pnpm harness:validate` (intended sanity check) | Same | **N** |
| Harness produces `runs/` outputs | `git status` shows them as untracked | **N** (not gitignored) |
| Outer agent edits `agent.py` and breaks import | All evals fail | partial (rejected, but diagnostic unclear) |
| Outer agent introduces a hot path that succeeds train but fails scorecard | scorecard set catches | Y — by design, this is exactly what scorecard is for |
| Two contributors run the harness concurrently against the same checkout | Race on surface files | Document: not supported |
| Eval suite uses fixed timestamps `20260601-000000` etc. and runs twice | First run creates `output/20260601-000000-video-...`, second run will encounter "directory exists" — but `init_video_session` uses `mkdir(exist_ok=True)` and overwrites silently | **N — but masked because each test uses tmp_path** |

**Recommendation:** the eval suites all use `tmp_path` correctly, so the timestamp-collision bug doesn't bite the eval — but the underlying source bug remains.

---

## Section 5: Code Quality Review

### What's good on this branch

- The new eval files are well-commented, consistent in style with the existing `tests/deepagents_video_maker/`, and use the same `_invoke(tool, ...)` helper pattern. Pleasant.
- `tests/evals/conftest.py` is well-documented including its parallel-unsafe limitation.
- `harness/video-maker.toml` is well-structured with descriptive `description` fields per surface.
- Conventional commit style maintained (`feat:`, `docs:`, `chore:`).

### What's not so good

- **Q9 (new). The `_invoke(tool, ...)` helper is duplicated in three eval files.** `tests/evals/scorecard/test_full_pipeline.py:25`, `tests/evals/holdout/test_regression_state_machine.py:25`, and others. Pull into `tests/evals/conftest.py` as a fixture or module-level helper. Half-hour fix.
- **Q10 (new). `tests/evals/train/test_skill_md_sections.py` accepts both Chinese and English heading variants** (`"参数收集" in text or "Parameter" in text or "parameter" in text`). That's the correct accommodation given the project's language conventions, but it makes the assertion *very* permissive — any document with the word "parameter" anywhere passes. If the optimiser drifts the SKILL.md to a structurally weak file, this test won't catch it. Tighten by requiring the substring within a heading line specifically (e.g., `re.search(r"^#+\s+.*[Pp]arameter", text, re.M)`).
- **Q11 (new). Test path roots are hardcoded relative.** `Path("skills/video-maker")` and `Path("harness/video-maker.toml")` work only when pytest is run from the project root. The unit tests use `tmp_path` and importable paths and avoid this. Pull a `_PROJECT_ROOT` fixture into `tests/evals/conftest.py` so the tests work from any CWD.
- **Q12 (new). The mocked `_VALID_RESEARCH` and `_VALID_SCRIPT` constants are duplicated across the train and scorecard eval files.** `tests/evals/scorecard/test_full_pipeline.py:35-60` and `tests/evals/train/test_ratify_research_pass.py` likely overlap. (The diff statistic suggests so.) Pull into a shared `tests/evals/_fixtures.py`. Makes "what counts as known-good content" a single source of truth.

All prior code-quality findings (Q1–Q8) are still open.

---

## Section 6: Test Review

### What this branch introduces

| Surface | New | Quality |
|---|---|---|
| Train evals | 5 cases, 26 tests | Structural assertions on SKILL.md, tools, ratify happy path. **None exercise the LLM.** |
| Holdout evals | 3 cases, 14 tests | Regression guards on ratify and state machine. Solid. **None exercise the LLM.** |
| Scorecard evals | 2 cases, 11 tests | End-to-end happy path with mocked artifacts. **Does not exercise the LLM.** |

51 new tests. **Every single one bypasses the LLM** — they call typed tools directly and write canned artifacts. The harness is set up to optimise prompt surfaces, but the eval signal is not behavioural with respect to prompts. **This is the test-ambition gap to close before declaring the harness operational.**

### Coverage assessment (combined suite, 119 tests, all green)

Compared to prior review:

| Prior TODO | Status |
|---|---|
| T1. End-to-end producer-protocol stub-model test | OPEN — and now more important because the harness depends on it. |
| T2. Tool-call dropout detection on script milestone | OPEN |
| T3. Goal-yaml round-trip with adversarial topics | OPEN |
| T4. Session-init collision test | OPEN |
| T5. Ratify regex edge cases | OPEN |
| T6. CI does not run web-UI tests | OPEN |

**New TODOs introduced:**

- **T7 (new).** Smoke-import test at the top of train/ — fails fast and clearly when the outer agent breaks an import.
- **T8 (new).** At least one stub-LLM eval that exercises `create_video_maker_agent` + `task(researcher)` against a deterministic stub model. Without this, prompt surfaces in the harness TOML are not measurably optimised.
- **T9 (new).** A regression test that confirms `tests/evals/conftest.py` writes a JSON report compatible with whatever schema better-harness consumes. (Cross-repo contract; needs a real `better-harness` install to verify.)

### Test pyramid

Excellent unit coverage, healthy integration coverage (research_flow, script_flow), now adequate "structural eval" coverage. **Still zero behavioural E2E.** The harness amplifies the cost of this gap.

### Test ambition checks

- "2am Friday confidence" → still T1 (now also T8). Without it, the harness's success metric is structural, not behavioural.
- "Hostile QA": adversarial topics (T3) still wanted. Add: outer agent that returns garbage edits 100 times; does the harness loop terminate cleanly?
- "Chaos test": inject `<sop_invocation>` into a script-milestone LLM stub response and assert dropout-blocking. Currently only research-side tests exist.

---

## Section 7: Performance Review

LLM-bound, single-user. The harness loop changes this slightly: 10 iterations × pytest-runtime-per-eval-set is the new perf consideration.

- Eval suite runtime today: **1.27s for all 119 tests.** Excellent.
- Per harness iteration: ~3× run (train + holdout + scorecard) ≈ 4–5s of pytest + LLM round-trip latency for the outer agent's proposal. Dominated by LLM, not pytest. Fine.
- **P9 (new).** No caching on eval-side fixtures. Not a problem at this scale; flag for later if eval count grows by 10×.

No issues.

---

## Section 8: Observability & Debuggability Review

All prior findings (O1–O6) remain open. New on this branch:

- **O7 (new). Harness run output structure is undocumented.** What lives in `runs/baseline/`? `runs/optimised/`? No mention in CLAUDE.md or the TOML. When a run completes, where does the user look for the diff between iterations? Document.
- **O8 (new). No per-iteration audit trail.** If iteration 7 of 10 broke a surface and was rejected, can the team reconstruct the rejected proposal? This is a question for the better-harness CLI itself, but the project should document its expectation. *This is exactly the gap that "outside voice" debugging needs.*
- **O9 (new). LangSmith tracing on the *outer* agent (the optimiser).** The inner-agent CLI sets `LANGSMITH_TRACING=true` (`scripts/deepagents_video_maker.py:36`) but nothing tells the outer agent to do the same. If the harness loop misbehaves, you'll wish you'd had traces. Document the env var setup for the outer model in CLAUDE.md.

---

## Section 9: Deployment & Rollout Review

Prior findings (D1–D7) all open. New on this branch:

- **D8 (new). `better-harness` CLI is not in pyproject.toml.** Highest-priority cleanup from this branch. Suggested fix:
  ```toml
  # in pyproject.toml or in a separate uv.tool config:
  [tool.uv.sources]
  better-harness = { git = "https://github.com/langchain-ai/deepagents", subdirectory = "examples/better-harness", rev = "<pinned-sha>" }
  ```
  Then `uv add better-harness` (or pin via `dev` group). Without this, every harness command in `package.json` is broken from a fresh `uv sync`.
- **D9 (new). `runs/` not gitignored.** One-line .gitignore fix.
- **D10 (new). No CI step for evals.** `pnpm test:py` runs unit tests; there is no `pnpm test:evals` step in CI. The eval suites should run on every PR — they exist precisely to be regression guards.

---

## Section 10: Long-Term Trajectory Review

### Tech debt introduced or carried

Prior debt (L1–L8) all still open. New on this branch:

- **L9 (new).** Three aspirational/orchestration layers now live in `skills/`: `video-maker/SKILL.md` (per-scene/HITL designed), `feature-pipeline/SKILL.md` (gstack/superpowers chained), and the actual two-milestone runtime. Pick one source of truth and demote the others to `docs/design/`.
- **L10 (new).** Eval taxonomy commits the project to a contract with better-harness. If better-harness changes its TOML format, JSON report schema, or surface kinds, the project must follow. Track this as a vendored-contract risk and pin a known-working better-harness version.
- **L11 (new).** `runs/` will accumulate. Even with .gitignore, a contributor's local `runs/` will balloon. Add a `pnpm harness:clean` script: `rm -rf runs/`. Trivial but hygiene-positive.

### Reversibility ratings (delta this branch)

| Decision | 1–5 |
|---|---|
| Adopt better-harness as the optimisation surface | 4 — could swap to a hand-rolled loop, but the eval taxonomy stays |
| Eval taxonomy (train/holdout/scorecard) | 5 — these are pytest paths, fully reversible |
| TOML surfaces declaration | 5 — config file |
| Pinning outer model to claude-sonnet-4-6 | 5 — env var |

### Path dependency (new)

- **The JSON report schema in `tests/evals/conftest.py` is now a contract** between this project and better-harness. Document it as such (it already is, in the conftest docstring — promote to README).
- **The 9 declared surfaces are an implicit "what's optimisable" contract** — adding a 10th later is fine; removing one breaks any baselined run. Tag the harness TOML with a schema version.

### The 1-year question

A new engineer looking at this repo cold:
- README + CLAUDE.md + harness TOML + the eval suites = a *better* onboarding signal than the prior review, because the train/holdout/scorecard split clearly communicates "what we test for, what we guard against, what we ship-block on."
- But the three aspirational layers (L9) are now harder to reconcile.
- And the missing better-harness dependency means the first thing a new contributor tries (`pnpm harness:validate` per CLAUDE.md) fails opaquely.

---

## Section 11: Design & UX Review

No UI scope on this branch. Skipping per skill rules.

The `skills/feature-pipeline/SKILL.md` mentions a "/feature-pipeline" entry point and references AskUserQuestion ceremonies — that's CLI/agent UX, not graphical UX, and it's documented but not wired in this branch.

---

## Required Outputs

### NOT in scope

| Item | Why deferred |
|---|---|
| All items from prior review's NOT-in-scope list | Still deferred |
| Running the harness loop end-to-end against a real LLM | Awaiting CLI install + critical-gap closure |
| Web-UI test suite | Same as prior |
| Optimisation cost telemetry | New deferred item |

### What already exists (and is reused)

| Sub-problem | File | Reused? |
|---|---|---|
| Pytest harness pattern | `tests/deepagents_video_maker/conftest.py` | ✅ pattern reused in eval conftest |
| Tool-registry introspection | `build_langchain_tools()` | ✅ |
| Skill-file structural assertions | `test_skill_files.py` | ✅ pattern lifted |
| `_invoke(tool, ...)` helper | inline in unit tests | ⚠️ duplicated 3× across eval files |
| Mock artifact constants | `_VALID_RESEARCH`/`_VALID_SCRIPT` | ⚠️ duplicated across train and scorecard |

### Dream state delta

This branch advances the project on the **tooling axis** (autonomous optimisation scaffold). It does not advance the runnable pipeline forward and does not close any of the prior review's critical gaps. **Two consecutive non-pipeline-forward branches.** The next branch should explicitly choose Approach Y (close gaps + first harness run) or pivot to Approach Z (ship v0.1).

### Error & Rescue Registry (combined: prior review + this branch)

**Total open critical gaps: 8** (5 prior + 3 new).

1. Silent Tavily absence (prior).
2. `init_video_session` overwrite (prior).
3. Dropout detection only research (prior).
4. `patch_deepagents_path_validation` silent no-op (prior).
5. `UnicodeDecodeError` on garbage research.md (prior).
6. Hand-rolled YAML corruption on adversarial topics (prior).
7. **Missing `better-harness` CLI dependency** (new — central new finding).
8. **`runs/` not gitignored** (new).

### Failure Modes Registry

| CODEPATH | FAILURE MODE | RESCUED? | TEST? | USER SEES? | LOGGED? |
|---|---|---|---|---|---|
| (all from prior review) | unchanged | — | — | — | — |
| `pnpm harness:validate` | CLI missing | N | N | spawn error | N — **CRITICAL GAP** |
| `pnpm harness:run` | CLI missing | N | N | spawn error | N — **CRITICAL GAP** |
| `runs/` left in working tree | not gitignored | N | N | committed accidentally | N |
| outer agent breaks import | All evals skip-fail | partial | N (no smoke-import test) | "100% fail", unclear cause | N |
| eval reporter parallel race | xdist enabled | N | N | silent missing rows | N |
| eval JSON schema drift vs better-harness | upstream contract change | N | N | parse error in harness CLI | N |

### TODOS proposed (priority order, ready to lift into TODOS.md)

Keeping prior 20 TODOs intact, adding 9 new ones from this branch:

| # | Title | Priority | Effort (CC) |
|---|---|---|---|
| **N1** | **Add `better-harness` to pyproject.toml dependencies (pin a SHA)** | **P0** | XS |
| **N2** | **Add `runs/` to `.gitignore`** | **P0** | XS |
| **N3** | Smoke-import test at the top of `tests/evals/train/` | P1 | XS |
| **N4** | Pull duplicated `_invoke` helper and `_VALID_*` fixtures into `tests/evals/conftest.py` and `tests/evals/_fixtures.py` | P2 | S |
| **N5** | Use a `_PROJECT_ROOT` fixture in eval conftest so tests don't depend on CWD | P2 | XS |
| **N6** | Document harness install steps and outer-agent LangSmith tracing setup in CLAUDE.md | P2 | XS |
| **N7** | Tighten skill-md section regex assertions (require heading context, not bare substring) | P2 | XS |
| **N8** | Add CI step for `pnpm evals:all` (PR-blocking) | P1 | XS |
| **N9** | Document `runs/` output structure + add `pnpm harness:clean` | P3 | XS |
| **N10** | Per-iteration cost cap in harness TOML | P3 | S |
| **N11** | Sandbox-worktree convention for harness runs (security note in CLAUDE.md) | P2 | XS |
| **N12** | Add at least one stub-LLM eval that exercises `create_video_maker_agent` (also closes prior TODO #13) | P1 | M |
| **N13** | Pick one source of truth between SKILL.md, `feature-pipeline/SKILL.md`, and the actual runtime; demote the rest to `docs/design/` | P2 | S |

**P0 means "blocking for the harness branch's stated capability."** N1 and N2 should land before this branch is considered done.

### Diagrams produced

1. ✅ Outer optimisation loop (Section 1).

### Diagrams missing (to add when the loop runs end-to-end for the first time)

- Sequence diagram: outer agent ↔ pytest reporter ↔ surface files ↔ git/snapshot rollback.
- State machine for the harness iteration lifecycle (proposed → applied → tested → kept/reverted → committed).
- Failure-flow diagram for "outer agent breaks an import" (currently untested path).

### Stale diagram audit

Prior review's component graph and research data-flow are still current. No staleness.

---

## Outside Voice (skipped)

Skill recommends a different-model second opinion. Not invoked here. If the team wants this on the harness specifically, run the better-harness loop with `outer_model = "gpt-5"` for one iteration and compare proposal quality vs claude-sonnet-4-6.

---

## Completion Summary

```
+========================================================================+
|   CEO PLAN REVIEW — COMPLETION SUMMARY (better-harness integration)    |
+========================================================================+
| Mode selected         | HOLD SCOPE (ratify Approach Y next)            |
| System Audit          | Tooling-forward branch; pipeline static        |
| Step 0                | Approach Y recommended (close gaps then run)   |
| Section 1  (Arch)     | Prior A1-A6 open + 4 new (A7-A10)              |
| Section 2  (Errors)   | Prior 6 open + 3 new (CLI missing, runs/, signal)|
| Section 3  (Security) | Prior + 3 new (sandboxing, budget cap, pin)    |
| Section 4  (Data/UX)  | Outer-loop edge cases mapped                   |
| Section 5  (Quality)  | Prior Q1-Q8 open + 4 new (Q9-Q12)              |
| Section 6  (Tests)    | 119 tests green; behavioural E2E still missing |
| Section 7  (Perf)     | 0 issues                                       |
| Section 8  (Observ)   | Prior 6 open + 3 new (run output, audit, traces)|
| Section 9  (Deploy)   | Prior 7 open + 3 new (D8-D10)                  |
| Section 10 (Future)   | Prior 8 debt items open + 3 new (L9-L11)        |
| Section 11 (Design)   | SKIPPED (no UI scope)                          |
+------------------------------------------------------------------------+
| NOT in scope          | Prior list + 3 new                             |
| Critical gaps total   | 8 open (5 prior + 3 new)                       |
| TODOs proposed        | Prior 20 + 13 new = 33                         |
| Scope proposals       | 0 (HOLD SCOPE)                                 |
| CEO plan persisted    | this file                                      |
| Outside voice         | skipped                                        |
| Diagrams produced     | 1 (outer optimisation loop)                    |
| Stale diagrams found  | 0                                              |
| Unresolved decisions  | 1 (see below)                                  |
+========================================================================+
```

### Unresolved decisions (require user input)

1. **What's the next branch: Approach Y, Approach Z, or run the harness loop now (Approach X)?**

   This review recommends **Approach Y** (close the 8 critical gaps first, then run the harness for the first time as a 1-iteration baseline; only then commit budget for a real optimisation run). Approach X is dangerous because it amplifies un-paid-down debt; Approach Z is reasonable if the team prefers user value before optimisation infrastructure but defers the hardening work that makes the harness signal honest.

   The team should also decide whether to **pivot the harness's first real run to a sandboxed worktree** (see S5) so an outer-agent prompt-injection cannot reach `master` or this branch.

---

## Verdict

**The better-harness scaffold is a thoughtful, well-structured investment** — train/holdout/scorecard taxonomy is correct, the JSON reporter is documented, the surface declarations are sensible. The new test surface is healthy (51 new tests, all green; combined 119 green). But the scaffold has **two sharp implementation gaps** (missing `better-harness` CLI dependency, `runs/` not gitignored) that block the stated capability from working out-of-box, and **one structural gap** (eval suites bypass the LLM) that means the optimisation loop will, today, only optimise non-prompt surfaces.

**The prior review's 5 critical gaps remain open.** Two consecutive non-pipeline-forward branches is a pattern. The team should consciously decide whether the next branch is "harness ready, gaps closed, first real run" (Approach Y), "ship v0.1 of the manifest-generator" (Approach Z), or "open the assets milestone" (Approach A from prior review). Continuing to add scaffolding without paying down scar tissue is the failure mode to avoid.

**Engineering preference compliance:** DRY violations include three duplicated `_invoke` helpers and two duplicated `_VALID_*` constants — flagged. Test ambition is up structurally but flat behaviourally — the harness exists to optimise prompts but no eval exercises the LLM. Observability around the outer optimisation loop is unspecified — document the run-output structure and the rollback mechanism. Security around the outer agent's edit access is non-trivial; recommend sandboxing in a worktree.

**Recommended next steps in priority order:**

1. **N1 + N2 (P0).** Add `better-harness` to dependencies (pinned SHA); add `runs/` to .gitignore. Half a day with CC.
2. Close prior critical gaps 1–5 (~1–2 days with CC).
3. **N3 + N12 + N8 (P1).** Smoke-import eval; one stub-LLM behavioural eval; CI gate for evals. ~1 day with CC.
4. Run `pnpm harness:run` (the 1-iteration baseline) and confirm a clean green baseline.
5. Then either commit budget for a real `--max-iterations 10` run (Approach Y completion) or pivot to v0.1 ship (Approach Z) or open the assets milestone (Approach A).

— end of review —
