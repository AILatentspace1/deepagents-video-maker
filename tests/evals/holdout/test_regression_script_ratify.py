"""Holdout eval: script ratify must reject malformed script / manifest files.

These are regression guards.  If the better-harness outer agent proposes an
edit that weakens the script quality gates, these tests will fail and the
harness will discard the proposal.
"""

from __future__ import annotations

import json
from pathlib import Path

from deepagents_video_maker.langchain_tools import (
    vm_init_video_session,
    vm_ratify_script,
    vm_start_script,
)
from deepagents_video_maker.models import MilestoneStatus
from deepagents_video_maker.state_store import (
    load_state_yaml,
    save_state_yaml,
    update_milestone_status,
)


def _invoke(tool, **kwargs):
    if hasattr(tool, "invoke"):
        return tool.invoke(kwargs)
    return tool(**kwargs)


def _make_session_ready_for_script(tmp_path: Path, *, ts: str) -> tuple[str, Path]:
    """Return (output_dir, run_dir) with research already completed."""
    init = _invoke(
        vm_init_video_session,
        topic="Script regression",
        source="local-file",
        local_file="/docs/arch.md",
        root_dir=str(tmp_path),
        timestamp=ts,
    )
    output_dir = init["output_dir"]

    state_path = Path(output_dir) / "state.yaml"
    state = load_state_yaml(state_path)
    state.milestone("research").current_run = 1
    update_milestone_status(state, "research", MilestoneStatus.COMPLETED)
    save_state_yaml(state, state_path)

    started = _invoke(vm_start_script, output_dir=output_dir)
    run_dir = Path(started["run"]["run_dir"])
    run_dir.mkdir(parents=True, exist_ok=True)
    return output_dir, run_dir


def test_missing_script_file_fails_ratify(tmp_path: Path) -> None:
    """Ratify must fail when script.md is absent."""
    output_dir, run_dir = _make_session_ready_for_script(tmp_path, ts="20260501-000000")
    # Write only manifest, omit script.md.
    (run_dir / "manifest.json").write_text('{"scenes":[{"id":"s1","narration":"x","duration":5}]}')

    result = _invoke(vm_ratify_script, output_dir=output_dir, run_number=1)
    assert result["result"]["passed"] is False


def test_missing_manifest_fails_ratify(tmp_path: Path) -> None:
    """Ratify must fail when manifest.json is absent."""
    output_dir, run_dir = _make_session_ready_for_script(tmp_path, ts="20260501-000001")
    (run_dir / "script.md").write_text("## Scene 1\ntype: narration\nnarration: hi\nscene_intent: x\ncontent_brief: y\n")
    # Do NOT write manifest.json.

    result = _invoke(vm_ratify_script, output_dir=output_dir, run_number=1)
    assert result["result"]["passed"] is False


def test_invalid_json_manifest_fails_ratify(tmp_path: Path) -> None:
    """Ratify must fail when manifest.json is not valid JSON."""
    output_dir, run_dir = _make_session_ready_for_script(tmp_path, ts="20260501-000002")
    (run_dir / "script.md").write_text("## Scene 1\ntype: narration\nnarration: hi\nscene_intent: x\ncontent_brief: y\n")
    (run_dir / "manifest.json").write_text("{invalid json", encoding="utf-8")

    result = _invoke(vm_ratify_script, output_dir=output_dir, run_number=1)
    assert result["result"]["passed"] is False


def test_manifest_without_scenes_fails_ratify(tmp_path: Path) -> None:
    """Ratify must fail when manifest.json has no 'scenes' array."""
    output_dir, run_dir = _make_session_ready_for_script(tmp_path, ts="20260501-000003")
    (run_dir / "script.md").write_text("## Scene 1\ntype: narration\nnarration: hi\nscene_intent: x\ncontent_brief: y\n")
    (run_dir / "manifest.json").write_text(json.dumps({"metadata": {}}), encoding="utf-8")

    result = _invoke(vm_ratify_script, output_dir=output_dir, run_number=1)
    assert result["result"]["passed"] is False


def test_duplicate_scene_ids_fail_ratify(tmp_path: Path) -> None:
    """Ratify must fail when manifest.json contains duplicate scene IDs."""
    output_dir, run_dir = _make_session_ready_for_script(tmp_path, ts="20260501-000004")
    (run_dir / "script.md").write_text(
        "## Scene 1\ntype: narration\nnarration: hi\nscene_intent: x\ncontent_brief: y\n"
        "## Scene 2\ntype: narration\nnarration: bye\nscene_intent: z\ncontent_brief: w\n"
    )
    (run_dir / "manifest.json").write_text(
        json.dumps({"scenes": [
            {"id": "s1", "narration": "hi", "duration": 5},
            {"id": "s1", "narration": "bye", "duration": 5},  # duplicate id
        ]}),
        encoding="utf-8",
    )

    result = _invoke(vm_ratify_script, output_dir=output_dir, run_number=1)
    assert result["result"]["passed"] is False
    issues = result["result"]["issues"]
    assert any("duplicate" in i.lower() or "unique" in i.lower() for i in issues), (
        f"expected duplicate-id issue, got: {issues}"
    )
