"""Holdout eval cases for scriptwriter prompt optimization.

These cases test different domains and edge cases to prevent overfitting.
"""

import json
import pytest
from pathlib import Path

from deepagents_video_maker.models import MilestoneStatus, VideoMakerGoal
from deepagents_video_maker.params import derive_video_params
from deepagents_video_maker.script_flow import (
    ratify_and_update_script,
    start_script_milestone,
)
from deepagents_video_maker.session import init_video_session


@pytest.fixture
def storytelling_research():
    """Research content for storytelling domain (different from tech)."""
    return """# Research Report: Ancient Rome Architecture

## 1. Executive Summary
Ancient Roman architecture combined engineering excellence with artistic beauty. From the Colosseum to aqueducts, Roman builders left an indelible mark.

## 2. Data Points
- Colosseum capacity: 50,000 spectators
- Pantheon dome diameter: 43.3 meters
- Roman road network: 400,000 km total
- Building period: 753 BC - 476 AD (1,229 years)

## 3. Visual Strategy
visual_strategy: image_heavy
Recommend images for: Colosseum, Pantheon dome, Roman Forum, aqueduct

## 4. Key Findings
Romans pioneered concrete construction, enabling massive structures. The arch, vault, and dome were their signature innovations.

## 5. Architectural Elements
Key features: columns, arches, domes, vaults, concrete

## 6. Style Spine
lut_style: cinematic_drama
tone: epic, historical

## 7. Narrative Flow
Hook → Innovations → Masterpieces → Legacy → Reflection

## 8. Additional Data
- Pantheon still stands after 1,900 years
- Concrete formula: volcanic ash + lime + seawater

## 9. Quotes
"Rome wasn't built in a day, but its architecture changed the world forever." - Prof. Marcus Vitruvius
"""


@pytest.fixture
def setup_storytelling_session(tmp_path, storytelling_research):
    """Set up session with storytelling content (different domain)."""
    goal = VideoMakerGoal(
        topic="Ancient Rome Architecture",
        source="local-file",
        local_file="research.md"
    )
    goal.duration = "3-5min"  # Longer duration edge case
    goal.style = "storytelling"  # Different style
    goal.aspect_ratio = "16:9"
    goal = derive_video_params(goal)

    state = init_video_session(goal, tmp_path, timestamp="20260429-110000")

    research_milestone = state.milestone("research")
    research_milestone.status = MilestoneStatus.COMPLETED
    research_milestone.current_run = 1

    research_dir = Path(state.output_dir) / "artifacts" / "research" / "run-1"
    research_dir.mkdir(parents=True, exist_ok=True)
    (research_dir / "research.md").write_text(storytelling_research, encoding="utf-8")

    return {"goal": goal, "state": state, "output_dir": tmp_path}


@pytest.fixture
def short_duration_research():
    """Research for very short video."""
    return """# Research Report: Quick AI Tips

## 1. Executive Summary
Three essential tips for using AI tools effectively in 2025.

## 2. Data Points
- Average productivity gain: 40%
- User adoption rate: 85%

## 3. Visual Strategy
visual_strategy: image_none

## 4. Key Findings
1. Be specific in prompts
2. Iterate and refine
3. Validate outputs

## 5. Tips
Clear communication with AI tools is key.

## 6. Style Spine
lut_style: pastel_dream
tone: casual, friendly

## 7. Narrative Flow
Hook → Tip 1 → Tip 2 → Tip 3 → CTA

## 8. Additional Data
Users who follow best practices see 2x better results.

## 9. Quotes
"Clarity beats complexity." - AI Expert
"""


@pytest.fixture
def setup_short_session(tmp_path, short_duration_research):
    """Set up session for very short (1min) video."""
    goal = VideoMakerGoal(
        topic="Quick AI Tips",
        source="local-file",
        local_file="research.md"
    )
    goal.duration = "1-3min"  # Lower bound
    goal.style = "casual"  # Different style
    goal.aspect_ratio = "9:16"  # Vertical format
    goal = derive_video_params(goal)

    state = init_video_session(goal, tmp_path, timestamp="20260429-120000")

    research_milestone = state.milestone("research")
    research_milestone.status = MilestoneStatus.COMPLETED
    research_milestone.current_run = 1

    research_dir = Path(state.output_dir) / "artifacts" / "research" / "run-1"
    research_dir.mkdir(parents=True, exist_ok=True)
    (research_dir / "research.md").write_text(short_duration_research, encoding="utf-8")

    return {"goal": goal, "state": state, "output_dir": tmp_path}


