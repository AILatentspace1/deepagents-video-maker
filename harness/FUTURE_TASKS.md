# Future Better-Harness Tasks

## Phase 2: Install and Test Better-Harness

**Priority: High**

### Description
Install the better-harness system from the deepagents repo and validate the minimal configuration works.

### Tasks
- [ ] Clone deepagents repo and install better-harness
- [ ] Run `pnpm harness:validate` to validate config
- [ ] Run baseline test with `--max-iterations 1`
- [ ] Document any issues or required env variables
- [ ] Add installation instructions to harness/README.md

### Success Criteria
- Config validates without errors
- Baseline run completes successfully
- All 5 eval cases run and report results

---

## Phase 3: Expand Harness Surfaces

**Priority: Medium**

### Description
Add more optimization surfaces beyond just the scriptwriter prompt.

### Additional Surfaces to Add
1. **Producer prompt** (`skills/video-maker/SKILL.md`)
   - Main orchestrator logic
   - High impact on overall agent behavior

2. **Researcher prompt** (`skills/video-maker/agents/researcher.md`)
   - Research quality impacts script quality
   - Medium priority

3. **LangChain tools** (`src/deepagents_video_maker/langchain_tools.py`)
   - Tool definitions and error messages
   - Medium priority

4. **Agent factory** (`src/deepagents_video_maker/agent.py`)
   - Agent construction and wiring
   - Low priority (risky changes)

### Approach
- Add one surface at a time
- Run optimization loop after each addition
- Measure impact on pass rates

---

## Phase 4: Add More Eval Cases

**Priority: Medium**

### Description
Expand eval coverage to test more aspects of the video-maker pipeline.

### New Test Categories

**Research Milestone**
- [ ] Web search integration test
- [ ] Local file parsing test
- [ ] Research report quality test

**Tool Selection**
- [ ] Correct tool chosen for task
- [ ] Tool parameters properly extracted

**Error Handling**
- [ ] Graceful handling of missing files
- [ ] Retry logic on failures

**Multi-Milestone Integration**
- [ ] Full research → script pipeline
- [ ] State persistence across milestones

### Target
- 10-15 train cases
- 5-8 holdout cases
- 3-5 scorecard cases

---

## Phase 5: Harbor Runner Integration

**Priority: Low**

### Description
Migrate from pytest to Harbor for richer evaluation scoring.

### Benefits
- Numeric scoring (0-100) vs binary pass/fail
- Multi-dimensional evaluation (accuracy, creativity, structure)
- LLM-as-judge for narrative quality
- Better tracking of incremental improvements

### Tasks
- [ ] Install Harbor evaluation framework
- [ ] Convert existing pytest cases to Harbor tasks
- [ ] Define scoring rubrics for each eval
- [ ] Update harness config for Harbor runner
- [ ] Compare results with pytest baseline

---

## Phase 6: Optimization Analysis and Tuning

**Priority: Medium**

### Description
Analyze optimization results and tune the better-harness configuration.

### Analysis Tasks
- [ ] Review baseline vs final performance
- [ ] Analyze which surfaces have most impact
- [ ] Identify eval cases causing most optimization
- [ ] Check for overfitting on train set
- [ ] Measure holdout regression

### Tuning Parameters
- `max_iterations`: Current 5, may need 10-15
- `better_agent_max_turns`: Current 30, may need adjustment
- Better agent model: Try different models for outer agent
- Surface selection: Enable/disable surfaces based on impact

---

## Phase 7: CI/CD Integration

**Priority: Low**

### Description
Integrate better-harness into CI pipeline.

### Tasks
- [ ] Add GitHub Actions workflow for harness validation
- [ ] Run baseline tests on each PR
- [ ] Store optimization results as artifacts
- [ ] Compare PR changes against baseline
- [ ] Alert on regression in holdout scores

### Automation
- Nightly optimization runs
- Weekly reports on improvement trends
- Automatic PR creation for accepted improvements

---

## Phase 8: Custom Better-Agent System Prompt

**Priority: Low**

### Description
Customize the outer agent's system prompt for video-maker domain expertise.

### Customizations
- Add context about video production terminology
- Provide examples of good script structures
- Include ratify rules as constraints
- Add domain knowledge about scene types and pacing

### Tasks
- [ ] Create custom system prompt file
- [ ] Reference in harness config: `better_agent.system_prompt_file`
- [ ] Test impact on proposal quality
- [ ] Iterate based on results

---

## Open Questions

1. **Model Selection**
   - Should outer agent use same model as inner agent?
   - Would a cheaper/faster model (Haiku) work for outer loop?

2. **Eval Infrastructure**
   - Stay with pytest or migrate to Harbor?
   - Add LangSmith tracing integration?

3. **Surface Prioritization**
   - Start with all surfaces or add incrementally?
   - Which surfaces have highest ROI?

4. **Optimization Strategy**
   - How many iterations needed for convergence?
   - Should we run optimization weekly/monthly?
