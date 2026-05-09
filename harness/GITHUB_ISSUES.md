# GitHub Issues to Create for Better-Harness Integration

Copy these issue templates to create tracking issues in the GitHub repository.

---

## Issue 1: Install and Validate Better-Harness System

**Title:** Install and validate better-harness system

**Labels:** `enhancement`, `priority:high`

**Body:**
```markdown
## Description

Install the better-harness autonomous optimization system from the deepagents repo and validate that the minimal configuration works.

## Tasks

- [ ] Clone deepagents repo: `git clone https://github.com/langchain-ai/deepagents.git`
- [ ] Install better-harness: `cd deepagents/examples/better-harness && uv sync && uv pip install -e .`
- [ ] Run validation: `pnpm harness:validate`
- [ ] Run baseline test: `pnpm harness:run` (or with `--max-iterations 1` for quick test)
- [ ] Document any required environment variables (ANTHROPIC_API_KEY, etc.)
- [ ] Update harness/README.md with detailed setup instructions

## Success Criteria

- Config validates without errors
- Baseline run completes successfully
- All 5 eval cases (3 train + 2 holdout) run and report results
- Report is generated in runs/ directory with baseline performance metrics

## References

- Better-harness README: https://github.com/langchain-ai/deepagents/tree/main/examples/better-harness
- Blog post: https://blog.langchain.com/improving-deep-agents-with-harness-engineering/
- Our config: `harness/video-maker-minimal.toml`
- Our evals: `tests/evals/`
```

---

## Issue 2: Expand Harness Optimization Surfaces

**Title:** Expand harness surfaces beyond scriptwriter prompt

**Labels:** `enhancement`, `priority:medium`

**Body:**
```markdown
## Description

Add additional optimization surfaces beyond the scriptwriter prompt to improve overall agent performance.

## Proposed Surfaces (in priority order)

1. **Producer prompt** - `skills/video-maker/SKILL.md`
   - Main orchestrator logic
   - High impact on overall behavior

2. **Researcher prompt** - `skills/video-maker/agents/researcher.md`
   - Research quality impacts script quality
   - Medium priority

3. **LangChain tools** - `src/deepagents_video_maker/langchain_tools.py`
   - Tool definitions and error messages
   - Medium priority

4. **Agent factory** - `src/deepagents_video_maker/agent.py`
   - Agent construction and wiring
   - Lower priority (riskier changes)

## Approach

- Add surfaces incrementally, one at a time
- Run optimization loop after each addition
- Measure impact on train/holdout pass rates
- Document which surfaces provide most improvement

## Tasks

- [ ] Add Producer prompt surface to config
- [ ] Run optimization and measure impact
- [ ] Add Researcher prompt surface
- [ ] Add LangChain tools surface
- [ ] Compare multi-surface vs single-surface results

## Dependencies

- Requires Issue #1 (install better-harness) to be completed first
```

---

## Issue 3: Expand Eval Test Coverage

**Title:** Add more eval cases for comprehensive testing

**Labels:** `testing`, `priority:medium`

**Body:**
```markdown
## Description

Expand eval coverage to test more aspects of the video-maker pipeline beyond basic scriptwriter functionality.

## New Test Categories

### Research Milestone
- [ ] Web search integration test
- [ ] Local file parsing test
- [ ] Research report quality and structure

### Tool Selection & Usage
- [ ] Correct tool chosen for given task
- [ ] Tool parameters properly extracted from context
- [ ] Error handling when tools fail

### Multi-Milestone Integration
- [ ] Full research → script pipeline
- [ ] State persistence across milestones
- [ ] Ratify gates working correctly

### Edge Cases
- [ ] Very short duration (30s-1min)
- [ ] Long duration (10min+)
- [ ] Different aspect ratios (1:1, 9:16, etc.)
- [ ] Multiple content styles (professional, casual, storytelling)

## Target Coverage