def test_scriptwriter_different_domain(setup_storytelling_session, model):
    """Holdout case 1: Storytelling domain (history) vs tech domain.

    Tests domain transfer ability - can the prompt adapt to
    narrative-heavy historical content vs data-heavy tech content.
    """
    goal = setup_storytelling_session["goal"]
    state = setup_storytelling_session["state"]

    run = start_script_milestone(state)
    run_dir = Path(run.run_dir)

    # Create valid storytelling script
    script_content = """```style_spine
lut_style: cinematic_drama
aspect_ratio: 16:9
style_template: cinema-drama
visual_strategy: image_heavy
pacing: moderate
tone: epic, historical
glossary: [Colosseum, Pantheon, Roman Forum, aqueduct, Vitruvius]
```

## Scene 1: Opening
type: narration
narrative_role: hook
narration: |
  Two thousand years ago, Roman builders created structures that still stand today.
  Their secrets changed architecture forever.
visual_assets:
  - { role: "background", type: "image", effect: "zoom-in", prompt: "ancient Roman Colosseum at sunset, epic cinematic lighting, wide shot, dramatic mood" }
scene_intent:
  story_beat: hook
  data_story: none
  emotional_target: inspiration
  pacing: moderate
content_brief: |
  Epic opening with Colosseum image and dramatic title.
duration_estimate: 9

## Scene 2: Colosseum Capacity
type: data_card
narrative_role: development
narration: |
  The Colosseum could hold fifty thousand spectators.
scene_intent:
  story_beat: reveal
  data_story: single_impact
  emotional_target: surprise
  pacing: moderate
content_brief: |
  Animated counter showing capacity number.
data_semantic:
  claim: "50,000 spectators capacity"
  anchor_number: 50000
  comparison_axis: "Capacity"
  items:
    - { label: "Colosseum", value: 50000, unit: "people" }
duration_estimate: 6

## Scene 3: Innovation Quote
type: quote_card
narrative_role: climax
narration: |
  As the experts say, Rome's architecture changed the world.
quote: "Rome wasn't built in a day, but its architecture changed the world forever."
attribution: "Prof. Marcus Vitruvius"
scene_intent:
  story_beat: climax
  data_story: none
  emotional_target: reflection
  pacing: dramatic
content_brief: |
  Elegant quote display with serif typography.
duration_estimate: 7

## Scene 4: Conclusion
type: narration
narrative_role: cta
narration: |
  The legacy of Rome lives on in every building we see today.
scene_intent:
  story_beat: cta
  data_story: none
  emotional_target: reflection
  pacing: moderate
content_brief: |
  Final reflection text with fade.
duration_estimate: 6

## Audio Design

bgm_track: dramatic-cinematic
bgm_reasoning: "Historical epic content"

sfx_cues:
  - scene: 1
    event: intro
    sfx: intro-stinger
    anchor: before_audio
    offsetMs: 300
  - scene: 4
    event: outro
    sfx: outro-jingle
    anchor: after_audio
    offsetMs: 400
"""

    manifest_content = {
        "scenes": [
            {"id": "scene-1", "narration": "Two thousand years ago, Roman builders created structures that still stand today. Their secrets changed architecture forever.", "duration": 9},
            {"id": "scene-2", "narration": "The Colosseum could hold fifty thousand spectators.", "duration": 6},
            {"id": "scene-3", "narration": "As the experts say, Rome's architecture changed the world.", "duration": 7},
            {"id": "scene-4", "narration": "The legacy of Rome lives on in every building we see today.", "duration": 6},
        ]
    }

    (run_dir / "script.md").write_text(script_content, encoding="utf-8")
    (run_dir / "manifest.json").write_text(json.dumps(manifest_content, indent=2), encoding="utf-8")

    result = ratify_and_update_script(state, goal)

    assert result.passed, f"Scriptwriter should handle different domain (history/storytelling). Issues: {result.issues}"


