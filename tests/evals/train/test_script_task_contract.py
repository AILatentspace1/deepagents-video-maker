"""Train eval: scriptwriter task description must expose the full I/O contract.

The better-harness outer agent may edit ``langchain_tools.py`` or
``skills/video-maker/agents/scriptwriter.md``.  These tests guard that the
resulting task description still carries the fields the Scriptwriter subagent
depends on.
"""

from __future__ import annotations

from pathlib import Path

from deepagents_video_maker.langchain_tools import (
    vm_build_scriptwriter_task,
    vm_init_video_session,
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


def _make_session_with_research_done(tmp_path: Path, *, topic: str = "LLM benchmark 2026", ts: str = "20260201-000000") -> str:
    """Create a session with the research milestone already completed."""
    init = _invoke(
        vm_init_video_session,
        topic=topic,
        source="local-file",
        local_file="/docs/arch.md",
        root_dir=str(tmp_path),
        timestamp=ts,
    )
    output_dir = init["output_dir"]

    # Mark research as completed so we can advance to script.
    state_path = Path(output_dir) / "state.yaml"
    state = load_state_yaml(state_path)
    state.milestone("research").current_run = 1
    update_milestone_status(state, "research", MilestoneStatus.COMPLETED)
    save_state_yaml(state, state_path)

    _invoke(vm_start_script, output_dir=output_dir)
    return output_dir


def test_scriptwriter_task_has_input_contract(tmp_path: Path) -> None:
    """Scriptwriter task description must include an 'Input contract' block."""
    output_dir = _make_session_with_research_done(tmp_path, ts="20260201-000000")
    task = _invoke(vm_build_scriptwriter_task, output_dir=output_dir, run_number=1)

    desc = task["description"]
    assert "Input contract" in desc, "description must contain 'Input contract'"


def test_scriptwriter_task_has_output_contract(tmp_path: Path) -> None:
    """Scriptwriter task description must include an 'Output contract' block."""
    output_dir = _make_session_with_research_done(tmp_path, ts="20260201-000001")
    task = _invoke(vm_build_scriptwriter_task, output_dir=output_dir, run_number=1)

    desc = task["description"]
    assert "Output contract" in desc, "description must contain 'Output contract'"


def test_scriptwriter_task_subagent_type(tmp_path: Path) -> None:
    """vm_build_scriptwriter_task must return subagent_type='scriptwriter'."""
    output_dir = _make_session_with_research_done(tmp_path, ts="20260201-000002")
    task = _invoke(vm_build_scriptwriter_task, output_dir=output_dir, run_number=1)

    assert task["subagent_type"] == "scriptwriter"


def test_scriptwriter_task_embeds_topic(tmp_path: Path) -> None:
    """Scriptwriter task description must embed the specific topic string."""
    topic = "Serverless architecture patterns"
    output_dir = _make_session_with_research_done(tmp_path, topic=topic, ts="20260201-000003")
    task = _invoke(vm_build_scriptwriter_task, output_dir=output_dir, run_number=1)

    assert topic in task["description"], "task description must embed the topic"


def test_scriptwriter_task_run_dir_is_correct(tmp_path: Path) -> None:
    """run_dir must be nested under artifacts/script/run-{N}."""
    output_dir = _make_session_with_research_done(tmp_path, ts="20260201-000004")
    task = _invoke(vm_build_scriptwriter_task, output_dir=output_dir, run_number=1)

    run_dir = Path(task["run_dir"])
    assert run_dir.parts[-1] == "run-1", f"expected run-1, got {run_dir.parts[-1]}"
    assert "script" in run_dir.parts, "run_dir must be under 'script' artifact dir"
