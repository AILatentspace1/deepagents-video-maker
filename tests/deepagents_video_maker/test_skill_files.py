from pathlib import Path

SKILLS_ROOT = Path(".deepagents/skills")


def test_video_researcher_skill_has_frontmatter():
    text = (SKILLS_ROOT / "video-researcher" / "SKILL.md").read_text(encoding="utf-8")
    assert text.startswith("---\n")
    assert "name: video-researcher" in text
    assert "description:" in text


def test_video_scriptwriter_skill_has_frontmatter():
    text = (SKILLS_ROOT / "video-scriptwriter" / "SKILL.md").read_text(encoding="utf-8")
    assert text.startswith("---\n")
    assert "name: video-scriptwriter" in text
    assert "description:" in text


def test_skill_wrappers_reference_virtual_paths():
    for name in ("video-researcher", "video-scriptwriter"):
        text = (SKILLS_ROOT / name / "SKILL.md").read_text(encoding="utf-8")
        for line in text.splitlines():
            if "skills/video-maker" in line:
                assert "/skills/video-maker" in line, f"{name} has non-virtual path: {line}"
            assert ".claude/skills/video-maker" not in line, (
                f"{name} still references .claude/skills/video-maker: {line}"
            )


def test_no_claude_skills_path_in_code():
    """Ensure code and config do not reference .claude/skills/video-maker."""
    import re
    src_root = Path("src")
    tests_root = Path("tests")
    scripts_root = Path("scripts")
    skill_wrappers = Path(".deepagents/skills")
    pattern = re.compile(r"\.claude/skills/video-maker")
    _this_file = Path(__file__).resolve()
    exempt_prefixes = (Path("docs/design"),)

    def check_dir(d: Path):
        if not d.exists():
            return
        for f in d.rglob("*"):
            if not f.is_file():
                continue
            if f.resolve() == _this_file:
                continue
            if "__pycache__" in f.parts:
                continue
            if any(str(f).startswith(str(e)) for e in exempt_prefixes):
                continue
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            assert not pattern.search(content), (
                f"{f} still contains .claude/skills/video-maker"
            )

    for d in (src_root, tests_root, scripts_root, skill_wrappers):
        check_dir(d)


def test_no_producer_business_skill_in_skills_root():
    if SKILLS_ROOT.exists():
        for skill_dir in SKILLS_ROOT.iterdir():
            if not skill_dir.is_dir():
                continue
            assert skill_dir.name in {"video-researcher", "video-scriptwriter"}, (
                f"unexpected skill dir {skill_dir.name}; only subagent wrappers allowed"
            )
