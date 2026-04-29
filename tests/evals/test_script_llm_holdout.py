"""LLM-based holdout eval cases for scriptwriter prompt optimization.

These cases test domain transfer and edge-case compliance to prevent
the harness from overfitting the scriptwriter prompt to the train cases.

Holdout strata:
  - structure: data_card quality (domain transfer with data-heavy research)
  - scene_quality: duration compliance (short video, strict scene count)
"""

from __future__ import annotations

import json
import re
import pytest
from pathlib import Path

from deepagents_video_maker.models import MilestoneStatus, VideoMakerGoal
from deepagents_video_maker.params import derive_video_params
from deepagents_video_maker.script_flow import start_script_milestone
from deepagents_video_maker.session import init_video_session

from .conftest import invoke_scriptwriter


# ---------------------------------------------------------------------------
# Holdout case 1 — structure: data_card scenes have data_semantic
# ---------------------------------------------------------------------------

@pytest.fixture
def data_heavy_research():
    """Research with multiple quantitative data points (different domain: climate tech)."""
    return """# Research Report: Climate Tech Investment 2025

## 1. Executive Summary
Climate technology has attracted record investment as the urgency of climate action intensifies.
Solar, wind, battery storage, and carbon capture are the top four sectors.

## 2. Data Points
- Total climate tech investment 2024: $1.2 trillion
- Solar energy capacity growth: +180 GW in 2024
- Battery storage cost: $78/kWh (down 89% since 2010)
- Carbon capture projects: 43 operational globally
- EV adoption: 18% of new car sales globally
- Green hydrogen cost: $4.2/kg (target: $1/kg by 2030)

## 3. Visual Strategy
visual_strategy: image_light
Recommend images for: hook scene (solar farm aerial), climax (battery storage facility)

## 4. Key Findings
Investment reached a new high driven by government subsidies and corporate net-zero pledges.
Battery storage is the fastest-falling cost technology ever recorded.

## 5. Technical Landscape
Solar: utility-scale dominates; Battery: lithium-ion + solid-state emerging;
Carbon capture: direct air capture (DAC) scaling up; Green hydrogen: electrolysis cost decline.

## 6. Style Spine
lut_style: pastel_dream
tone: optimistic, authoritative
style_template: docu-natural

## 7. Narrative Flow
Hook (crisis → opportunity) → Investment wave ($1.2T) → Technology breakdown (4 sectors)
→ Cost curves (batteries, hydrogen) → Outlook → CTA

## 8. Additional Data
- Levelized cost of solar: $0.028/kWh (cheapest electricity ever)
- Job creation: 12 million climate tech jobs added in 2024
- Countries at 100% renewable: 13 (up from 5 in 2020)

## 9. Quotes
"We've crossed the economic tipping point. Clean energy is now the cheapest option." - IEA Director
"Battery cost decline has been the biggest surprise of the energy transition." - BloombergNEF
"""


def test_llm_scriptwriter_data_card_quality(tmp_path, llm_client, model, data_heavy_research):
    """Holdout case 1: data-heavy research should produce data_card scenes with data_semantic.

    Success criteria:
    - At least 2 data_card type scenes exist
    - Each data_card scene has a data_semantic block with:
        * claim field
        * anchor_number field
        * items array with ≥2 items
    """
    goal = VideoMakerGoal(
        topic="Climate Tech Investment 2025",
        source="local-file",
        local_file="research.md",
    )
    goal.duration = "3-5min"
    goal.style = "professional"
    goal.aspect_ratio = "16:9"
    goal = derive_video_params(goal)

    state = init_video_session(goal, tmp_path, timestamp="20260429-hold01")

    research_milestone = state.milestone("research")
    research_milestone.status = MilestoneStatus.COMPLETED
    research_milestone.current_run = 1

    research_dir = Path(state.output_dir) / "artifacts" / "research" / "run-1"
    research_dir.mkdir(parents=True, exist_ok=True)
    (research_dir / "research.md").write_text(data_heavy_research, encoding="utf-8")

    run = start_script_milestone(state)
    run_dir = Path(run.run_dir)

    ok, err = invoke_scriptwriter(llm_client, goal, data_heavy_research, run_dir)
    assert ok, f"invoke_scriptwriter failed: {err}"

    script_text = (run_dir / "script.md").read_text(encoding="utf-8")

    # Find all data_card scenes
    scene_blocks = re.findall(r"(?ms)^##\s+Scene\b.*?(?=^##\s+Scene\b|^##\s+Audio\b|\Z)", script_text)
    data_card_blocks = [b for b in scene_blocks if re.search(r"type:\s*data_card", b)]

    assert len(data_card_blocks) >= 2, (
        f"Data-heavy research should produce ≥2 data_card scenes. "
        f"Found {len(data_card_blocks)} out of {len(scene_blocks)} total scenes."
    )

    # Each data_card should have data_semantic with claim, anchor_number, items
    for i, block in enumerate(data_card_blocks):
        assert "data_semantic:" in block, (
            f"data_card scene {i+1} is missing data_semantic block:\n{block[:400]}"
        )
        assert "claim:" in block, (
            f"data_card scene {i+1} data_semantic missing 'claim' field:\n{block[:400]}"
        )
        assert "anchor_number:" in block, (
            f"data_card scene {i+1} data_semantic missing 'anchor_number' field:\n{block[:400]}"
        )
        items = re.findall(r"- \{.*?label.*?\}", block)
        assert len(items) >= 3, (
            f"data_card scene {i+1} data_semantic.items should have ≥3 entries "
            f"(climate tech research has 6+ data points — use them!). "
            f"Found {len(items)}:\n{block[:400]}"
        )


