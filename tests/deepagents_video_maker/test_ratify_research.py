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
