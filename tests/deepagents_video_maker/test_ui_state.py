import json
from pathlib import Path
from types import SimpleNamespace

from langchain_core.messages import ToolMessage
from langgraph.types import Command

from deepagents_video_maker.middleware import VideoMakerUiStateMiddleware
from deepagents_video_maker.models import MilestoneStatus
from deepagents_video_maker.params import parse_video_request
from deepagents_video_maker.session import init_video_session
from deepagents_video_maker.state_store import save_state_yaml, update_milestone_status
from deepagents_video_maker.ui_state import build_video_maker_ui_state


def test_build_video_maker_ui_state_projects_milestones_artifacts_and_publish_readiness(tmp_path: Path):
    goal = parse_video_request("topic=ui projection")
    state = init_video_session(goal, tmp_path, timestamp="20260508-100000")
    update_milestone_status(state, "source_intake", MilestoneStatus.COMPLETED)
    update_milestone_status(state, "script", MilestoneStatus.BLOCKED, blocking_reason="needs user review")
    save_state_yaml(state, Path(state.output_dir) / "state.yaml")
    (Path(state.output_dir) / "artifacts" / "source").mkdir(parents=True, exist_ok=True)
    (Path(state.output_dir) / "artifacts" / "source" / "source-manifest.md").write_text(
        "# Source Manifest\n",
        encoding="utf-8",
    )
    (Path(state.output_dir) / "ratify").mkdir(parents=True, exist_ok=True)
    (Path(state.output_dir) / "ratify" / "publish-readiness.json").write_text(
        json.dumps({"status": "needs_revision", "report": "final/publish-readiness.md", "notes": "fix pacing"}),
        encoding="utf-8",
    )

    ui = build_video_maker_ui_state(state.output_dir)

    assert ui["outputDir"] == state.output_dir
    assert ui["workflowStatus"] == "in_progress"
    assert ui["currentBlocker"] == "needs user review"
    assert ui["milestones"][0]["status"] == "completed"
    assert ui["milestones"][1]["blockingReason"] == "needs user review"
    assert ui["publishReadiness"]["status"] == "needs_revision"
    assert any(item["kind"] == "source_manifest" and item["exists"] for item in ui["artifacts"])


def test_build_video_maker_ui_state_uses_current_script_run(tmp_path: Path):
    goal = parse_video_request("topic=ui projection retry")
    state = init_video_session(goal, tmp_path, timestamp="20260508-100010")
    state.milestone("script").current_run = 2
    save_state_yaml(state, Path(state.output_dir) / "state.yaml")
    run_2 = Path(state.output_dir) / "artifacts" / "script" / "run-2"
    run_2.mkdir(parents=True)
    (run_2 / "script.md").write_text("## Scene 1\n", encoding="utf-8")
    (run_2 / "script-contract.json").write_text("{}", encoding="utf-8")

    ui = build_video_maker_ui_state(state.output_dir)

    script_milestone = next(item for item in ui["milestones"] if item["id"] == "script")
    assert all("run-2" in path for path in script_milestone["artifactPaths"])
    assert any(item["kind"] == "script" and item["exists"] and "run-2" in item["path"] for item in ui["artifacts"])


def test_video_maker_ui_state_middleware_updates_langgraph_state(tmp_path: Path):
    goal = parse_video_request("topic=middleware projection")
    state = init_video_session(goal, tmp_path, timestamp="20260508-100100")
    save_state_yaml(state, Path(state.output_dir) / "state.yaml")
    request = SimpleNamespace(
        tool_call={"name": "vm_load_state", "args": {"output_dir": state.output_dir}},
        runtime=None,
    )
    message = ToolMessage(
        content=json.dumps({"output_dir": state.output_dir}),
        tool_call_id="call-1",
        name="vm_load_state",
    )

    result = VideoMakerUiStateMiddleware().wrap_tool_call(request, lambda _: message)

    assert isinstance(result, Command)
    assert result.update["messages"] == [message]
    assert result.update["video_maker"]["outputDir"] == state.output_dir
    assert result.update["video_maker"]["milestones"][0]["id"] == "source_intake"
