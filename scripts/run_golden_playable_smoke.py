"""Run a deterministic golden smoke that produces a playable MP4.

This is the product-demo tier above ``run_golden_render_smoke.py``. The regular
render smoke validates pipeline plumbing with a simulated fixture; this script
requires a real media encoder (or Remotion) and verifies the final MP4 with
``ffprobe``.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
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
    render_remotion_project,
    start_build_scenes_milestone,
    start_render_package_milestone,
)
from deepagents_video_maker.state_store import load_state_yaml, save_state_yaml


COMPOSITION_ID = "GoldenPlayable"
PLAYABLE_DURATION_SECONDS = 65


def run(
    root_dir: Path,
    timestamp: str = "golden-playable-smoke",
    *,
    renderer: str = "ffmpeg",
    install: bool = False,
) -> Path:
    """Create a playable golden MP4 and ratify the full render package path.

    ``renderer="ffmpeg"`` is the deterministic default for local/CI proof of a
    playable MP4. ``renderer="remotion"`` uses the minimal Remotion project and
    the native render command path, optionally installing project dependencies.
    """

    output_dir = run_script_checkpoint(root_dir, timestamp=timestamp)
    state_path = output_dir / "state.yaml"
    state = load_state_yaml(state_path)

    start_build_scenes_milestone(state, script_approved=True)
    _write_minimal_playable_remotion_project(output_dir)
    build_result = ratify_and_update_build_scenes(state)
    if not build_result.passed:
        raise SystemExit(f"Build Scenes ratify failed: {build_result.issues}")

    start_render_package_milestone(state)
    if renderer == "ffmpeg":
        _render_with_ffmpeg(output_dir)
    elif renderer == "remotion":
        render_result = render_remotion_project(
            state,
            composition_id=COMPOSITION_ID,
            install=install,
        )
        if not render_result["passed"]:
            raise SystemExit(f"Remotion render failed: {render_result}")
    else:
        raise SystemExit(f"Unsupported renderer: {renderer}")

    package_result = package_render_output(state)
    if not package_result["final_video_exists"]:
        raise SystemExit(f"Render package copy failed: {package_result}")

    render_ratify = ratify_and_update_render_package(state, duration="1-3min")
    if not render_ratify.passed:
        raise SystemExit(f"Render Package ratify failed: {render_ratify.issues}")

    build_publish_readiness_report(
        state,
        decision="not_reviewed",
        notes=(
            "Golden playable smoke produced a real playable MP4. "
            "Human visual/taste review is still required before publishing."
        ),
    )
    save_state_yaml(state, state_path)
    return output_dir


def _write_minimal_playable_remotion_project(output_dir: Path) -> None:
    project = output_dir / "remotion-project"
    (project / "src").mkdir(parents=True, exist_ok=True)
    (project / "package.json").write_text(
        '{\n'
        '  "private": true,\n'
        '  "scripts": {"typecheck": "tsc --noEmit", "render": "remotion render src/index.ts GoldenPlayable --output=out/video.mp4 --gl=angle"},\n'
        '  "dependencies": {\n'
        '    "@remotion/cli": "^4.0.459",\n'
        '    "remotion": "^4.0.459",\n'
        '    "react": "^19.0.0",\n'
        '    "react-dom": "^19.0.0"\n'
        '  },\n'
        '  "devDependencies": {\n'
        '    "@types/react": "^19.0.0",\n'
        '    "typescript": "^5.0.0"\n'
        '  }\n'
        '}\n',
        encoding="utf-8",
    )
    (project / "tsconfig.json").write_text(
        '{\n'
        '  "compilerOptions": {\n'
        '    "target": "ES2020",\n'
        '    "module": "ESNext",\n'
        '    "moduleResolution": "Bundler",\n'
        '    "jsx": "react-jsx",\n'
        '    "strict": true,\n'
        '    "skipLibCheck": true,\n'
        '    "esModuleInterop": true,\n'
        '  },\n'
        '  "include": ["src"]\n'
        '}\n',
        encoding="utf-8",
    )
    (project / "src" / "index.ts").write_text(
        """import React from 'react';
