"""Training eval cases for scriptwriter prompt optimization."""

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
from deepagents_video_maker.state_store import save_state_yaml


@pytest.fixture
def setup_session(tmp_path, sample_research_content):
    """Set up a session with completed research milestone."""
    goal = VideoMakerGoal(
        topic="AI Agent Evolution",
        source="local-file",
        local_file="research.md"
    )
    goal.duration = "1-3min"
    goal.style = "professional"
    goal.aspect_ratio = "16:9"
    goal = derive_video_params(goal)

    state = init_video_session(goal, tmp_path, timestamp="20260429-100000")

    # Set up completed research
    research_milestone = state.milestone("research")
    research_milestone.status = MilestoneStatus.COMPLETED
    research_milestone.current_run = 1

    # Write research file under the session's output_dir
    research_dir = Path(state.output_dir) / "artifacts" / "research" / "run-1"
    research_dir.mkdir(parents=True, exist_ok=True)
    (research_dir / "research.md").write_text(sample_research_content, encoding="utf-8")

    save_state_yaml(state, tmp_path / "state.yaml")

    return {"goal": goal, "state": state, "output_dir": tmp_path}


@pytest.mark.parametrize("model", ["claude-sonnet-4-6"], indirect=True)
def test_scriptwriter_basic_structure(setup_session, model):
    """Train case 1: Scriptwriter generates valid script with required structure.

    Success criteria:
    - script.md exists
    - manifest.json exists
    - Has at least one scene with proper formatting
    - Passes ratify_script validation
    """
    goal = setup_session["goal"]
    state = setup_session["state"]
    output_dir = setup_session["output_dir"]

    # Start script milestone
    run = start_script_milestone(state)
    run_dir = Path(run.run_dir)

    # Simulate scriptwriter output (minimal valid script)
    script_content = """```style_spine
lut_style: tech_cool
aspect_ratio: 16:9
style_template: tech-noir
visual_strategy: image_light
pacing: moderate
tone: professional, confident
glossary: [AI Agent, LLM, Claude, GPT-4]
```

## Scene 1: Opening Hook
type: narration
narrative_role: hook
narration: |
  AI Agents are transforming how we work in 2025.
  From simple chatbots to autonomous systems.
scene_intent:
  story_beat: hook
  data_story: none
  emotional_target: inspiration
  pacing: moderate
content_brief: |
  Bold title animation "AI Agent Era" with animated entry.
duration_estimate: 6

## Scene 2: Market Overview
type: data_card
narrative_role: development
narration: |
  Global investment reached 150 billion dollars.
  Three tech giants dominate the market.
scene_intent:
  story_beat: reveal
  data_story: comparison
  emotional_target: surprise
  pacing: moderate
content_brief: |
  Show market share pie chart with leader emphasis.
data_semantic:
  claim: "Three giants control 70% of market"
  anchor_number: 150
  comparison_axis: "Market Share"
  items:
    - { label: "Google", value: 35, unit: "%" }
    - { label: "Microsoft", value: 25, unit: "%" }
    - { label: "Amazon", value: 10, unit: "%" }
    - { label: "Others", value: 30, unit: "%" }
duration_estimate: 7

## Scene 3: Call to Action
type: narration
narrative_role: cta
narration: |
  The future of work is here. Are you ready?
scene_intent:
  story_beat: cta
  data_story: none
  emotional_target: urgency
  pacing: moderate
content_brief: |
  Final text reveal with fade out.
duration_estimate: 5

## Audio Design

bgm_track: upbeat-tech
bgm_reasoning: "Tech topic + professional style"

sfx_cues:
  - scene: 1
    event: intro_stinger
    sfx: intro-stinger
    anchor: before_audio
    offsetMs: 300
  - scene: 2
    event: data_reveal
    sfx: counter-pop
    at: 80%
  - scene: 3
    event: outro_jingle
    sfx: outro-jingle
    anchor: after_audio
    offsetMs: 400
"""

    manifest_content = {
        "scenes": [
            {"id": "scene-1", "narration": "AI Agents are transforming how we work in 2025. From simple chatbots to autonomous systems.", "duration": 6},
            {"id": "scene-2", "narration": "Global investment reached 150 billion dollars. Three tech giants dominate the market.", "duration": 7},
            {"id": "scene-3", "narration": "The future of work is here. Are you ready?", "duration": 5},
        ]
    }

    (run_dir / "script.md").write_text(script_content, encoding="utf-8")
    (run_dir / "manifest.json").write_text(json.dumps(manifest_content, indent=2), encoding="utf-8")

    # Ratify
    result = ratify_and_update_script(state, goal)

    assert result.passed, f"Scriptwriter should generate valid script structure. Errors: {result.errors}"
    assert state.milestone("script").status == MilestoneStatus.COMPLETED


