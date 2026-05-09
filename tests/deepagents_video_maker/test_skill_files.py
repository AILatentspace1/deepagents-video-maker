from pathlib import Path

SKILLS_ROOT = Path(".deepagents/skills")
PROJECT_SKILL = Path("skills/video-maker-v2")


def test_video_maker_v2_project_skill_exists():
    text = (PROJECT_SKILL / "SKILL.md").read_text(encoding="utf-8")
    assert text.startswith("---\n")
    assert "name: video-maker-v2" in text
    assert (PROJECT_SKILL / "references" / "workflow-contract.md").is_file()
    assert (PROJECT_SKILL / "agents" / "scriptwriter.md").is_file()


def test_v2_scriptwriter_wrapper_has_frontmatter():
    text = (SKILLS_ROOT / "video-maker-v2-scriptwriter" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    assert text.startswith("---\n")
    assert "name: video-maker-v2-scriptwriter" in text
    assert "/skills/video-maker-v2/agents/scriptwriter.md" in text


def test_v2_remotion_builder_wrapper_has_frontmatter():
    text = (SKILLS_ROOT / "video-maker-v2-remotion-builder" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    assert text.startswith("---\n")
    assert "name: video-maker-v2-remotion-builder" in text
    assert "/skills/video-maker-v2/agents/remotion-builder.md" in text


def test_legacy_v1_skill_entries_are_removed():
    assert not Path("skills/video-maker").exists()
    assert not (SKILLS_ROOT / "video-researcher").exists()
    assert not (SKILLS_ROOT / "video-scriptwriter").exists()


def test_no_legacy_v1_skill_path_in_code():
    import re

    pattern = re.compile(r"skills/video-maker(?!-v2)")
    for root in (Path("src"), Path("scripts"), Path(".deepagents/skills")):
        if not root.exists():
            continue
        for f in root.rglob("*"):
            if not f.is_file() or "__pycache__" in f.parts:
                continue
            content = f.read_text(encoding="utf-8", errors="ignore")
            assert not pattern.search(content), f"{f} still references legacy video-maker"


def test_only_v2_subagent_wrapper_in_deepagents_skills():
    assert {p.name for p in SKILLS_ROOT.iterdir() if p.is_dir()} == {
        "video-maker-v2-scriptwriter",
        "video-maker-v2-remotion-builder",
    }


def test_harness_and_package_scripts_do_not_reference_removed_v1_or_evals():
    import json

    package = json.loads(Path("package.json").read_text(encoding="utf-8"))
    scripts_text = json.dumps(package.get("scripts", {}))
    harness_text = Path("harness/video-maker-minimal.toml").read_text(encoding="utf-8")

    combined = scripts_text + "\n" + harness_text
    assert "skills/video-maker/agents/scriptwriter.md" not in combined
    assert "tests/evals" not in combined
    assert "scripts/video_to_golden.py" not in combined
    assert "skills/video-maker-v2/agents/scriptwriter.md" in harness_text


def test_skill_documents_audio_as_optional_until_native_audio_milestone_exists():
    text = (PROJECT_SKILL / "SKILL.md").read_text(encoding="utf-8")

    assert "Generate Audio (optional)" in text
    assert (
        "native runnable path is Source Intake → Script → user script review → "
        "Build Remotion Project → Render & Package"
    ) in text
