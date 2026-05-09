"""Holdout eval: state machine transitions must follow the defined sequence.

These are regression guards for state management.  If the better-harness
outer agent proposes changes that break milestone ordering or status
transitions, these tests will fail and the proposal will be rejected.
"""

from __future__ import annotations

from pathlib import Path

from deepagents_video_maker.langchain_tools import (
    vm_init_video_session,
    vm_start_research,
    vm_start_script,
)
from deepagents_video_maker.models import MilestoneStatus
from deepagents_video_maker.state_store import (
    load_state_yaml,
    save_state_yaml,
    update_milestone_status,
)


def _invoke(tool, **kwargs):
    if hasattr(tool, "invoke"):
        return tool.invoke(kwargs)
    return tool(**kwargs)


def _make_session(tmp_path: Path, *, ts: str) -> str:
    init = _invoke(
        vm_init_video_session,
        topic="State machine test",
        source="local-file",
        local_file="/docs/arch.md",
        root_dir=str(tmp_path),
        timestamp=ts,
    )
    return init["output_dir"]


def test_fresh_session_milestones_start_pending(tmp_path: Path) -> None:
    """All milestones in a newly initialised session must be 'pending'."""
    output_dir = _make_session(tmp_path, ts="20260601-000000")
    state = load_state_yaml(Path(output_dir) / "state.yaml")

    for ms in state.milestones:
        assert ms.status == MilestoneStatus.PENDING, (
            f"milestone '{ms.id}' must start as pending, got {ms.status}"
        )


def test_start_research_sets_in_progress(tmp_path: Path) -> None:
    """vm_start_research must advance research status to 'in_progress'."""
    output_dir = _make_session(tmp_path, ts="20260601-000001")
    result = _invoke(vm_start_research, output_dir=output_dir)

    milestones = {m["id"]: m for m in result["state"]["milestones"]}
    assert milestones["research"]["status"] == "in_progress", (
        f"expected in_progress after start_research, got {milestones['research']['status']}"
    )


def test_start_script_requires_completed_research(tmp_path: Path) -> None:
    """vm_start_script must return an error if research is not completed."""
    output_dir = _make_session(tmp_path, ts="20260601-000002")
    # Do NOT complete research first.
    result = _invoke(vm_start_script, output_dir=output_dir)

    # The tool returns a structured error dict, not raises.
    assert "error" in result, (
        "vm_start_script must return an error dict when research is not completed"
    )


def test_start_script_succeeds_after_research_completed(tmp_path: Path) -> None:
    """vm_start_script must succeed once research is completed."""
    output_dir = _make_session(tmp_path, ts="20260601-000003")
    state_path = Path(output_dir) / "state.yaml"
    state = load_state_yaml(state_path)
    state.milestone("research").current_run = 1
    update_milestone_status(state, "research", MilestoneStatus.COMPLETED)
    save_state_yaml(state, state_path)

    result = _invoke(vm_start_script, output_dir=output_dir)
    assert "error" not in result, f"unexpected error: {result.get('error')}"
    milestones = {m["id"]: m for m in result["state"]["milestones"]}
    assert milestones["script"]["status"] == "in_progress"


def test_completed_research_is_reflected_in_load_state(tmp_path: Path) -> None:
    """State written to disk must be readable back with the correct status."""
    output_dir = _make_session(tmp_path, ts="20260601-000004")
    state_path = Path(output_dir) / "state.yaml"
    state = load_state_yaml(state_path)
    state.milestone("research").current_run = 1
    update_milestone_status(state, "research", MilestoneStatus.COMPLETED)
    save_state_yaml(state, state_path)

    reloaded = load_state_yaml(state_path)
    assert reloaded.milestone("research").status == MilestoneStatus.COMPLETED
