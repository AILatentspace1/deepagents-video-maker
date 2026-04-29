"""Stress test eval cases for scriptwriter prompt optimization.

Edge cases that probe structural robustness:
  - ultra_short: 30s video forces extreme density discipline
  - zh_en_mix: Chinese topic + English research requires locale-agnostic prompt adherence
  - pure_narrative: image_none research must produce zero data_card scenes

Train strata:
  - ultra_short   → duration (train)
  - pure_narrative → content_type (train)
Holdout:
  - zh_en_mix     → locale (holdout)
"""

from __future__ import annotations

import re
import pytest
from pathlib import Path

from deepagents_video_maker.models import MilestoneStatus, VideoMakerGoal
from deepagents_video_maker.params import derive_video_params
from deepagents_video_maker.script_flow import start_script_milestone
from deepagents_video_maker.session import init_video_session

from .conftest import invoke_scriptwriter


# ---------------------------------------------------------------------------
# Shared research fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def ultra_short_research():
    """Minimal research for a 30-second explainer — only 3 facts, no sub-sections."""
    return """# Research Report: What Is an AI Agent?

## 1. Executive Summary
An AI agent is a software system that perceives its environment, plans, and acts autonomously
to complete goals — without a human clicking every button.

## 2. Data Points
- Agents outperform single-shot prompts on complex tasks: 74% success rate vs 31%
- Adoption doubled in 12 months: 42% of enterprises now have at least one agent in production
- Average time-to-task: 3.2 minutes for agents vs 47 minutes manually

## 3. Visual Strategy
visual_strategy: image_none
Keep it clean — no background images needed for a 30-second explainer.

## 4. Key Findings
Agents = LLM + memory + tool use. They plan, act, observe, repeat.

## 5. Technical Details
Core loop: Perceive → Plan → Act → Observe → Repeat.

## 6. Style Spine
lut_style: tech_cool
tone: punchy, direct
style_template: tech-noir

## 7. Narrative Flow
Hook (what is it?) → One key fact → CTA (learn more)

## 8. Additional Data
No additional data needed for 30s format.

## 9. Quotes
"Agents are just LLMs that can take actions." - Andrej Karpathy
"""


@pytest.fixture
def zh_topic_research():
    """English research content but the goal topic is in Chinese."""
    return """# Research Report: AI Agent Evolution 2025

## 1. Executive Summary
AI Agents are transforming enterprise workflows. Investment and adoption have surged.

## 2. Data Points
- Global AI Agent investment: $150B in 2024 (+300% YoY)
- Enterprise adoption: 67% of Fortune 500 companies have deployed agents
- Task completion rate: 85% for complex multi-step workflows

## 3. Visual Strategy
visual_strategy: image_light
Recommend images for: hook scene, climax scene showing agent network

## 4. Key Findings
Modern agents combine planning, tool use, and self-correction.
Sub-agent orchestration enables parallel workstreams.

## 5. Technical Architecture
LLM + Memory + Planning + Tool Execution + Self-Correction loop.

## 6. Style Spine
lut_style: tech_cool
tone: professional, confident
style_template: tech-noir

## 7. Narrative Flow
Hook → Investment wave → Architecture → Impact → CTA

## 8. Additional Data
- Productivity gain: 40% for knowledge workers
- Error rate reduction: 60% vs manual

## 9. Quotes
"The agent era is rewriting the rules of software." - CEO, Anthropic
"""


