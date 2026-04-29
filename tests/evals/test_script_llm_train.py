"""LLM-based training eval cases for scriptwriter prompt optimization.

These tests actually invoke the LLM with the scriptwriter prompt and evaluate
the quality of the generated script. better-harness will optimize the prompt
by observing which tests fail and proposing edits to scriptwriter.md.

Train strata:
  - structure (x2): ratify pass, style_spine completeness
  - scene_quality (x1): narrative arc (hook → development → cta)
"""

from __future__ import annotations

import json
import re
import pytest
from pathlib import Path

from deepagents_video_maker.models import MilestoneStatus, VideoMakerGoal
from deepagents_video_maker.params import derive_video_params
from deepagents_video_maker.ratify import ratify_script
from deepagents_video_maker.script_flow import start_script_milestone
from deepagents_video_maker.session import init_video_session

from .conftest import invoke_scriptwriter


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tech_research():
    return """# Research Report: AI Agent Evolution 2025

## 1. Executive Summary
AI Agents are transforming how we work. From simple chatbots to fully autonomous systems,
the technology has advanced dramatically in 2024-2025. Investment surged to $150B globally.

## 2. Data Points
- Global AI Agent investment: $150B in 2024 (+300% YoY)
- Market leaders: Google (35%), Microsoft (25%), Amazon (10%), Others (30%)
- Task completion rate: 85% for complex multi-step workflows
- Enterprise adoption: 67% of Fortune 500 companies have deployed agents

## 3. Visual Strategy
visual_strategy: image_light
Recommend images for: hook scene (futuristic AI workspace), climax scene (agent network)

## 4. Key Findings
AI Agents now handle complex multi-step tasks autonomously. They combine planning,
tool use, and self-correction in a continuous loop.

## 5. Technical Architecture
Modern agents: LLM + Memory + Planning + Tool Execution + Self-Correction loop.
Key breakthrough: agents that can spawn sub-agents for parallel workstreams.

## 6. Style Spine
lut_style: tech_cool
tone: professional, confident
style_template: tech-noir

## 7. Narrative Flow
Hook (AI changing work) → Evolution (from chatbot to agent) → Impact ($150B, 67% Fortune 500)
→ Architecture (how it works) → Future (what's next) → CTA (get started)

## 8. Additional Data
- Average productivity gain: 40% for knowledge workers
- Error rate reduction: 60% vs manual processes
- ROI payback period: 8 months average

## 9. Quotes
"AI Agents are not just responding anymore, they're acting autonomously." - Dr. Sarah Chen, MIT AI Lab
"The agent era is here and it's rewriting the rules of software." - CEO, Anthropic
"""


@pytest.fixture
def setup_session(tmp_path, tech_research):
    goal = VideoMakerGoal(
        topic="AI Agent Evolution 2025",
        source="local-file",
        local_file="research.md",
    )
    goal.duration = "1-3min"
    goal.style = "professional"
    goal.aspect_ratio = "16:9"
    goal = derive_video_params(goal)

    state = init_video_session(goal, tmp_path, timestamp="20260429-eval01")

    research_milestone = state.milestone("research")
    research_milestone.status = MilestoneStatus.COMPLETED
    research_milestone.current_run = 1

    research_dir = Path(state.output_dir) / "artifacts" / "research" / "run-1"
    research_dir.mkdir(parents=True, exist_ok=True)
    (research_dir / "research.md").write_text(tech_research, encoding="utf-8")

    return {"goal": goal, "state": state}


# ---------------------------------------------------------------------------
# Train case 1 — structure: ratify pass
# ---------------------------------------------------------------------------

def test_llm_scriptwriter_passes_ratify(setup_session, llm_client, model):
    """LLM-generated script must pass all ratify_script checks.

    Success criteria:
    - script.md and manifest.json are produced
    - script.md has at least one '## Scene' block
    - manifest.json is valid JSON with a non-empty 'scenes' array
    - Each scene has id, narration, duration
    - scene count in script matches manifest
    """
    goal = setup_session["goal"]
    state = setup_session["state"]

    run = start_script_milestone(state)
    run_dir = Path(run.run_dir)

    research_dir = Path(state.output_dir) / "artifacts" / "research" / "run-1"
    research_content = (research_dir / "research.md").read_text(encoding="utf-8")
    ok, err = invoke_scriptwriter(llm_client, goal, research_content, run_dir)
    assert ok, f"invoke_scriptwriter failed: {err}"

    result = ratify_script(run_dir / "script.md", run_dir / "manifest.json")
    assert result.passed, f"ratify_script failed. Issues: {result.issues}"

    # Additional: manifest has scenes with required fields
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    scenes = manifest.get("scenes", [])
    assert len(scenes) > 0, "manifest.scenes must not be empty"
    for scene in scenes:
        assert "id" in scene, f"Scene missing 'id': {scene}"
        assert "narration" in scene, f"Scene missing 'narration': {scene}"
        assert "duration" in scene, f"Scene missing 'duration': {scene}"


# ---------------------------------------------------------------------------
# Train case 2 — scene_quality: narrative arc
# ---------------------------------------------------------------------------

