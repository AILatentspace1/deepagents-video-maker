"""Scorecard eval: Producer skill file and harness surfaces must meet quality bar.

These tests perform final validation of the harness surfaces as a whole —
confirming that all configurable surfaces referenced in ``harness/video-maker.toml``
are present, non-empty, and structurally sound.
"""

from __future__ import annotations

from pathlib import Path

_SKILLS_ROOT = Path("skills/video-maker")
_HARNESS_TOML = Path("harness/video-maker.toml")
_SRC_ROOT = Path("src/deepagents_video_maker")


def test_harness_toml_exists() -> None:
    """harness/video-maker.toml must exist."""
    assert _HARNESS_TOML.exists(), f"missing harness config: {_HARNESS_TOML}"


def test_harness_toml_references_inner_agent() -> None:
    """harness/video-maker.toml must reference the inner agent entry point."""
    text = _HARNESS_TOML.read_text(encoding="utf-8")
    assert "create_video_maker_agent" in text or "inner_agent" in text, (
        "harness TOML must reference the inner agent entry point"
    )


def test_harness_toml_declares_eval_sets() -> None:
    """harness/video-maker.toml must declare train and holdout eval sets."""
    text = _HARNESS_TOML.read_text(encoding="utf-8")
    assert "train" in text, "harness TOML must reference train eval set"
    assert "holdout" in text, "harness TOML must reference holdout eval set"


def test_harness_toml_declares_surfaces() -> None:
    """harness/video-maker.toml must declare at least one optimisable surface."""
    text = _HARNESS_TOML.read_text(encoding="utf-8")
    assert "surfaces" in text or "surface" in text, (
        "harness TOML must declare at least one surface"
    )


def test_producer_skill_md_non_empty() -> None:
    """SKILL.md must be non-trivially populated (> 500 chars)."""
    path = _SKILLS_ROOT / "SKILL.md"
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert len(content) > 500, f"SKILL.md appears too short ({len(content)} chars)"


def test_all_referenced_agent_prompts_exist() -> None:
    """Each agent prompt referenced in harness surfaces must exist on disk."""
    agent_prompts = [
        _SKILLS_ROOT / "agents" / "researcher.md",
        _SKILLS_ROOT / "agents" / "scriptwriter.md",
    ]
    for path in agent_prompts:
        assert path.exists(), f"agent prompt missing: {path}"
        assert len(path.read_text(encoding="utf-8")) > 200, (
            f"agent prompt appears truncated: {path}"
        )


def test_langchain_tools_module_importable() -> None:
    """langchain_tools.py must be importable without errors."""
    from deepagents_video_maker.langchain_tools import build_langchain_tools  # noqa: F401

    # Check for the core tools required by the Producer rather than a hard
    # count — this way the test remains valid when new tools are added.
    _CORE_TOOLS = {
        "vm_parse_video_request",
        "vm_init_video_session",
        "vm_start_research",
        "vm_build_researcher_task",
        "vm_ratify_research",
        "vm_start_script",
        "vm_build_scriptwriter_task",
        "vm_ratify_script",
    }
    names = {getattr(t, "name", getattr(t, "__name__", "")) for t in build_langchain_tools()}
    missing = _CORE_TOOLS - names
    assert not missing, f"Missing core tools: {sorted(missing)}"


def test_agent_factory_module_importable() -> None:
    """agent.py must be importable and expose create_video_maker_agent."""
    from deepagents_video_maker.agent import create_video_maker_agent  # noqa: F401
    assert callable(create_video_maker_agent)


def test_ratify_rules_are_non_empty() -> None:
    """Both ratify rules files must be non-empty."""
    for name in ("research-rules.md", "script-rules.md"):
        path = _SKILLS_ROOT / "ratify" / name
        assert path.exists(), f"missing ratify rules: {path}"
        content = path.read_text(encoding="utf-8")
        assert len(content) > 50, f"ratify rules file appears truncated: {path}"
