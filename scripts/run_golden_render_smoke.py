"""Run the deterministic approved-script downstream render/package smoke.

This smoke intentionally does not invoke an LLM or a real Remotion browser
render. It starts from the approved golden script fixture, creates the minimal
Remotion project structure expected by Build Scenes, simulates a renderer output
fixture, then exercises package, render ratify, and publish-readiness logic.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from scripts.run_golden_demo_smoke import run as run_script_checkpoint

from deepagents_video_maker.build_render_flow import (
    build_publish_readiness_report,
    package_render_output,
    ratify_and_update_build_scenes,
    ratify_and_update_render_package,
    start_build_scenes_milestone,
    start_render_package_milestone,
)
from deepagents_video_maker.state_store import load_state_yaml, save_state_yaml


def run(root_dir: Path, timestamp: str = "golden-render-smoke") -> Path:
    output_dir = run_script_checkpoint(root_dir, timestamp=timestamp)
    state_path = output_dir / "state.yaml"
    state = load_state_yaml(state_path)

    start_build_scenes_milestone(state, script_approved=True)
    _write_minimal_remotion_project(output_dir)
    build_result = ratify_and_update_build_scenes(state)
    if not build_result.passed:
        raise SystemExit(f"Build Scenes ratify failed: {build_result.issues}")

    start_render_package_milestone(state)
    _write_simulated_render_output(output_dir)
    package_result = package_render_output(state)
    if not package_result["final_video_exists"]:
        raise SystemExit(f"Render package copy failed: {package_result}")

    render_result = ratify_and_update_render_package(
        state,
        duration="1-3min",
        probe_runner=lambda path: (0, "90.0\n", ""),
    )
    if not render_result.passed:
        raise SystemExit(f"Render Package ratify failed: {render_result.issues}")

    build_publish_readiness_report(
        state,
        decision="not_reviewed",
        notes=(
            "Golden render smoke used simulated renderer output. "
            "Human publish review is still required."
        ),
    )
    save_state_yaml(state, state_path)
    return output_dir


def _write_minimal_remotion_project(output_dir: Path) -> None:
    project = output_dir / "remotion-project"
    (project / "src").mkdir(parents=True, exist_ok=True)
    (project / "package.json").write_text(
        '{\n'
        '  "private": true,\n'
        '  "scripts": {"typecheck": "tsc --noEmit"},\n'
        '  "dependencies": {"@remotion/cli": "latest", "remotion": "latest"}\n'
        '}\n',
        encoding="utf-8",
    )
    (project / "src" / "index.ts").write_text(
        "export const compositionId = 'GoldenDemo';\n",
        encoding="utf-8",
    )


def _write_simulated_render_output(output_dir: Path) -> None:
    out = output_dir / "remotion-project" / "out"
    out.mkdir(parents=True, exist_ok=True)
    # This is a deterministic renderer-output fixture, not a playable MP4.
    # The smoke validates package/state/ratify plumbing without requiring
    # Chromium, ffmpeg, or Remotion availability on every developer machine.
    (out / "video.mp4").write_bytes(b"golden render smoke video fixture\n")
    (out / "thumbnail.jpg").write_bytes(b"golden render smoke thumbnail fixture\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root-dir", default=str(PROJECT_ROOT))
    parser.add_argument("--timestamp", default="golden-render-smoke")
    args = parser.parse_args()
    output_dir = run(Path(args.root_dir), timestamp=args.timestamp)
    print(f"Golden render smoke passed: {output_dir}")
    print(f"Final video fixture: {output_dir / 'final' / 'video.mp4'}")
    print(f"Publish readiness: {output_dir / 'final' / 'publish-readiness.md'}")


if __name__ == "__main__":
    main()