@pytest.fixture
def pure_narrative_research():
    """Research with visual_strategy: image_none and zero quantitative data points.

    The scriptwriter must produce ONLY narration/title_card/transition/quote_card scenes —
    absolutely no data_card scenes when the research has nothing to visualize.
    """
    return """# Research Report: The Philosophy of Deep Work

## 1. Executive Summary
Deep work — the ability to focus without distraction on cognitively demanding tasks —
is becoming both increasingly rare and increasingly valuable.

## 2. Data Points
No quantitative data is available. This is a conceptual/philosophical topic.

## 3. Visual Strategy
visual_strategy: image_none
This is a purely narrative topic. All scenes should use primitives only.
Do NOT create any data_card scenes — there are no numbers to visualize.

## 4. Key Findings
Cal Newport defines deep work as "professional activities performed in a state of
distraction-free concentration that push cognitive capabilities to their limit."
The ability to produce deep work is rare because constant connectivity fragments attention.

## 5. Conceptual Framework
Shallow work (email, meetings, social media) is easy to replicate; deep work is hard.
Deep work produces rare, valuable output in less time.

## 6. Style Spine
lut_style: warm_human
tone: reflective, calm
style_template: docu-natural

## 7. Narrative Flow
Hook (attention crisis) → What is deep work → Why it matters → How to practice → CTA

## 8. Additional Data
No additional quantitative data. Rely purely on conceptual narrative.

## 9. Quotes
"Deep work is the superpower of the 21st century." - Cal Newport
"The ability to concentrate is disappearing at exactly the moment it becomes most valuable." - Cal Newport
"""


# ---------------------------------------------------------------------------
# Stress case 1 — ultra-short 30s video (train: duration)
# ---------------------------------------------------------------------------

def test_llm_scriptwriter_ultra_short(tmp_path, llm_client, model, ultra_short_research):
    """Stress case: 30-second explainer video must be extremely compact.

    A weaker model or inadequately prompted scriptwriter will produce a full 1-3min
    script anyway, ignoring the 30s constraint.

    Success criteria:
    - Scene count: 3–6
    - Sum of duration_estimate values: 20–40 seconds
    - No single scene duration > 8 seconds
    - Has a hook scene and a cta scene
    """
    goal = VideoMakerGoal(
        topic="What Is an AI Agent?",
        source="local-file",
        local_file="research.md",
    )
    goal.duration = "30s"
    goal.style = "professional"
    goal.aspect_ratio = "9:16"
    goal = derive_video_params(goal)

    state = init_video_session(goal, tmp_path, timestamp="20260429-stress01")

    research_milestone = state.milestone("research")
    research_milestone.status = MilestoneStatus.COMPLETED
    research_milestone.current_run = 1

    research_dir = Path(state.output_dir) / "artifacts" / "research" / "run-1"
    research_dir.mkdir(parents=True, exist_ok=True)
    (research_dir / "research.md").write_text(ultra_short_research, encoding="utf-8")

    run = start_script_milestone(state)
    run_dir = Path(run.run_dir)

    ok, err = invoke_scriptwriter(llm_client, goal, ultra_short_research, run_dir)
    assert ok, f"invoke_scriptwriter failed: {err}"

    script_text = (run_dir / "script.md").read_text(encoding="utf-8")

    scene_blocks = re.findall(
        r"(?ms)^##\s+Scene\b.*?(?=^##\s+Scene\b|^##\s+Audio\b|\Z)", script_text
    )
    scene_count = len(scene_blocks)
    durations = [int(d) for d in re.findall(r"duration_estimate:\s*(\d+)", script_text)]
    total_duration = sum(durations)

    assert 3 <= scene_count <= 6, (
        f"30s video must have 3–6 scenes (compact!). Got {scene_count}. "
        f"If you see 10+ scenes, the prompt is ignoring the duration constraint."
    )
    assert 20 <= total_duration <= 40, (
        f"30s video: total duration_estimate must be 20–40s. "
        f"Got {total_duration}s from {len(durations)} scenes."
    )
    oversized = [d for d in durations if d > 8]
    assert not oversized, (
        f"No single scene may exceed 8s in a 30s video. Found: {oversized}"
    )

    # Must still have hook and cta structure
    roles = re.findall(r"narrative_role:\s*(\w+)", script_text)
    role_set = set(roles)
    assert "hook" in role_set, f"30s video must still open with a hook. Roles found: {roles}"
    assert "cta" in role_set, f"30s video must still close with a cta. Roles found: {roles}"


# ---------------------------------------------------------------------------
# Stress case 2 — pure narrative, image_none (train: content_type)
# ---------------------------------------------------------------------------