- 10-15 train cases (currently 3)
- 5-8 holdout cases (currently 2)
- 3-5 scorecard cases (currently 0)

## Implementation

Create new test files in `tests/evals/`:
- `test_research_train.py`
- `test_research_holdout.py`
- `test_integration_train.py`
- `test_scorecard.py`

Update `harness/video-maker-minimal.toml` with new case IDs.
```

---

## Issue 4: Migrate to Harbor Runner for Richer Scoring

**Title:** Integrate Harbor runner for multi-dimensional evaluation

**Labels:** `enhancement`, `priority:low`

**Body:**
```markdown
## Description

Migrate from pytest binary pass/fail to Harbor's richer scoring system for better optimization feedback.

## Benefits

- Numeric scoring (0-100) vs binary pass/fail
- Multi-dimensional evaluation (accuracy, creativity, structure, coherence)
- LLM-as-judge for narrative quality assessment
- Better tracking of incremental improvements
- More nuanced optimization signals for outer agent

## Tasks

- [ ] Install Harbor evaluation framework
- [ ] Convert existing pytest cases to Harbor task format
- [ ] Define scoring rubrics for each eval dimension:
  - Script structure correctness (0-100)
  - Narrative coherence (0-100)
  - Scene pacing appropriateness (0-100)
  - Ratify compliance (0-100)
- [ ] Update harness config for Harbor runner
- [ ] Run comparison: pytest vs Harbor results
- [ ] Document Harbor setup in README

## Example Scoring Rubric

```yaml
# Script quality scoring
structure_score:
  - Valid YAML front matter: 20 points
  - All scenes have required fields: 30 points
  - Scene count appropriate for duration: 20 points
  - Audio design section present: 10 points
  - Glossary provided: 10 points
  - Bonus: scene variety: +10 points
```

## References

- Harbor docs (if available in deepagents repo)
- `harness/video-maker-minimal.toml` - runner.harbor section
```

---

## Issue 5: CI/CD Integration for Continuous Optimization

**Title:** Integrate better-harness into CI/CD pipeline

**Labels:** `devops`, `priority:low`

**Body:**
```markdown
## Description

Integrate better-harness into the CI/CD pipeline for continuous monitoring and optimization of agent performance.

## Proposed Workflows

### 1. PR Validation (GitHub Actions)
- Run `pnpm harness:validate` on config changes
- Run baseline tests on code changes affecting agent
- Compare against main branch baseline
- Alert on holdout regressions

### 2. Nightly Optimization
- Run full optimization loop (5-10 iterations)
- Store results as artifacts
- Generate performance report
- Create PR if improvements found

### 3. Weekly Analysis
- Aggregate optimization trends
- Identify surfaces with most impact
- Report on eval pass rate trends
- Recommend config tunings

## Tasks

- [ ] Create `.github/workflows/harness-validate.yml`
- [ ] Create `.github/workflows/harness-optimize-nightly.yml`
- [ ] Set up artifact storage for optimization runs
- [ ] Create reporting dashboard (optional)
- [ ] Document workflow in CLAUDE.md

## Success Criteria

- PRs automatically tested against harness
- No regression in holdout scores
- Automated improvement proposals via PRs
- Performance trends tracked over time
```

---

## How to Use These Templates

1. Go to https://github.com/AILatentspace1/deepagents-video-maker/issues/new
2. Copy the title and body from each issue above
3. Add the suggested labels
4. Create the issue
5. Link related issues together (e.g., Issue #2 depends on Issue #1)

## Recommended Priority Order

1. **Issue #1** (High) - Install and validate - Blocks all other work
2. **Issue #3** (Medium) - Expand tests - Needed for meaningful optimization
3. **Issue #2** (Medium) - Expand surfaces - Main value of better-harness
4. **Issue #4** (Low) - Harbor migration - Nice to have, not critical
5. **Issue #5** (Low) - CI/CD - Automation, low priority initially
