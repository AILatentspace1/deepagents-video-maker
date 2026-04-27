from pathlib import Path

from deepagents_video_maker.langchain_tools import (
    vm_build_researcher_task,
    vm_build_scriptwriter_task,
    vm_init_video_session,
    vm_parse_video_request,
    vm_ratify_research,
    vm_ratify_script,
    vm_start_script,
    vm_start_research,
)


PROMPT = """
topic=介绍 video-maker skill
source=local-file
local_file=/docs/ARCHITECTURE-VIDEO-MAKER.md
duration=1-3min
style=professional
"""


def _invoke(tool, *args, **kwargs):
    if hasattr(tool, "invoke"):
        return tool.invoke(kwargs if kwargs else dict(args=args))
    return tool(*args, **kwargs)


def test_vm_parse_video_request_returns_jsonable_goal():
    result = _invoke(vm_parse_video_request, prompt=PROMPT)

    assert result["topic"] == "介绍 video-maker skill"
    assert result["source"] == "local-file"
    assert result["research_depth"] == "light"


def test_research_tool_sequence(tmp_path: Path):
    init = _invoke(
        vm_init_video_session,
        topic="介绍 video-maker skill",
        source="local-file",
        local_file="/docs/ARCHITECTURE-VIDEO-MAKER.md",
        duration="1-3min",
        style="professional",
        aspect_ratio="16:9",
        root_dir=str(tmp_path),
        timestamp="20260425-120000",
    )
    output_dir = init["output_dir"]

    started = _invoke(vm_start_research, output_dir=output_dir)
    assert started["run"]["run_number"] == 1
    assert started["state"]["milestones"][0]["status"] == "in_progress"

    task = _invoke(
        vm_build_researcher_task,
        output_dir=output_dir,
        run_number=1,
        topic="介绍 video-maker skill",
        source="local-file",
        local_file="/docs/ARCHITECTURE-VIDEO-MAKER.md",
        duration="1-3min",
        style="professional",
        aspect_ratio="16:9",
    )
    assert task["subagent_type"] == "researcher"
    assert "Output contract" in task["description"]

    research_path = Path(task["run_dir"]) / "research.md"
    research_path.write_text(
        "# Research\n\n## A\n" + ("内容" * 450) + "\n## B\nx\n## C\nx\n",
        encoding="utf-8",
    )
    ratified = _invoke(
        vm_ratify_research,
        output_dir=output_dir,
        run_number=1,
        topic="介绍 video-maker skill",
        source="local-file",
        local_file="/docs/ARCHITECTURE-VIDEO-MAKER.md",
        duration="1-3min",
        style="professional",
        aspect_ratio="16:9",
    )

    assert ratified["result"]["passed"] is True
    assert ratified["state"]["milestones"][0]["status"] == "completed"



def test_build_langchain_tools_includes_script_tools():
    from deepagents_video_maker.langchain_tools import build_langchain_tools

    names = {t.name for t in build_langchain_tools()}
    assert {"vm_load_state", "vm_start_script", "vm_build_scriptwriter_task", "vm_ratify_script"}.issubset(names)


def test_build_researcher_task_can_load_goal_from_output_dir(tmp_path: Path):
    init = _invoke(
        vm_init_video_session,
        topic="goal fallback",
        source="local-file",
        local_file="/docs/ARCHITECTURE-VIDEO-MAKER.md",
        root_dir=str(tmp_path),
        timestamp="20260427-110000",
    )
    output_dir = init["output_dir"]
    _invoke(vm_start_research, output_dir=output_dir)

    task = _invoke(vm_build_researcher_task, output_dir=output_dir, run_number=1)

    assert task["subagent_type"] == "researcher"
    assert "goal fallback" in task["description"]


def test_build_scriptwriter_task_can_load_goal_from_output_dir(tmp_path: Path):
    init = _invoke(
        vm_init_video_session,
        topic="script goal fallback",
        source="local-file",
        local_file="/docs/ARCHITECTURE-VIDEO-MAKER.md",
        root_dir=str(tmp_path),
        timestamp="20260427-110100",
    )
    output_dir = init["output_dir"]

    from deepagents_video_maker.models import MilestoneStatus
    from deepagents_video_maker.state_store import (
        load_state_yaml,
        save_state_yaml,
        update_milestone_status,
    )

    state_path = Path(output_dir) / "state.yaml"
    state = load_state_yaml(state_path)
    state.milestone("research").current_run = 1
    update_milestone_status(state, "research", MilestoneStatus.COMPLETED)
    save_state_yaml(state, state_path)
    _invoke(vm_start_script, output_dir=output_dir)

    task = _invoke(vm_build_scriptwriter_task, output_dir=output_dir, run_number=1)

    assert task["subagent_type"] == "scriptwriter"
    assert "script goal fallback" in task["description"]


def test_ratify_script_can_load_goal_from_output_dir(tmp_path: Path):
    init = _invoke(
        vm_init_video_session,
        topic="script ratify fallback",
        source="local-file",
        local_file="/docs/ARCHITECTURE-VIDEO-MAKER.md",
        root_dir=str(tmp_path),
        timestamp="20260427-110200",
    )
    output_dir = init["output_dir"]

    from deepagents_video_maker.models import MilestoneStatus
    from deepagents_video_maker.state_store import (
        load_state_yaml,
        save_state_yaml,
        update_milestone_status,
    )

    state_path = Path(output_dir) / "state.yaml"
    state = load_state_yaml(state_path)
    state.milestone("research").current_run = 1
    update_milestone_status(state, "research", MilestoneStatus.COMPLETED)
    save_state_yaml(state, state_path)
    started = _invoke(vm_start_script, output_dir=output_dir)
    run_dir = Path(started["run"]["run_dir"])
    (run_dir / "script.md").write_text(
        "## Scene 1\n"
        "type: narration\n"
        "narration: hi\n"
        "scene_intent: hook\n"
        "content_brief: brief\n",
        encoding="utf-8",
    )
    (run_dir / "manifest.json").write_text(
        '{"scenes":[{"id":"s1","narration":"hi","duration":5}]}',
        encoding="utf-8",
    )

    result = _invoke(vm_ratify_script, output_dir=output_dir, run_number=1)

    assert result["result"]["passed"] is True