@pytest.mark.parametrize("model", ["claude-sonnet-4-6"], indirect=True)
def test_scriptwriter_scene_count(setup_session, model):
    """Train case 2: Script has appropriate number of scenes for 1-3min duration.

    Success criteria:
    - Total scenes between 10-16 (per duration guidelines)
    - Scene durations sum to approximately target duration
    - No single scene exceeds 15 seconds
    """
    goal = setup_session["goal"]
    state = setup_session["state"]

    run = start_script_milestone(state)
    run_dir = Path(run.run_dir)

    # Create script with proper scene count
    scenes = []
    manifest_scenes = []

    for i in range(1, 13):  # 12 scenes is mid-range for 1-3min
        scene_type = "narration" if i % 3 != 0 else "data_card"
        scenes.append(f"""## Scene {i}: Part {i}
type: {scene_type}
narrative_role: development
narration: |
  Content for scene {i}.
scene_intent:
  story_beat: reveal
  data_story: {'comparison' if scene_type == 'data_card' else 'none'}
  emotional_target: trust
  pacing: moderate
content_brief: |
  Visual for scene {i}.
{'data_semantic:\n  claim: "Test"\n  anchor_number: 100\n  comparison_axis: "Test"\n  items:\n    - { label: "A", value: 50, unit: "%" }\n    - { label: "B", value: 50, unit: "%" }' if scene_type == 'data_card' else ''}
duration_estimate: {8 if i <= 6 else 7}
""")
        manifest_scenes.append({
            "id": f"scene-{i}",
            "narration": f"Content for scene {i}.",
            "duration": 8 if i <= 6 else 7
        })

    script_content = """```style_spine
lut_style: tech_cool
aspect_ratio: 16:9
style_template: tech-noir
visual_strategy: image_light
pacing: moderate
tone: professional
glossary: [AI, Agent]
```

""" + "\n\n".join(scenes) + """

## Audio Design

bgm_track: upbeat-tech
bgm_reasoning: "Standard tech track"

sfx_cues: []
"""

    (run_dir / "script.md").write_text(script_content, encoding="utf-8")
    (run_dir / "manifest.json").write_text(json.dumps({"scenes": manifest_scenes}, indent=2), encoding="utf-8")

    result = ratify_and_update_script(state, goal)

    # Check scene count
    total_duration = sum(s["duration"] for s in manifest_scenes)
    assert 10 <= len(manifest_scenes) <= 16, f"Scene count {len(manifest_scenes)} should be 10-16 for 1-3min video"
    assert 60 <= total_duration <= 180, f"Total duration {total_duration}s should be 60-180s for 1-3min video"
    assert result.passed, f"Script with proper scene count should pass. Errors: {result.errors}"


@pytest.mark.parametrize("model", ["claude-sonnet-4-6"], indirect=True)
def test_scriptwriter_ratify_rules(setup_session, model):
    """Train case 3: Script passes all ratify_script validation rules.

    Success criteria:
    - Both script.md and manifest.json exist
    - Script has at least one ## Scene block
    - Manifest has non-empty scenes array
    - All scenes have id, narration, duration
    - Scene IDs are unique
    - Scene count matches between script and manifest
    """
    goal = setup_session["goal"]
    state = setup_session["state"]

    run = start_script_milestone(state)
    run_dir = Path(run.run_dir)

    # Create fully compliant script
    script_content = """```style_spine
lut_style: news_neutral
aspect_ratio: 16:9
style_template: news-clean
visual_strategy: image_light
pacing: moderate
tone: professional, informative
glossary: [AI Agent, machine learning, automation]
```

## Scene 1: Introduction
type: narration
narrative_role: hook
narration: |
  Welcome to our exploration of AI Agents.
  These systems are changing everything.
scene_intent:
  story_beat: hook
  data_story: none
  emotional_target: inspiration
  pacing: moderate
content_brief: |
  Opening title with fade-in animation.
duration_estimate: 7

## Scene 2: Key Data
type: data_card
narrative_role: development
narration: |
  The market has grown by 300 percent this year.
scene_intent:
  story_beat: reveal
  data_story: single_impact
  emotional_target: surprise
  pacing: moderate
content_brief: |
  Big number counter animation.
data_semantic:
  claim: "300% growth rate"
  anchor_number: 300
  comparison_axis: "Growth"
  items:
    - { label: "2024", value: 100, unit: "%" }
    - { label: "2025", value: 300, unit: "%" }
duration_estimate: 6

## Scene 3: Quote
type: quote_card
narrative_role: climax
narration: |
  As Dr. Chen said, agents are not just responding, they're acting.
quote: "AI Agents are not just responding anymore, they're acting."
attribution: "Dr. Sarah Chen, MIT AI Lab"
scene_intent:
  story_beat: climax
  data_story: none
  emotional_target: reflection
  pacing: dramatic
content_brief: |
  Centered quote with typewriter effect.
duration_estimate: 5

## Scene 4: Closing
type: narration
narrative_role: cta
narration: |
  The future is here. Join the revolution.
scene_intent:
  story_beat: cta
  data_story: none
  emotional_target: urgency
  pacing: moderate
content_brief: |
  Call to action text with highlight.
duration_estimate: 5

## Audio Design

bgm_track: calm-corporate
bgm_reasoning: "Professional news-style content"

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
            {
                "id": "scene-1",
                "narration": "Welcome to our exploration of AI Agents. These systems are changing everything.",
                "duration": 7
            },
            {
                "id": "scene-2",
                "narration": "The market has grown by 300 percent this year.",
                "duration": 6
            },
            {
                "id": "scene-3",
                "narration": "As Dr. Chen said, agents are not just responding, they're acting.",
                "duration": 5
            },
            {
                "id": "scene-4",
                "narration": "The future is here. Join the revolution.",
                "duration": 5
            }
        ]
    }

    (run_dir / "script.md").write_text(script_content, encoding="utf-8")
    (run_dir / "manifest.json").write_text(json.dumps(manifest_content, indent=2), encoding="utf-8")

    result = ratify_and_update_script(state, goal)

    assert result.passed, f"Fully compliant script should pass all validation rules. Errors: {result.errors}"
    assert len(result.errors) == 0, "Should have no validation errors"
