from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.run_golden_demo_smoke import run
from scripts.run_golden_playable_smoke import run as run_playable_smoke
from scripts.run_golden_render_smoke import run as run_render_smoke


def test_golden_demo_smoke_reaches_script_checkpoint_without_network(tmp_path: Path):
    output_dir = run(tmp_path, timestamp="20260507-000000")

    manifest = output_dir / "artifacts" / "source" / "source-manifest.md"
    script = output_dir / "artifacts" / "script" / "run-1" / "script.md"
    contract = output_dir / "artifacts" / "script" / "run-1" / "script-contract.json"
    state = output_dir / "state.yaml"

    assert manifest.is_file()
    assert "brief.md" in manifest.read_text(encoding="utf-8")
    assert script.is_file()
    assert contract.is_file()
    state_text = state.read_text(encoding="utf-8")
    assert "id: source_intake" in state_text
    assert "id: script" in state_text
    assert "status: completed" in state_text


def test_golden_render_smoke_packages_final_fixture_and_publish_readiness(tmp_path: Path):
    output_dir = run_render_smoke(tmp_path, timestamp="20260508-000000")

    project_package = output_dir / "remotion-project" / "package.json"
    project_entry = output_dir / "remotion-project" / "src" / "index.ts"
    final_video = output_dir / "final" / "video.mp4"
    thumbnail = output_dir / "final" / "thumbnail.jpg"
    publish_report = output_dir / "final" / "publish-readiness.md"
    publish_ratify = output_dir / "ratify" / "publish-readiness.json"
    render_ratify = output_dir / "ratify" / "render-package.json"
    state = output_dir / "state.yaml"

    assert project_package.is_file()
    assert project_entry.is_file()
    assert final_video.read_bytes() == b"golden render smoke video fixture\n"
    assert thumbnail.read_bytes() == b"golden render smoke thumbnail fixture\n"
    assert publish_report.is_file()
    assert publish_ratify.is_file()
    assert render_ratify.is_file()
    assert "- status: not_reviewed" in publish_report.read_text(encoding="utf-8")
    state_text = state.read_text(encoding="utf-8")
    assert "id: build_scenes" in state_text
    assert "id: render_package" in state_text
    assert "workflow_status: completed" in state_text


def test_golden_playable_smoke_produces_probeable_mp4(tmp_path: Path):
    output_dir = run_playable_smoke(tmp_path, timestamp="20260508-010000")

    final_video = output_dir / "final" / "video.mp4"
    thumbnail = output_dir / "final" / "thumbnail.jpg"
    render_ratify = output_dir / "ratify" / "render-package.json"
    publish_report = output_dir / "final" / "publish-readiness.md"
    state = output_dir / "state.yaml"

    assert final_video.is_file()
    assert final_video.stat().st_size > 100_000
    assert final_video.read_bytes() != b"golden render smoke video fixture\n"
    assert thumbnail.is_file()
    ratify_text = render_ratify.read_text(encoding="utf-8")
    assert '"ffprobe_duration_exit_zero"' in ratify_text
    assert '"final_video_duration_in_range"' in ratify_text
    assert "- status: not_reviewed" in publish_report.read_text(encoding="utf-8")
    state_text = state.read_text(encoding="utf-8")
    assert "id: render_package" in state_text
    assert "workflow_status: completed" in state_text