import {
  AbsoluteFill,
  Composition,
  interpolate,
  registerRoot,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

const durationInFrames = 65 * 30;

function GoldenPlayable() {
  const frame = useCurrentFrame();
  const { durationInFrames: total } = useVideoConfig();
  const progress = interpolate(frame, [0, total - 1], [0, 100]);
  const opacity = interpolate(frame, [0, 45, total - 45, total - 1], [0, 1, 1, 0]);
  return React.createElement(
    AbsoluteFill,
    {
      style: {
        alignItems: 'center',
        background: 'linear-gradient(135deg, #07111f 0%, #123c69 55%, #2f6868 100%)',
        color: 'white',
        display: 'flex',
        fontFamily: 'Arial, sans-serif',
        justifyContent: 'center',
      },
    },
    React.createElement(
      'div',
      { style: { maxWidth: 920, opacity, textAlign: 'center' } },
      React.createElement('div', { style: { fontSize: 72, fontWeight: 800 } }, 'AI Agent Intro'),
      React.createElement(
        'div',
        { style: { fontSize: 34, marginTop: 28 } },
        'Source → Script → Build → Render → Publish readiness'
      ),
      React.createElement(
        'div',
        {
          style: {
            background: 'rgba(255,255,255,0.22)',
            borderRadius: 999,
            height: 18,
            marginTop: 54,
            overflow: 'hidden',
            width: 760,
          },
        },
        React.createElement('div', {
          style: {
            background: '#9df2d5',
            height: '100%',
            width: `${progress}%`,
          },
        })
      )
    )
  );
}

function RemotionRoot() {
  return React.createElement(Composition, {
    id: 'GoldenPlayable',
    component: GoldenPlayable,
    durationInFrames,
    fps: 30,
    width: 1280,
    height: 720,
  });
}

registerRoot(RemotionRoot);
""",
        encoding="utf-8",
    )


def _render_with_ffmpeg(output_dir: Path) -> None:
    if shutil.which("ffmpeg") is None:
        raise SystemExit(
            "ffmpeg is required for golden playable smoke. "
            "Install ffmpeg or run with --renderer remotion --install."
        )
    out = output_dir / "remotion-project" / "out"
    out.mkdir(parents=True, exist_ok=True)
    video = out / "video.mp4"
    thumbnail = out / "thumbnail.jpg"
    _run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"testsrc2=size=1280x720:rate=30:duration={PLAYABLE_DURATION_SECONDS}",
            "-pix_fmt",
            "yuv420p",
            str(video),
        ]
    )
    _run(["ffmpeg", "-y", "-i", str(video), "-frames:v", "1", str(thumbnail)])


def _run(command: list[str]) -> None:
    completed = subprocess.run(command, text=True, capture_output=True, timeout=900)
    if completed.returncode != 0:
        raise SystemExit(
            f"Command failed: {' '.join(command)}\n"
            f"stdout:\n{completed.stdout[-4000:]}\n"
            f"stderr:\n{completed.stderr[-4000:]}"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root-dir", default=str(PROJECT_ROOT))
    parser.add_argument("--timestamp", default="golden-playable-smoke")
    parser.add_argument("--renderer", choices=["ffmpeg", "remotion"], default="ffmpeg")
    parser.add_argument(
        "--install",
        action="store_true",
        help="Install dependencies before running the Remotion renderer.",
    )
    args = parser.parse_args()
    output_dir = run(
        Path(args.root_dir),
        timestamp=args.timestamp,
        renderer=args.renderer,
        install=args.install,
    )
    print(f"Golden playable smoke passed: {output_dir}")
    print(f"Playable video: {output_dir / 'final' / 'video.mp4'}")
    print(f"Publish readiness: {output_dir / 'final' / 'publish-readiness.md'}")


if __name__ == "__main__":
    main()
