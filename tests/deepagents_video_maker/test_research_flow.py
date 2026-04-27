from pathlib import Path

from deepagents_video_maker.models import MilestoneStatus
from deepagents_video_maker.params import parse_video_request
from deepagents_video_maker.research_flow import (
    build_researcher_task_description,
    ratify_and_update_research,
    start_research_milestone,
)
from deepagents_video_maker.session import init_video_session


def _goal():
    return parse_video_request(
        """
        topic=介绍 video-maker skill
        source=local-file
        local_file=/docs/ARCHITECTURE-VIDEO-MAKER.md
        excalidraw_file=/docs/video-maker-architecture.excalidraw
        """
    )


def test_start_research_milestone_creates_run_and_updates_state(tmp_path: Path):
    goal = _goal()
    state = init_video_session(goal, tmp_path, timestamp="20260425-120000")

    run = start_research_milestone(state)

    assert run.milestone == "research"
    assert run.run_number == 1
    assert Path(run.run_dir).is_dir()
    assert state.milestone("research").status == MilestoneStatus.IN_PROGRESS


def test_build_researcher_task_description_contains_contract(tmp_path: Path):
    goal = _goal()
    state = init_video_session(goal, tmp_path, timestamp="20260425-120000")
    run = start_research_milestone(state)

    description = build_researcher_task_description(goal, state, run)

    assert "Input contract" in description
    assert "Output contract" in description
    assert "topic: 介绍 video-maker skill" in description
    assert "source: local-file" in description
    assert "output_path:" in description
    assert "research_path:" in description
    assert "blocking_issues:" in description
    assert str(Path(run.run_dir) / "research.md") in description


def test_build_researcher_task_description_uses_virtual_path_when_root_env(
    tmp_path: Path, monkeypatch
):
    monkeypatch.setenv("ORCHESTRATOR_SKILLS_ROOT", str(tmp_path))
    goal = _goal()
    state = init_video_session(goal, tmp_path, timestamp="20260425-120000")
    run = start_research_milestone(state)

    description = build_researcher_task_description(goal, state, run)

    assert "/output/20260425-120000-video-" in description
    assert "\\output\\" not in description


def test_ratify_and_update_research_completes_on_pass(tmp_path: Path):
    goal = _goal()
    state = init_video_session(goal, tmp_path, timestamp="20260425-120000")
    run = start_research_milestone(state)
    research_path = Path(run.run_dir) / "research.md"
    research_path.write_text(
        "# Research\n\n"
        "## 一、核心事实\n"
        + ("内容" * 450)
        + "\n## 二、关键数据\n- data\n"
        + "\n## 三、视觉素材线索\n- visual\n",
        encoding="utf-8",
    )

    result = ratify_and_update_research(state, goal)

    assert result.passed is True
    assert result.next_action == "complete_milestone"
    assert state.milestone("research").status == MilestoneStatus.COMPLETED
    assert state.milestone("research").ratify["passed"] is True


def test_ratify_and_update_research_retries_then_blocks(tmp_path: Path):
    goal = _goal()
    state = init_video_session(goal, tmp_path, timestamp="20260425-120000")
    start_research_milestone(state)

    first = ratify_and_update_research(state, goal)
    second = ratify_and_update_research(state, goal)
    third = ratify_and_update_research(state, goal)

    assert first.passed is False
    assert second.passed is False
    assert third.passed is False
    assert third.next_action == "block_for_user"
    assert state.milestone("research").status == MilestoneStatus.BLOCKED
    assert "max retries" in state.milestone("research").blocking_reason
