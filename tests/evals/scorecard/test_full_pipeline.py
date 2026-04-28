"""Scorecard eval: full research → script pipeline must succeed end-to-end.

Scorecard evals are run as the final validation step.  They exercise the
complete happy path so the harness can confirm that an optimised agent
still works correctly from start to finish.
"""

from __future__ import annotations

import json
from pathlib import Path

from deepagents_video_maker.langchain_tools import (
    vm_build_researcher_task,
    vm_build_scriptwriter_task,
    vm_init_video_session,
    vm_ratify_research,
    vm_ratify_script,
    vm_start_research,
    vm_start_script,
)
from deepagents_video_maker.models import MilestoneStatus


def _invoke(tool, **kwargs):
    if hasattr(tool, "invoke"):
        return tool.invoke(kwargs)
    return tool(**kwargs)


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

_VALID_RESEARCH = (
    "# Research: Full Pipeline\n\n"
    "## One — Core facts\n\n" + ("Agents automate complex workflows. " * 30) + "\n\n"
    "## Two — Data\n\n" + ("Usage grew 4x in 2025. " * 30) + "\n\n"
    "## Three — Visuals\n\n" + ("Diagrams show multi-agent orchestration. " * 30) + "\n"
)

_VALID_SCRIPT = (
    "## Scene 1\n"
    "type: narration\n"
    "narration: Agents are reshaping software.\n"
    "scene_intent: hook\n"
    "content_brief: Open with a compelling statement about AI agents.\n\n"
    "## Scene 2\n"
    "type: data_card\n"
    "narration: Usage grew 4x last year.\n"
    "scene_intent: development\n"
    "content_brief: Show growth chart.\n"
)

_VALID_MANIFEST = json.dumps({
    "scenes": [
        {"id": "s1", "narration": "Agents are reshaping software.", "duration": 5},
        {"id": "s2", "narration": "Usage grew 4x last year.", "duration": 5},
    ]
})


def test_full_research_to_script_pipeline(tmp_path: Path) -> None:
    """Full pipeline: init → research → ratify → script → ratify must all pass."""

    # 1. Init session
    init = _invoke(
        vm_init_video_session,
        topic="Full pipeline test",
        source="local-file",
        local_file="/docs/arch.md",
        root_dir=str(tmp_path),
        timestamp="20260701-000000",
    )
    output_dir = init["output_dir"]
    assert "output_dir" in init

    # 2. Start research milestone
    started_r = _invoke(vm_start_research, output_dir=output_dir)
    assert started_r["run"]["run_number"] == 1
    milestones_r = {m["id"]: m for m in started_r["state"]["milestones"]}
    assert milestones_r["research"]["status"] == "in_progress"

    # 3. Build researcher task (contract check)
    task_r = _invoke(vm_build_researcher_task, output_dir=output_dir, run_number=1)
    assert task_r["subagent_type"] == "researcher"
    assert "Output contract" in task_r["description"]

    # 4. Simulate researcher writing research.md
    run_dir_r = Path(task_r["run_dir"])
    run_dir_r.mkdir(parents=True, exist_ok=True)
    (run_dir_r / "research.md").write_text(_VALID_RESEARCH, encoding="utf-8")

    # 5. Ratify research
    ratify_r = _invoke(vm_ratify_research, output_dir=output_dir, run_number=1)
    assert ratify_r["result"]["passed"] is True, f"research ratify failed: {ratify_r['result']['issues']}"

    # 6. Start script milestone
    started_s = _invoke(vm_start_script, output_dir=output_dir)
    assert "error" not in started_s, f"unexpected script start error: {started_s.get('error')}"
    milestones_s = {m["id"]: m for m in started_s["state"]["milestones"]}
    assert milestones_s["script"]["status"] == "in_progress"

    # 7. Build scriptwriter task (contract check)
    task_s = _invoke(vm_build_scriptwriter_task, output_dir=output_dir, run_number=1)
    assert task_s["subagent_type"] == "scriptwriter"

    # 8. Simulate scriptwriter writing script.md + manifest.json
    run_dir_s = Path(task_s["run_dir"])
    run_dir_s.mkdir(parents=True, exist_ok=True)
    (run_dir_s / "script.md").write_text(_VALID_SCRIPT, encoding="utf-8")
    (run_dir_s / "manifest.json").write_text(_VALID_MANIFEST, encoding="utf-8")

    # 9. Ratify script
    ratify_s = _invoke(vm_ratify_script, output_dir=output_dir, run_number=1)
    assert ratify_s["result"]["passed"] is True, f"script ratify failed: {ratify_s['result']['issues']}"

    # 10. Final state check
    milestones_final = {m["id"]: m for m in ratify_s["state"]["milestones"]}
    assert milestones_final["research"]["status"] == MilestoneStatus.COMPLETED
    assert milestones_final["script"]["status"] == MilestoneStatus.COMPLETED


def test_pipeline_state_persisted_to_disk(tmp_path: Path) -> None:
    """State must be correctly persisted to disk throughout the pipeline."""
    from deepagents_video_maker.state_store import load_state_yaml

    init = _invoke(
        vm_init_video_session,
        topic="State persistence check",
        source="local-file",
        local_file="/docs/arch.md",
        root_dir=str(tmp_path),
        timestamp="20260701-000001",
    )
    output_dir = init["output_dir"]
    _invoke(vm_start_research, output_dir=output_dir)

    run_dir = Path(output_dir) / "artifacts" / "research" / "run-1"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "research.md").write_text(_VALID_RESEARCH, encoding="utf-8")
    _invoke(vm_ratify_research, output_dir=output_dir, run_number=1)

    # Reload from disk — must reflect completed research
    state = load_state_yaml(Path(output_dir) / "state.yaml")
    assert state.milestone("research").status == MilestoneStatus.COMPLETED
