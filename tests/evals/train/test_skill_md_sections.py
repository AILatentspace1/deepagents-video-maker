"""Train eval: Producer SKILL.md and subagent prompts must contain required sections.

The better-harness outer agent may edit ``skills/video-maker/SKILL.md`` and
``skills/video-maker/agents/*.md``.  These tests confirm the structural
contracts (e.g. required headings) are preserved after each proposal.
"""

from __future__ import annotations

from pathlib import Path

_SKILLS_ROOT = Path("skills/video-maker")


def test_producer_skill_md_has_parameter_collection_section() -> None:
    """SKILL.md must describe the parameter collection step.

    The assertion accepts both Chinese (参数收集) and English terms because
    the codebase uses Chinese for human-facing prompts while test task
    descriptions and tool contracts use English.  Both variants are valid.
    """
    text = (_SKILLS_ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert "参数收集" in text or "Parameter" in text or "parameter" in text, (
        "SKILL.md must contain a parameter collection section"
    )


def test_producer_skill_md_has_milestone_loop_section() -> None:
    """SKILL.md must describe the milestone execution loop."""
    text = (_SKILLS_ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert "里程碑" in text or "milestone" in text.lower(), (
        "SKILL.md must contain a milestone loop section"
    )


def test_producer_skill_md_has_ratify_reference() -> None:
    """SKILL.md must reference the Ratify quality gate mechanism."""
    text = (_SKILLS_ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert "Ratify" in text or "ratify" in text, (
        "SKILL.md must reference the Ratify quality gate"
    )


def test_researcher_prompt_has_output_specification() -> None:
    """Researcher agent prompt must declare an output specification (where to write research.md)."""
    text = (_SKILLS_ROOT / "agents" / "researcher.md").read_text(encoding="utf-8")
    assert "research.md" in text or "output_path" in text or "输出规范" in text, (
        "researcher.md must specify the output path or output specification section"
    )


def test_scriptwriter_prompt_has_output_specification() -> None:
    """Scriptwriter agent prompt must declare an output specification (where to write script.md)."""
    text = (_SKILLS_ROOT / "agents" / "scriptwriter.md").read_text(encoding="utf-8")
    assert "script.md" in text or "Output contract" in text or "输出" in text, (
        "scriptwriter.md must declare an output specification or Output contract"
    )


def test_research_milestone_md_exists() -> None:
    """Research milestone definition file must exist."""
    path = _SKILLS_ROOT / "milestones" / "research.md"
    assert path.exists(), f"missing milestone file: {path}"
    content = path.read_text(encoding="utf-8")
    assert len(content) > 100, "research.md milestone file appears truncated"


def test_script_milestone_md_exists() -> None:
    """Script milestone definition file must exist."""
    path = _SKILLS_ROOT / "milestones" / "script.md"
    assert path.exists(), f"missing milestone file: {path}"
    content = path.read_text(encoding="utf-8")
    assert len(content) > 100, "script.md milestone file appears truncated"


def test_research_ratify_rules_exist() -> None:
    """Research ratify rules file must exist."""
    path = _SKILLS_ROOT / "ratify" / "research-rules.md"
    assert path.exists(), f"missing ratify rules: {path}"


def test_script_ratify_rules_exist() -> None:
    """Script ratify rules file must exist."""
    path = _SKILLS_ROOT / "ratify" / "script-rules.md"
    assert path.exists(), f"missing ratify rules: {path}"
