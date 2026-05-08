from pathlib import Path

import pytest

from deepagents_video_maker.build_render_flow import (
    build_remotion_builder_task_description,
    build_publish_readiness_report,
    package_render_output,
    ratify_and_update_build_scenes,
    ratify_and_update_render_package,
    ratify_render_package,
    render_remotion_project,
    start_build_scenes_milestone,
    start_render_package_milestone,
)
from deepagents_video_maker.models import (
    MilestoneState,
    MilestoneStatus,
    VideoMakerGoal,
    VideoMakerState,
    WorkflowStatus,
)


def _state(tmp_path: Path, script_status=MilestoneStatus.COMPLETED) -> VideoMakerState:
    return VideoMakerState(
        output_dir=str(tmp_path),
        milestones=[
            MilestoneState(id="source_intake", status=MilestoneStatus.COMPLETED),
            MilestoneState(id="script", status=script_status, current_run=1),
            MilestoneState(id="build_scenes"),
            MilestoneState(id="render_package"),
        ],
    )


def _goal() -> VideoMakerGoal:
    goal = VideoMakerGoal(topic="native render tools", source="manual")
    goal.aspect_ratio = "16:9"
    goal.style = "professional"
    return goal


def test_start_build_scenes_requires_completed_script_and_explicit_approval(tmp_path: Path):
    state = _state(tmp_path, script_status=MilestoneStatus.IN_PROGRESS)
    with pytest.raises(RuntimeError, match="script status=in_progress"):
        start_build_scenes_milestone(state, script_approved=True)

    state = _state(tmp_path)
    with pytest.raises(RuntimeError, match="script_approved=True"):
        start_build_scenes_milestone(state, script_approved=False)

    run = start_build_scenes_milestone(state, script_approved=True)

    assert run.milestone == "build_scenes"
    assert Path(run.run_dir).is_dir()
    assert state.milestone("build_scenes").status == MilestoneStatus.IN_PROGRESS


def test_build_remotion_builder_task_description_is_path_based(tmp_path: Path):
    state = _state(tmp_path)
    run = start_build_scenes_milestone(state, script_approved=True)

    description = build_remotion_builder_task_description(_goal(), state, run)

    assert "subagent_type='remotion-builder'" in description
    assert "goal_file:" in description
    assert "script_file:" in description
    assert "source_manifest_file:" in description
    assert "output_project_dir:" in description
    assert "no video-pipeline-cli" in description
    assert "write only output_project_dir/final" in description


def test_ratify_build_scenes_requires_minimal_remotion_project(tmp_path: Path):
    state = _state(tmp_path)
    start_build_scenes_milestone(state, script_approved=True)

    first = ratify_and_update_build_scenes(state)
    assert not first.passed
    assert state.milestone("build_scenes").status == MilestoneStatus.IN_PROGRESS

    project = tmp_path / "remotion-project"
    (project / "src").mkdir(parents=True)
    (project / "package.json").write_text('{"scripts":{}}', encoding="utf-8")
    (project / "src" / "index.ts").write_text("export {};\n", encoding="utf-8")

    second = ratify_and_update_build_scenes(state)
    assert second.passed
    assert state.milestone("build_scenes").status == MilestoneStatus.COMPLETED


def test_render_package_copies_remotion_output_and_ratifies_final_video(tmp_path: Path):
    state = _state(tmp_path)
    state.milestone("build_scenes").status = MilestoneStatus.COMPLETED
    start_render_package_milestone(state)
    out_dir = tmp_path / "remotion-project" / "out"
    out_dir.mkdir(parents=True)
    (out_dir / "video.mp4").write_bytes(b"fake video")
    (out_dir / "thumbnail.jpg").write_bytes(b"fake thumb")

    package_result = package_render_output(state)
    ratify_result = ratify_and_update_render_package(state)

    assert package_result["final_video_exists"] is True
    assert (tmp_path / "final" / "video.mp4").read_bytes() == b"fake video"
    assert (tmp_path / "final" / "thumbnail.jpg").read_bytes() == b"fake thumb"
    assert ratify_result.passed
    assert state.milestone("render_package").status == MilestoneStatus.COMPLETED
    assert state.workflow_status == WorkflowStatus.COMPLETED


def test_render_and_package_require_render_package_milestone_in_progress(tmp_path: Path):
    state = _state(tmp_path)
    state.milestone("build_scenes").status = MilestoneStatus.COMPLETED

    with pytest.raises(RuntimeError, match="render_package status=pending"):
        render_remotion_project(state, composition_id="VideoMaker", command_runner=lambda c, w: (0, "", ""))

    with pytest.raises(RuntimeError, match="render_package status=pending"):
        package_render_output(state)


def test_ratify_render_package_rejects_wrong_duration_video(tmp_path: Path):
    video = tmp_path / "final" / "video.mp4"
    video.parent.mkdir(parents=True)
    video.write_bytes(b"fake video")

    def fake_probe(path: Path):
        assert path == video
        return 0, "10.0\n", ""

    result = ratify_render_package(tmp_path, duration="1-3min", probe_runner=fake_probe)

    assert not result.passed
    assert any(c.id == "final_video_duration_in_range" and not c.passed for c in result.checks)


def test_render_remotion_project_runs_tsc_render_and_still_commands(tmp_path: Path):
    state = _state(tmp_path)
    state.milestone("build_scenes").status = MilestoneStatus.COMPLETED
    start_render_package_milestone(state)
    project = tmp_path / "remotion-project"
    (project / "src").mkdir(parents=True)
    (project / "package.json").write_text('{"scripts":{}}', encoding="utf-8")
    (project / "src" / "index.ts").write_text("export {};\n", encoding="utf-8")
    calls = []

    def fake_runner(command, cwd):
        calls.append((command, cwd))
        return 0, "ok", ""

    result = render_remotion_project(
        state,
        composition_id="VideoMaker",
        install=False,
        command_runner=fake_runner,
    )

    assert result["passed"] is True
    assert [call[0][0:3] for call in calls] == [
        ["pnpm", "exec", "tsc"],
        ["pnpm", "exec", "remotion"],
        ["pnpm", "exec", "remotion"],
    ]
    assert all(call[1] == project for call in calls)
    ratify_log = tmp_path / "ratify" / "render-command.json"
    assert ratify_log.is_file()
    assert "VideoMaker" in ratify_log.read_text(encoding="utf-8")


def test_publish_readiness_report_is_advisory_and_requires_final_video(tmp_path: Path):
    state = _state(tmp_path)

    with pytest.raises(RuntimeError, match="missing final video"):
        build_publish_readiness_report(state)

    final = tmp_path / "final"
    final.mkdir()
    (final / "video.mp4").write_bytes(b"fake video")

    payload = build_publish_readiness_report(
        state,
        decision="needs_revision",
        checklist={"subtitle_readability": "needs larger captions"},
        notes="Opening scene is too text-heavy.",
    )

    assert payload["status"] == "needs_revision"
    assert payload["checklist"]["source_faithfulness"] == "not_reviewed"
    assert payload["checklist"]["subtitle_readability"] == "needs larger captions"
    report = tmp_path / "final" / "publish-readiness.md"
    ratify = tmp_path / "ratify" / "publish-readiness.json"
    assert report.is_file()
    assert ratify.is_file()
    assert "Opening scene is too text-heavy." in report.read_text(encoding="utf-8")
