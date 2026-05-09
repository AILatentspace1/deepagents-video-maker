from deepagents_video_maker.agent import (
    SUBAGENT_NAMES,
    build_native_tools,
    build_subagents,
)


def test_build_subagents_loads_v2_scriptwriter_prompt():
    subagents = build_subagents()

    assert [item["name"] for item in subagents] == SUBAGENT_NAMES == [
        "scriptwriter",
        "remotion-builder",
    ]
    assert "Input contract" in subagents[0]["system_prompt"]
    assert "Output contract" in subagents[0]["system_prompt"]
    assert "Remotion Builder" in subagents[1]["system_prompt"]


def test_build_native_tools_exposes_v2_controller_protocol_tools():
    tools = build_native_tools()
    names = {getattr(tool, "name", getattr(tool, "__name__", "")) for tool in tools}

    assert "vm_parse_video_request" in names
    assert "vm_init_video_session" in names
    assert "vm_start_source_intake" in names
    assert "vm_ratify_source_intake" in names
    assert "vm_start_script" in names
    assert "vm_build_scriptwriter_task" in names
    assert "vm_ratify_script" in names
    assert "vm_start_build_scenes" in names
    assert "vm_build_remotion_task" in names
    assert "vm_ratify_build_scenes" in names
    assert "vm_start_render_package" in names
    assert "vm_package_render_output" in names
    assert "vm_ratify_render_package" in names
    assert "vm_start_research" not in names


def test_main_agent_does_not_load_business_skills():
    from deepagents_video_maker import agent as agent_mod

    paths = getattr(agent_mod, "PROJECT_SKILLS_PATHS", [])
    assert paths == [], f"main agent must not load skills, got {paths}"


def test_scriptwriter_carries_v2_skill_only():
    subs = build_subagents()
    assert len(subs) == 2
    assert len(subs[0]["skills"]) == 1
    assert "video-maker-v2-scriptwriter" in subs[0]["skills"][0]
    assert len(subs[1]["skills"]) == 1
    assert "video-maker-v2-remotion-builder" in subs[1]["skills"][0]


def test_create_video_maker_agent_smoke(tmp_path):
    pytest = __import__("pytest")
    pytest.importorskip("deepagents")
    from deepagents_video_maker.agent import create_video_maker_agent

    agent = create_video_maker_agent(
        model="anthropic:claude-sonnet-4-5-20250929",
        project_root=tmp_path,
    )
    assert agent is not None
