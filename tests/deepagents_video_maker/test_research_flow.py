from pathlib import Path
import sys
from types import SimpleNamespace

from deepagents_video_maker.models import MilestoneStatus
from deepagents_video_maker.params import parse_video_request
from deepagents_video_maker.session import init_video_session
from deepagents_video_maker.source_flow import (
    ratify_and_update_source_intake,
    start_source_intake_milestone,
)


def _goal(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "brief.md").write_text("# Brief\n", encoding="utf-8")
    return parse_video_request(f"topic=source smoke\nsource=folder\nsource_folder={source}")


def test_start_source_intake_milestone_creates_run_and_updates_state(tmp_path: Path):
    state = init_video_session(_goal(tmp_path), tmp_path, timestamp="20260425-120000")

    run = start_source_intake_milestone(state)

    assert run.milestone == "source_intake"
    assert state.milestone("source_intake").status == MilestoneStatus.IN_PROGRESS


def test_ratify_and_update_source_intake_completes_on_pass(tmp_path: Path):
    goal = _goal(tmp_path)
    state = init_video_session(goal, tmp_path, timestamp="20260425-120000")
    start_source_intake_milestone(state)

    result = ratify_and_update_source_intake(state, goal)

    assert result.passed
    assert state.milestone("source_intake").status == MilestoneStatus.COMPLETED
    assert (Path(state.output_dir) / "artifacts" / "source" / "source-manifest.md").exists()
    assert (Path(state.output_dir) / "ratify" / "source-intake.json").exists()


def test_ratify_source_intake_blocks_missing_folder(tmp_path: Path):
    goal = parse_video_request(
        f"topic=missing folder\nsource=folder\nsource_folder={tmp_path / 'missing'}"
    )
    state = init_video_session(goal, tmp_path, timestamp="20260425-120000")
    start_source_intake_milestone(state)

    result = ratify_and_update_source_intake(state, goal)

    assert not result.passed
    assert result.next_action == "retry_milestone"
    assert state.milestone("source_intake").status == MilestoneStatus.IN_PROGRESS
    assert any("source folder does not exist" in issue for issue in result.issues)


def test_ratify_source_intake_blocks_missing_local_file(tmp_path: Path):
    goal = parse_video_request(
        f"topic=missing file\nsource=local-file\nlocal_file={tmp_path / 'missing.md'}"
    )
    state = init_video_session(goal, tmp_path, timestamp="20260425-120000")
    start_source_intake_milestone(state)

    result = ratify_and_update_source_intake(state, goal)

    assert not result.passed
    assert any("local file does not exist" in issue for issue in result.issues)


def test_explicit_websearch_without_provider_blocks_with_clear_issue(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    monkeypatch.setenv("ORCHESTRATOR_SKILLS_ROOT", str(tmp_path))
    goal = parse_video_request("topic=web topic\nsource=websearch")
    state = init_video_session(goal, tmp_path, timestamp="20260425-120000")
    start_source_intake_milestone(state)

    result = ratify_and_update_source_intake(state, goal)

    assert not result.passed
    assert any("websearch source intake requires TAVILY_API_KEY" in issue for issue in result.issues)


def test_default_websearch_uses_tavily_when_no_source_path(tmp_path: Path, monkeypatch):
    class FakeTavilyClient:
        def __init__(self, api_key):
            assert api_key == "fake-key"

        def search(self, query, max_results, search_depth):
            assert query == "web topic"
            return {
                "results": [
                    {
                        "title": "AI Agent overview",
                        "url": "https://example.com/ai-agent",
                        "content": "AI Agent source snippet",
                    }
                ]
            }

    monkeypatch.setenv("TAVILY_API_KEY", "fake-key")
    monkeypatch.setitem(sys.modules, "tavily", SimpleNamespace(TavilyClient=FakeTavilyClient))
    goal = parse_video_request("topic=web topic")
    state = init_video_session(goal, tmp_path, timestamp="20260425-120100")
    start_source_intake_milestone(state)

    result = ratify_and_update_source_intake(state, goal)

    assert goal.source == "websearch"
    assert result.passed
    manifest = Path(state.output_dir) / "artifacts" / "source" / "source-manifest.md"
    text = manifest.read_text(encoding="utf-8")
    assert "source_type: websearch" in text
    assert "https://example.com/ai-agent" in text
