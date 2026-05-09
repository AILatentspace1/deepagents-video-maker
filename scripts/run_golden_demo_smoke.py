"""Run the deterministic golden-demo smoke path without invoking an LLM."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from deepagents_video_maker.models import VideoMakerGoal
from deepagents_video_maker.script_flow import start_script_milestone
from deepagents_video_maker.session import init_video_session
from deepagents_video_maker.source_flow import (
    ratify_and_update_source_intake,
    start_source_intake_milestone,
)
from deepagents_video_maker.script_flow import ratify_and_update_script
from deepagents_video_maker.state_store import save_state_yaml

SOURCE_FIXTURE = PROJECT_ROOT / "tests" / "fixtures" / "golden_demo_source"
APPROVED_SCRIPT = PROJECT_ROOT / "tests" / "fixtures" / "golden_demo_approved_script.md"


def run(root_dir: Path, timestamp: str = "golden-demo-smoke") -> Path:
    goal = VideoMakerGoal(
        topic="AI Agent Intro",
        source="folder",
        source_folder=str(SOURCE_FIXTURE),
        duration="1-3min",
        style="professional",
        aspect_ratio="16:9",
    )
    state = init_video_session(goal, root_dir, timestamp=timestamp)
    start_source_intake_milestone(state)
    source_result = ratify_and_update_source_intake(state, goal)
    if not source_result.passed:
        raise SystemExit(f"Source Intake failed: {source_result.issues}")

    script_run = start_script_milestone(state)
    script_target = Path(script_run.run_dir) / "script.md"
    shutil.copy2(APPROVED_SCRIPT, script_target)
    script_result = ratify_and_update_script(state, goal)
    if not script_result.passed:
        raise SystemExit(f"Script ratify failed: {script_result.issues}")
    save_state_yaml(state, Path(state.output_dir) / "state.yaml")
    return Path(state.output_dir)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root-dir", default=str(PROJECT_ROOT))
    parser.add_argument("--timestamp", default="golden-demo-smoke")
    args = parser.parse_args()
    output_dir = run(Path(args.root_dir), timestamp=args.timestamp)
    print(f"Golden demo smoke passed: {output_dir}")
    print(f"Script ready for review: {output_dir / 'artifacts' / 'script' / 'run-1' / 'script.md'}")


if __name__ == "__main__":
    main()
