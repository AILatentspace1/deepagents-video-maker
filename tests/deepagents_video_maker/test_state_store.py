from pathlib import Path

from deepagents_video_maker.models import MilestoneStatus
from deepagents_video_maker.params import parse_video_request
from deepagents_video_maker.session import create_milestone_run, init_video_session
from deepagents_video_maker.state_store import save_state_yaml, update_milestone_status


def test_update_milestone_status_and_save(tmp_path: Path):
    goal = parse_video_request("topic=介绍 video-maker-v2 skill\nsource=folder")
    state = init_video_session(goal, tmp_path, timestamp="20260425-120000")

    update_milestone_status(
        state,
        "source_intake",
        MilestoneStatus.BLOCKED,
        blocking_reason="missing source-manifest.md",
    )
    save_state_yaml(state, Path(state.output_dir) / "state.yaml")

    source_intake = state.milestone("source_intake")
    assert source_intake.status == MilestoneStatus.BLOCKED
    assert source_intake.blocking_reason == "missing source-manifest.md"
    text = (Path(state.output_dir) / "state.yaml").read_text(encoding="utf-8")
    assert "status: blocked" in text
    assert 'blocking_reason: "missing source-manifest.md"' in text


def test_create_milestone_run_updates_state(tmp_path: Path):
    goal = parse_video_request("topic=介绍 video-maker-v2 skill\nsource=folder")
    state = init_video_session(goal, tmp_path, timestamp="20260425-120000")

    run = create_milestone_run(state, "source_intake")

    assert run.milestone == "source_intake"
    assert run.run_number == 1
    assert Path(run.run_dir).is_dir()
    assert state.milestone("source_intake").status == MilestoneStatus.IN_PROGRESS
    assert state.milestone("source_intake").current_run == 1


def test_update_milestone_status_completed_sets_completed_at_and_clears_blocker(tmp_path: Path):
    goal = parse_video_request("topic=介绍 video-maker-v2 skill\nsource=folder")
    state = init_video_session(goal, tmp_path, timestamp="20260425-120000")
    source_intake = state.milestone("source_intake")
    source_intake.blocking_reason = "previous blocker"

    update_milestone_status(state, "source_intake", MilestoneStatus.COMPLETED)

    assert source_intake.completed_at is not None
    assert source_intake.blocking_reason is None


def test_save_state_yaml_is_parseable_by_pyyaml_with_windows_paths(tmp_path: Path):
    import yaml

    goal = parse_video_request("topic=介绍 video-maker-v2 skill\nsource=folder")
    state = init_video_session(goal, tmp_path, timestamp="20260425-120000")
    state_path = Path(state.output_dir) / "state.yaml"

    data = yaml.safe_load(state_path.read_text(encoding="utf-8"))

    assert data["output_dir"] == state.output_dir


def test_workflow_contract_documents_runtime_milestone_state_schema():
    text = Path("skills/video-maker-v2/references/workflow-contract.md").read_text(
        encoding="utf-8"
    )

    assert "workflow: video-maker-v2" in text
    assert "milestones:" in text
    assert "id: source_intake" in text
    assert "current_step:" not in text
