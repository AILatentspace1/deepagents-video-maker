from pathlib import Path

from deepagents_video_maker.ratify import ratify_research


def test_ratify_research_passes_for_local_file_without_url(tmp_path: Path):
    research = tmp_path / "research.md"
    research.write_text(
        "# Research\n\n"
        "## 一、核心事实\n"
        + ("内容" * 450)
        + "\n## 二、关键数据\n- data\n"
        + "\n## 三、视觉素材线索\n- visual\n",
        encoding="utf-8",
    )

    result = ratify_research(research, source="local-file")

    assert result.passed is True
    assert result.next_action == "complete_milestone"
    assert {check.id: check.passed for check in result.checks}["min_urls"] is True


def test_ratify_research_requires_url_for_websearch(tmp_path: Path):
    research = tmp_path / "research.md"
    research.write_text(
        "# Research\n\n"
        "## 一、核心事实\n"
        + ("内容" * 300)
        + "\n## 二、关键数据\n- data\n"
        + "\n## 三、视觉素材线索\n- visual\n",
        encoding="utf-8",
    )

    result = ratify_research(research, source="websearch")

    assert result.passed is False
    assert result.next_action == "retry_milestone"
    assert any("URL" in issue for issue in result.issues)


def test_ratify_research_fails_when_missing(tmp_path: Path):
    result = ratify_research(tmp_path / "missing.md", source="local-file")

    assert result.passed is False
    assert result.checks[0].id == "exists"


def test_ratify_research_fails_when_content_too_short(tmp_path: Path):
    research = tmp_path / "research.md"
    research.write_text(
        "# Research\n\n## 一、核心事实\n短\n## 二、关键数据\n- data\n## 三、视觉素材\n- visual\n",
        encoding="utf-8",
    )

    result = ratify_research(research, source="local-file")

    assert result.passed is False
    assert any(c.id == "min_chars" and not c.passed for c in result.checks)


def test_ratify_research_fails_when_too_few_headings(tmp_path: Path):
    research = tmp_path / "research.md"
    # 450 × 2 bytes = 900 chars, exceeds the 800-char minimum; only 1 h2 heading present.
    research.write_text(
        "# Research\n\n## 一、核心事实\n" + ("内容" * 450) + "\n",
        encoding="utf-8",
    )

    result = ratify_research(research, source="local-file")

    assert result.passed is False
    assert any(c.id == "min_headings" and not c.passed for c in result.checks)