# ---------------------------------------------------------------------------
# Holdout case 2 — scene_quality: duration compliance for short video
# ---------------------------------------------------------------------------

@pytest.fixture
def short_research():
    """Compact research for a 1-3min casual video (different domain: productivity tips)."""
    return """# Research Report: Top 3 Productivity Hacks with AI

## 1. Executive Summary
Three simple AI tools can save knowledge workers 2+ hours per day.

## 2. Data Points
- Average time saved with AI writing tools: 45 min/day
- Meeting time reduction with AI summaries: 30 min/day
- Email triage time saved: 20 min/day
- Total: 95 min/day savings for average user

## 3. Visual Strategy
visual_strategy: image_none
Simple clean visuals work best for productivity tips content.

## 4. Key Findings
1. AI writing assistants cut drafting time by 60%
2. AI meeting summaries eliminate manual note-taking
3. AI email triage prioritizes inbox automatically

## 5. Tools Covered
Writing: ChatGPT / Claude. Meetings: Otter.ai / Fireflies. Email: SaneBox / Superhuman.

## 6. Style Spine
lut_style: pastel_dream
tone: casual, friendly

## 7. Narrative Flow
Hook (time problem) → Hack 1 (writing) → Hack 2 (meetings) → Hack 3 (email) → CTA

## 8. Additional Data
- ROI: $180/hour worker saves 95 min = $285/day value
- Setup time: under 30 minutes for all three tools

## 9. Quotes
"I got back 2 hours a day just by changing how I use AI." - Productivity Coach, Maria Lopez
"""


def test_llm_scriptwriter_duration_compliance(tmp_path, llm_client, model, short_research):
    """Holdout case 2: short 1-3min video must have scene count and duration in range.

    Success criteria:
    - Scene count: 6–16 (spec for 1-3min)
    - Sum of duration_estimate values: 60–180 seconds
    - No single scene duration > 20 seconds
    """
    goal = VideoMakerGoal(
        topic="Top 3 Productivity Hacks with AI",
        source="local-file",
        local_file="research.md",
    )
    goal.duration = "1-3min"
    goal.style = "casual"
    goal.aspect_ratio = "9:16"
    goal = derive_video_params(goal)

    state = init_video_session(goal, tmp_path, timestamp="20260429-hold02")

    research_milestone = state.milestone("research")
    research_milestone.status = MilestoneStatus.COMPLETED
    research_milestone.current_run = 1

    research_dir = Path(state.output_dir) / "artifacts" / "research" / "run-1"
    research_dir.mkdir(parents=True, exist_ok=True)
    (research_dir / "research.md").write_text(short_research, encoding="utf-8")

    run = start_script_milestone(state)
    run_dir = Path(run.run_dir)

    ok, err = invoke_scriptwriter(llm_client, goal, short_research, run_dir)
    assert ok, f"invoke_scriptwriter failed: {err}"

    script_text = (run_dir / "script.md").read_text(encoding="utf-8")

    # Extract duration_estimate values
    durations = [int(d) for d in re.findall(r"duration_estimate:\s*(\d+)", script_text)]
    scene_blocks = re.findall(r"(?ms)^##\s+Scene\b.*?(?=^##\s+Scene\b|^##\s+Audio\b|\Z)", script_text)
    scene_count = len(scene_blocks)

    assert 6 <= scene_count <= 16, (
        f"1-3min video should have 6–16 scenes, got {scene_count}"
    )

    total_duration = sum(durations)
    assert 60 <= total_duration <= 180, (
        f"Total duration_estimate should be 60–180s for 1-3min video, got {total_duration}s "
        f"(from {len(durations)} scenes with estimates)"
    )

    oversized = [d for d in durations if d > 20]
    assert not oversized, (
        f"No single scene should exceed 20s. Found scenes with: {oversized}"
    )
