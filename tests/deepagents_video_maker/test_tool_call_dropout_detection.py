from pathlib import Path

from deepagents_video_maker.artifacts import detect_tool_call_dropout


def test_detects_pseudo_task_without_real_tool_call(tmp_path: Path):
    missing_research = tmp_path / "research.md"
    message = {
        "content": '<sop_invocation><invoke name="task">researcher</invoke> DSML',
        "tool_calls": [],
    }

    assert (
        detect_tool_call_dropout(
            message,
            milestone_status="in_progress",
            expected_artifact=missing_research,
        )
        is True
    )


def test_no_dropout_when_real_tool_call_exists(tmp_path: Path):
    message = {
        "content": '<invoke name="task">researcher</invoke>',
        "tool_calls": [{"name": "task"}],
    }

    assert (
        detect_tool_call_dropout(
            message,
            milestone_status="in_progress",
            expected_artifact=tmp_path / "research.md",
        )
        is False
    )


def test_no_dropout_when_artifact_exists(tmp_path: Path):
    research = tmp_path / "research.md"
    research.write_text("ok", encoding="utf-8")
    message = {"content": '<invoke name="task">researcher</invoke>', "tool_calls": []}

    assert (
        detect_tool_call_dropout(
            message,
            milestone_status="in_progress",
            expected_artifact=research,
        )
        is False
    )

