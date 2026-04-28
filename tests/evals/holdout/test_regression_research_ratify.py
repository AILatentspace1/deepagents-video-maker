"""Holdout eval: research ratify must reject malformed or insufficient reports.

These are regression guards.  If the better-harness outer agent proposes an
edit that breaks the research quality gates, these tests will fail and the
harness will discard the proposal.
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


def _make_session(tmp_path: Path, *, ts: str) -> str:
    init = _invoke(
        vm_init_video_session,
        topic="Regression topic",
        source="local-file",
        local_file="/docs/arch.md",
        root_dir=str(tmp_path),
        timestamp=ts,
    )
    return init["output_dir"]


def _write_research(output_dir: str, content: str, *, run: int = 1) -> None:
    run_dir = Path(output_dir) / "artifacts" / "research" / f"run-{run}"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "research.md").write_text(content, encoding="utf-8")


def test_empty_research_file_fails_ratify(tmp_path: Path) -> None:
    """An empty research.md must fail the ratify gate."""
    output_dir = _make_session(tmp_path, ts="20260401-000000")
    _invoke(vm_start_research, output_dir=output_dir)
    _write_research(output_dir, "")

    result = _invoke(vm_ratify_research, output_dir=output_dir, run_number=1)
    assert result["result"]["passed"] is False, "empty research.md must fail ratify"


def test_short_research_file_fails_ratify(tmp_path: Path) -> None:
    """A research.md with fewer than 800 chars must fail the min_chars gate."""
    output_dir = _make_session(tmp_path, ts="20260401-000001")
    _invoke(vm_start_research, output_dir=output_dir)
    # < 800 chars, has headings, but too short.
    _write_research(output_dir, "## A\nshort\n## B\ntext\n## C\nhere\n")

    result = _invoke(vm_ratify_research, output_dir=output_dir, run_number=1)
    assert result["result"]["passed"] is False, "short research.md must fail min_chars gate"
    issues = result["result"]["issues"]
    assert any("char_count" in issue or "min_chars" in issue for issue in issues), (
        f"expected a min_chars issue, got: {issues}"
    )


def test_research_without_headings_fails_ratify(tmp_path: Path) -> None:
    """A research.md with no H2 headings must fail the min_headings gate."""
    output_dir = _make_session(tmp_path, ts="20260401-000002")
    _invoke(vm_start_research, output_dir=output_dir)
    # > 800 chars but no ## headings.
    _write_research(output_dir, "Content without headings. " * 50)

    result = _invoke(vm_ratify_research, output_dir=output_dir, run_number=1)
    assert result["result"]["passed"] is False, "research.md without headings must fail ratify"
    issues = result["result"]["issues"]
    assert any("heading" in issue.lower() for issue in issues), (
        f"expected a heading-related issue, got: {issues}"
    )


def test_missing_research_file_fails_ratify(tmp_path: Path) -> None:
    """A missing research.md must fail the 'exists' gate."""
    output_dir = _make_session(tmp_path, ts="20260401-000003")
    _invoke(vm_start_research, output_dir=output_dir)
    # Do NOT write research.md.

    result = _invoke(vm_ratify_research, output_dir=output_dir, run_number=1)
    assert result["result"]["passed"] is False, "missing research.md must fail ratify"
    issues = result["result"]["issues"]
    assert any("exists" in issue.lower() for issue in issues), (
        f"expected an 'exists' issue, got: {issues}"
    )
