"""Train eval: researcher task description must expose the full I/O contract.

The better-harness outer agent may edit ``langchain_tools.py`` or
``skills/video-maker/agents/researcher.md``.  These tests guard that the
resulting task description still carries the contract fields the Researcher
subagent depends on.
"""

from __future__ import annotations

from pathlib import Path

from deepagents_video_maker.langchain_tools import (
    vm_build_researcher_task,
    vm_init_video_session,
    vm_start_research,
)


def _invoke(tool, **kwargs):
    if hasattr(tool, "invoke"):
        return tool.invoke(kwargs)
    return tool(**kwargs)


def _make_session(tmp_path: Path, *, topic: str = "AI Agent trends 2026", ts: str = "20260101-000000") -> str:
    init = _invoke(
        vm_init_video_session,
        topic=topic,
        source="local-file",
        local_file="/docs/arch.md",
        root_dir=str(tmp_path),
        timestamp=ts,
    )
    return init["output_dir"]


def test_researcher_task_has_input_contract(tmp_path: Path) -> None:
    """Researcher task description must include an 'Input contract' block."""
    output_dir = _make_session(tmp_path, ts="20260101-000000")
    _invoke(vm_start_research, output_dir=output_dir)
    task = _invoke(vm_build_researcher_task, output_dir=output_dir, run_number=1)

    desc = task["description"]
    assert "Input contract" in desc, "description must contain 'Input contract'"
    assert "topic:" in desc, "description must list topic in input contract"
    assert "output_path:" in desc, "description must specify output_path"


def test_researcher_task_has_output_contract(tmp_path: Path) -> None:
    """Researcher task description must include an 'Output contract' block."""
    output_dir = _make_session(tmp_path, ts="20260101-000001")
    _invoke(vm_start_research, output_dir=output_dir)
    task = _invoke(vm_build_researcher_task, output_dir=output_dir, run_number=1)

    desc = task["description"]
    assert "Output contract" in desc, "description must contain 'Output contract'"
    assert "research_path:" in desc, "output contract must include research_path"
    assert "summary:" in desc, "output contract must include summary"
    assert "section_count:" in desc, "output contract must include section_count"


def test_researcher_task_embeds_topic(tmp_path: Path) -> None:
    """Researcher task description must embed the specific topic string."""
    topic = "Quantum computing breakthroughs"
    output_dir = _make_session(tmp_path, topic=topic, ts="20260101-000002")
    _invoke(vm_start_research, output_dir=output_dir)
    task = _invoke(vm_build_researcher_task, output_dir=output_dir, run_number=1)

    assert topic in task["description"], "task description must embed the topic"


def test_researcher_task_subagent_type(tmp_path: Path) -> None:
    """vm_build_researcher_task must return subagent_type='researcher'."""
    output_dir = _make_session(tmp_path, ts="20260101-000003")
    _invoke(vm_start_research, output_dir=output_dir)
    task = _invoke(vm_build_researcher_task, output_dir=output_dir, run_number=1)

    assert task["subagent_type"] == "researcher"


def test_researcher_task_run_dir_is_correct(tmp_path: Path) -> None:
    """run_dir must be nested under artifacts/research/run-{N}."""
    output_dir = _make_session(tmp_path, ts="20260101-000004")
    _invoke(vm_start_research, output_dir=output_dir)
    task = _invoke(vm_build_researcher_task, output_dir=output_dir, run_number=1)

    run_dir = Path(task["run_dir"])
    assert run_dir.parts[-1] == "run-1", f"expected run-1, got {run_dir.parts[-1]}"
    assert "research" in run_dir.parts, "run_dir must be under 'research' artifact dir"