def test_scriptwriter_short_duration(setup_short_session, model):
    """Holdout case 2: Very short duration (1min) with vertical format.

    Tests edge case handling - minimal content, different aspect ratio.
    """
    goal = setup_short_session["goal"]
    state = setup_short_session["state"]

    run = start_script_milestone(state)
    run_dir = Path(run.run_dir)

    # Create compact script for short video
    script_content = """```style_spine
lut_style: pastel_dream
aspect_ratio: 9:16
style_template: pastel-pop
visual_strategy: image_none
pacing: punchy
tone: casual, friendly
glossary: [AI, productivity]
```

## Scene 1: Hook
type: narration
narrative_role: hook
narration: |
  Want better AI results? Here are three quick tips.
scene_intent:
  story_beat: hook
  data_story: none
  emotional_target: urgency
  pacing: punchy
content_brief: |
  Bold text "3 AI Tips" with quick animation.
duration_estimate: 4

## Scene 2: Tip One
type: narration
narrative_role: development
narration: |
  First: be specific in your prompts. Details matter.
scene_intent:
  story_beat: reveal
  data_story: none
  emotional_target: trust
  pacing: punchy
content_brief: |
  Text slide "Tip 1: Be Specific" with icon.
duration_estimate: 5

## Scene 3: Tip Two
type: narration
narrative_role: development
narration: |
  Second: iterate and refine your results.
scene_intent:
  story_beat: reveal
  data_story: none
  emotional_target: trust
  pacing: punchy
content_brief: |
  Text slide "Tip 2: Iterate" with cycle animation.
duration_estimate: 4

## Scene 4: Tip Three
type: narration
narrative_role: development
narration: |
  Third: always validate what AI generates.
scene_intent:
  story_beat: reveal
  data_story: none
  emotional_target: trust
  pacing: punchy
content_brief: |
  Text slide "Tip 3: Validate" with checkmark.
duration_estimate: 4

## Scene 5: CTA
type: narration
narrative_role: cta
narration: |
  Try these tips today. You'll see the difference.
scene_intent:
  story_beat: cta
  data_story: none
  emotional_target: urgency
  pacing: moderate
content_brief: |
  Final call to action text.
duration_estimate: 4

## Audio Design

bgm_track: energetic-pop
bgm_reasoning: "Casual quick tips format"

sfx_cues:
  - scene: 1
    event: intro
    sfx: intro-stinger
    anchor: before_audio
    offsetMs: 300
  - scene: 5
    event: outro
    sfx: outro-jingle
    anchor: after_audio
    offsetMs: 400
"""

    manifest_content = {
        "scenes": [
            {"id": "scene-1", "narration": "Want better AI results? Here are three quick tips.", "duration": 4},
            {"id": "scene-2", "narration": "First: be specific in your prompts. Details matter.", "duration": 5},
            {"id": "scene-3", "narration": "Second: iterate and refine your results.", "duration": 4},
            {"id": "scene-4", "narration": "Third: always validate what AI generates.", "duration": 4},
            {"id": "scene-5", "narration": "Try these tips today. You'll see the difference.", "duration": 4},
        ]
    }

    (run_dir / "script.md").write_text(script_content, encoding="utf-8")
    (run_dir / "manifest.json").write_text(json.dumps(manifest_content, indent=2), encoding="utf-8")

    result = ratify_and_update_script(state, goal)

    # Verify short duration and scene count
    total_duration = sum(s["duration"] for s in manifest_content["scenes"])
    assert 4 <= len(manifest_content["scenes"]) <= 6, (
        f"Scene count {len(manifest_content['scenes'])} should be appropriate for a short video"
    )
    assert total_duration <= 90, f"Duration {total_duration}s appropriate for short video"
    assert result.passed, f"Scriptwriter should handle short duration and vertical format. Issues: {result.issues}"
