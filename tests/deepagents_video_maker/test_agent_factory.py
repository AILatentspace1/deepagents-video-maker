from deepagents_video_maker.agent import (
    SUBAGENT_NAMES,
    build_native_tools,
    build_subagents,
)


def test_build_subagents_loads_all_native_prompts():
    subagents = build_subagents()

    assert [item["name"] for item in subagents] == SUBAGENT_NAMES
    for item in subagents:
        assert item["description"]
        assert "Input contract" in item["system_prompt"]
        assert "Output contract" in item["system_prompt"]


def test_build_native_tools_exposes_controller_protocol_tools():
    tools = build_native_tools()
    names = {getattr(tool, "name", getattr(tool, "__name__", "")) for tool in tools}

    assert "vm_parse_video_request" in names
    assert "vm_init_video_session" in names
    assert "vm_start_research" in names
    assert "vm_build_researcher_task" in names
    assert "vm_ratify_research" in names



def test_main_agent_does_not_load_business_skills():
    """Producer must stay controller-only; business skills go to subagents."""
    from deepagents_video_maker import agent as agent_mod

    paths = getattr(agent_mod, "PROJECT_SKILLS_PATHS", [])
    assert paths == [], f"main agent must not load skills, got {paths}"


def test_each_subagent_carries_its_own_skill():
    from pathlib import Path

    subs = build_subagents()
    by_name = {s["name"]: s for s in subs}
    assert set(by_name) == {"researcher", "scriptwriter"}

    rs = by_name["researcher"]["skills"]
    assert len(rs) == 1
    assert "video-researcher" in rs[0]
    assert "video-maker" not in Path(rs[0]).name

    ss = by_name["scriptwriter"]["skills"]
    assert len(ss) == 1
    assert "video-scriptwriter" in ss[0]
    assert "video-maker" not in Path(ss[0]).name


def test_create_video_maker_agent_smoke(tmp_path):
    pytest = __import__("pytest")
    pytest.importorskip("deepagents")
    from deepagents_video_maker.agent import create_video_maker_agent

    agent = create_video_maker_agent(
        model="anthropic:claude-sonnet-4-5-20250929",
        project_root=tmp_path,
    )
    assert agent is not None