def test_llm_scriptwriter_pure_narrative(tmp_path, llm_client, model, pure_narrative_research):
    """Stress case: research with image_none and no quantitative data must yield zero data_card scenes.

    A weaker model or over-templated prompt will hallucinate data_card scenes even when
    the research explicitly says there is no data.

    Success criteria:
    - ZERO data_card type scenes
    - ZERO data_semantic blocks anywhere in script
    - At least 4 narration scenes (story must be told through narration)
    - At least one quote_card scene (research has quotes)
    - style_spine.lut_style = warm_human (from research §6)
    """
    goal = VideoMakerGoal(
        topic="The Philosophy of Deep Work",
        source="local-file",
        local_file="research.md",
    )
    goal.duration = "1-3min"
    goal.style = "storytelling"
    goal.aspect_ratio = "16:9"
    goal = derive_video_params(goal)

    state = init_video_session(goal, tmp_path, timestamp="20260429-stress02")

    research_milestone = state.milestone("research")
    research_milestone.status = MilestoneStatus.COMPLETED
    research_milestone.current_run = 1

    research_dir = Path(state.output_dir) / "artifacts" / "research" / "run-1"
    research_dir.mkdir(parents=True, exist_ok=True)
    (research_dir / "research.md").write_text(pure_narrative_research, encoding="utf-8")

    run = start_script_milestone(state)
    run_dir = Path(run.run_dir)

    ok, err = invoke_scriptwriter(llm_client, goal, pure_narrative_research, run_dir)
    assert ok, f"invoke_scriptwriter failed: {err}"

    script_text = (run_dir / "script.md").read_text(encoding="utf-8")

    scene_blocks = re.findall(
        r"(?ms)^##\s+Scene\b.*?(?=^##\s+Scene\b|^##\s+Audio\b|\Z)", script_text
    )

    # Must have ZERO data_card scenes
    data_card_blocks = [b for b in scene_blocks if re.search(r"type:\s*data_card", b)]
    assert len(data_card_blocks) == 0, (
        f"Pure-narrative research (image_none, no data) must produce ZERO data_card scenes. "
        f"Got {len(data_card_blocks)}. The scriptwriter must respect visual_strategy: image_none "
        f"and the absence of quantitative data.\n\nOffending blocks:\n"
        + "\n---\n".join(b[:300] for b in data_card_blocks)
    )

    # Must have ZERO data_semantic blocks
    data_semantic_count = len(re.findall(r"data_semantic:", script_text))
    assert data_semantic_count == 0, (
        f"data_semantic blocks must not appear when there is no quantitative data. "
        f"Found {data_semantic_count} occurrences."
    )

    # Must have substantial narration content
    narration_blocks = [b for b in scene_blocks if re.search(r"type:\s*narration", b)]
    assert len(narration_blocks) >= 4, (
        f"Pure-narrative script must have ≥4 narration scenes to carry the story. "
        f"Got {len(narration_blocks)}."
    )

    # Must include at least one quote_card (research has 2 quotes)
    quote_card_blocks = [b for b in scene_blocks if re.search(r"type:\s*quote_card", b)]
    assert len(quote_card_blocks) >= 1, (
        f"Research provides 2 Cal Newport quotes — at least one quote_card scene expected. "
        f"Got 0."
    )

    # lut_style must match research §6 (warm_human for philosophical/storytelling topic)
    spine_match = re.search(r"```style_spine\n(.*?)```", script_text, re.DOTALL)
    assert spine_match, "script.md must have a ```style_spine block"
    spine = spine_match.group(1)
    lut_match = re.search(r"lut_style:\s*(\S+)", spine)
    assert lut_match, "style_spine must contain lut_style"
    lut_value = lut_match.group(1).rstrip(",").strip()
    assert lut_value == "warm_human", (
        f"lut_style must be 'warm_human' (research §6 says so for storytelling topics). "
        f"Got: '{lut_value}'"
    )


# ---------------------------------------------------------------------------
# Stress case 3 — Chinese topic + English research (holdout: locale)
# ---------------------------------------------------------------------------