def test_llm_scriptwriter_narrative_arc(setup_session, llm_client, model):
    """LLM-generated script must have a precise hook → climax → cta narrative arc.

    Success criteria:
    - At least one scene with narrative_role: hook
    - At least one scene with narrative_role: climax  (explicitly required)
    - At least one scene with narrative_role: cta
    - ORDER enforced: first hook index < first climax index < first cta-from-end index
    - At least two scenes with narrative_role in {development, setup}
    - cta must appear within the last 3 scenes
    """
    goal = setup_session["goal"]
    state = setup_session["state"]

    run = start_script_milestone(state)
    run_dir = Path(run.run_dir)

    research_dir = Path(state.output_dir) / "artifacts" / "research" / "run-1"
    research_content = (research_dir / "research.md").read_text(encoding="utf-8")
    ok, err = invoke_scriptwriter(llm_client, goal, research_content, run_dir)
    assert ok, f"invoke_scriptwriter failed: {err}"

    script_text = (run_dir / "script.md").read_text(encoding="utf-8")

    # Extract all narrative_role values in document order
    roles = re.findall(r"narrative_role:\s*(\w+)", script_text)
    role_set = set(roles)

    # 1. Required roles
    assert "hook" in role_set, (
        f"Script must have at least one 'hook' scene. Found roles: {sorted(role_set)}"
    )
    assert "climax" in role_set, (
        f"Script must have at least one 'climax' scene (explicitly required, not just development). "
        f"Found roles: {sorted(role_set)}"
    )
    assert "cta" in role_set, (
        f"Script must have at least one 'cta' scene. Found roles: {sorted(role_set)}"
    )

    # 2. ORDER: hook < climax < cta
    hook_idx = next(i for i, r in enumerate(roles) if r == "hook")
    climax_idx = next(i for i, r in enumerate(roles) if r == "climax")
    cta_idx = next(i for i, r in enumerate(reversed(roles)) if r == "cta")
    cta_idx = len(roles) - 1 - cta_idx
    assert hook_idx < climax_idx, (
        f"hook (pos {hook_idx}) must precede climax (pos {climax_idx}) in role sequence: {roles}"
    )
    assert climax_idx < cta_idx, (
        f"climax (pos {climax_idx}) must precede cta (pos {cta_idx}) in role sequence: {roles}"
    )

    # 3. cta must appear within the last 3 roles
    assert cta_idx >= len(roles) - 3, (
        f"cta must be among the last 3 narrative_role entries (got pos {cta_idx} of {len(roles)}). "
        f"Full sequence: {roles}"
    )

    # 4. Middle content: at least 2 development or setup scenes
    dev_count = sum(1 for r in roles if r in {"development", "setup"})
    assert dev_count >= 2, (
        f"Script must have ≥2 development/setup scenes (the body). "
        f"Found {dev_count}. All roles: {roles}"
    )


# ---------------------------------------------------------------------------
# Train case 3 — structure: style_spine completeness
# ---------------------------------------------------------------------------

def test_llm_scriptwriter_style_spine(setup_session, llm_client, model):
    """LLM-generated script must have a complete style_spine block.

    Success criteria:
    - script.md starts with a ```style_spine code block
    - Block contains: lut_style, aspect_ratio, style_template, visual_strategy, pacing, tone, glossary
    - glossary is a non-empty list
    """
    goal = setup_session["goal"]
    state = setup_session["state"]

    run = start_script_milestone(state)
    run_dir = Path(run.run_dir)

    research_dir = Path(state.output_dir) / "artifacts" / "research" / "run-1"
    research_content = (research_dir / "research.md").read_text(encoding="utf-8")
    ok, err = invoke_scriptwriter(llm_client, goal, research_content, run_dir)
    assert ok, f"invoke_scriptwriter failed: {err}"

    script_text = (run_dir / "script.md").read_text(encoding="utf-8")

    # Check style_spine block exists
    spine_match = re.search(r"```style_spine\n(.*?)```", script_text, re.DOTALL)
    assert spine_match, "script.md must begin with a ```style_spine code block"

    spine = spine_match.group(1)
    required_fields = ["lut_style", "aspect_ratio", "style_template", "visual_strategy", "pacing", "tone", "glossary"]
    missing = [f for f in required_fields if f not in spine]
    assert not missing, f"style_spine is missing required fields: {missing}\n\nspine content:\n{spine}"

    # lut_style must match research section 6 recommendation (tech_cool for AI/tech topic)
    lut_match = re.search(r"lut_style:\s*(\S+)", spine)
    assert lut_match, "style_spine must contain lut_style field"
    lut_value = lut_match.group(1).rstrip(",").strip()
    assert lut_value == "tech_cool", (
        f"lut_style must be 'tech_cool' as recommended in research §6 for AI/tech topics. "
        f"Got: '{lut_value}'\n\nspine:\n{spine}"
    )

    # tone must contain both 'professional' and 'confident' (from research §6)
    tone_match = re.search(r"tone:\s*(.+)", spine)
    assert tone_match, "style_spine must contain tone field"
    tone_value = tone_match.group(1).lower()
    assert "professional" in tone_value, (
        f"tone must include 'professional' (research §6 says: 'professional, confident'). "
        f"Got: '{tone_value}'"
    )
    assert "confident" in tone_value, (
        f"tone must include 'confident' (research §6 says: 'professional, confident'). "
        f"Got: '{tone_value}'"
    )

    # glossary must be a non-empty list with ≥3 domain-specific terms
    glossary_match = re.search(r"glossary:\s*\[(.+?)\]", spine)
    assert glossary_match, "style_spine.glossary must be a YAML list like: glossary: [Term1, Term2]"
    glossary_items = [item.strip() for item in glossary_match.group(1).split(",") if item.strip()]
    assert len(glossary_items) >= 3, (
        f"glossary must have ≥3 domain-specific terms to help Whisper ASR. "
        f"Got {len(glossary_items)}: {glossary_items}"
    )
