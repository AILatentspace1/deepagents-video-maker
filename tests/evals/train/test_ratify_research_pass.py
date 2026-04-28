"""Train eval: research ratify must pass for a well-formed research report.

The better-harness outer agent may edit ``ratify.py``,
``skills/video-maker/ratify/research-rules.md``, or
``langchain_tools.py``.  These tests confirm the happy-path gates stay intact
after any proposed edit.
"""

from __future__ import annotations

from pathlib import Path

from deepagents_video_maker.langchain_tools import (
    vm_init_video_session,
    vm_ratify_research,
    vm_start_research,
)


def _invoke(tool, **kwargs):
    if hasattr(tool, "invoke"):
        return tool.invoke(kwargs)
    return tool(**kwargs)


# A well-formed research.md with 3 H2 headings and > 800 chars.
_VALID_RESEARCH = (
    "# Research: AI Agents\n\n"
    "## One\n\n" + ("AI agents are autonomous systems. " * 30) + "\n\n"
    "## Two\n\n" + ("They use tools and memory. " * 30) + "\n\n"
    "## Three\n\n" + ("Applications span many domains. " * 30) + "\n"
)


def _make_session(tmp_path: Path, *, topic: str = "AI Agents", ts: str) -> str:
    init = _invoke(
        vm_init_video_session,
        topic=topic,
        source="local-file",
        local_file="/docs/arch.md",
        root_dir=str(tmp_path),
        timestamp=ts,
    )
    return init["output_dir"]


def test_valid_research_passes_ratify(tmp_path: Path) -> None:
    """A well-formed research.md with 3 headings and >800 chars must pass."""
    output_dir = _make_session(tmp_path, ts="20260301-000000")
    _invoke(vm_start_research, output_dir=output_dir)

    run_dir = Path(output_dir) / "artifacts" / "research" / "run-1"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "research.md").write_text(_VALID_RESEARCH, encoding="utf-8")

    result = _invoke(vm_ratify_research, output_dir=output_dir, run_number=1)
    assert result["result"]["passed"] is True, f"expected pass, got issues: {result['result']['issues']}"


def test_valid_research_marks_milestone_completed(tmp_path: Path) -> None:
    """Passing ratify must set research milestone status to 'completed'."""
    output_dir = _make_session(tmp_path, ts="20260301-000001")
    _invoke(vm_start_research, output_dir=output_dir)

    run_dir = Path(output_dir) / "artifacts" / "research" / "run-1"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "research.md").write_text(_VALID_RESEARCH, encoding="utf-8")

    result = _invoke(vm_ratify_research, output_dir=output_dir, run_number=1)
    milestones = {m["id"]: m for m in result["state"]["milestones"]}
    assert milestones["research"]["status"] == "completed", (
        f"expected completed, got {milestones['research']['status']}"
    )


def test_valid_research_ratify_emits_no_issues(tmp_path: Path) -> None:
    """Passing ratify must return an empty issues list."""
    output_dir = _make_session(tmp_path, ts="20260301-000002")
    _invoke(vm_start_research, output_dir=output_dir)

    run_dir = Path(output_dir) / "artifacts" / "research" / "run-1"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "research.md").write_text(_VALID_RESEARCH, encoding="utf-8")

    result = _invoke(vm_ratify_research, output_dir=output_dir, run_number=1)
    assert result["result"]["issues"] == [], (
        f"expected no issues, got {result['result']['issues']}"
    )