def test_llm_scriptwriter_zh_en_mix(tmp_path, llm_client, model, zh_topic_research):
    """Holdout stress case: Chinese topic title with English research content.

    Tests that the scriptwriter prompt doesn't break on mixed-locale input.
    The script structure and style_spine format must be identical to a pure-English run.

    Success criteria:
    - style_spine block is present and complete (all 7 required fields)
    - lut_style = tech_cool (from research §6)
    - Scene count ≥ 8 (1-3min content still requires substantial script)
    - At least one data_card scene (research has 3 data points)
    - All ## Scene headings use the English format "## Scene N:" (not Chinese 场景)
    - narration text is present and non-empty for narration scenes
    """
    goal = VideoMakerGoal(
        topic="人工智能Agent的崛起与未来",   # Chinese topic title
        source="local-file",
        local_file="research.md",
    )
    goal.duration = "1-3min"
    goal.style = "professional"
    goal.aspect_ratio = "16:9"
    goal = derive_video_params(goal)

    state = init_video_session(goal, tmp_path, timestamp="20260429-stress03")

    research_milestone = state.milestone("research")
    research_milestone.status = MilestoneStatus.COMPLETED
    research_milestone.current_run = 1

    research_dir = Path(state.output_dir) / "artifacts" / "research" / "run-1"
    research_dir.mkdir(parents=True, exist_ok=True)
    (research_dir / "research.md").write_text(zh_topic_research, encoding="utf-8")

    run = start_script_milestone(state)
    run_dir = Path(run.run_dir)

    ok, err = invoke_scriptwriter(llm_client, goal, zh_topic_research, run_dir)
    assert ok, f"invoke_scriptwriter failed: {err}"

    script_text = (run_dir / "script.md").read_text(encoding="utf-8")

    # style_spine must be present and complete
    spine_match = re.search(r"```style_spine\n(.*?)```", script_text, re.DOTALL)
    assert spine_match, "script.md must have a ```style_spine block even for Chinese topics"
    spine = spine_match.group(1)

    required_fields = ["lut_style", "aspect_ratio", "style_template", "visual_strategy", "pacing", "tone", "glossary"]
    missing = [f for f in required_fields if f not in spine]
    assert not missing, (
        f"style_spine missing fields for Chinese-topic script: {missing}\n\nspine:\n{spine}"
    )

    lut_match = re.search(r"lut_style:\s*(\S+)", spine)
    lut_value = lut_match.group(1).rstrip(",").strip() if lut_match else ""
    assert lut_value == "tech_cool", (
        f"lut_style must be 'tech_cool' regardless of topic language. Got: '{lut_value}'"
    )

    # Scene headings must use English format "## Scene N"
    english_scene_headings = re.findall(r"(?m)^##\s+Scene\s+\d+", script_text)
    chinese_scene_headings = re.findall(r"(?m)^##\s+场景\s*\d+", script_text)
    assert len(english_scene_headings) >= 8, (
        f"1-3min video needs ≥8 English-format '## Scene N' headings. "
        f"Got {len(english_scene_headings)} English, {len(chinese_scene_headings)} Chinese. "
        f"The prompt mandates English scene headings regardless of topic language."
    )

    # At least one data_card (research has 3 clear data points)
    scene_blocks = re.findall(
        r"(?ms)^##\s+Scene\b.*?(?=^##\s+Scene\b|^##\s+Audio\b|\Z)", script_text
    )
    data_card_blocks = [b for b in scene_blocks if re.search(r"type:\s*data_card", b)]
    assert len(data_card_blocks) >= 1, (
        f"Research has 3 strong data points — at least 1 data_card scene expected. "
        f"Got 0 out of {len(scene_blocks)} total scenes."
    )

    # Narration scenes must have non-empty narration text
    narration_blocks = [b for b in scene_blocks if re.search(r"type:\s*narration", b)]
    for i, block in enumerate(narration_blocks):
        narr_match = re.search(r"narration:\s*\|?\s*\n((?:[ \t]+.+\n?)+)", block)
        if narr_match:
            text = narr_match.group(1).strip()
            assert len(text) >= 10, (
                f"narration scene {i+1} has near-empty narration text: '{text}'"
            )
