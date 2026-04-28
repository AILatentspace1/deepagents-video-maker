"""Train eval: all expected LangChain tools must be registered.

The better-harness outer agent may edit ``langchain_tools.py`` or
``agent.py``.  These tests guard that the full tool registry stays intact
so the Producer can call every tool it documents in its system prompt.
"""

from __future__ import annotations

from deepagents_video_maker.agent import build_native_tools
from deepagents_video_maker.langchain_tools import build_langchain_tools


_REQUIRED_TOOLS = {
    "vm_parse_video_request",
    "vm_init_video_session",
    "vm_load_state",
    "vm_start_research",
    "vm_build_researcher_task",
    "vm_ratify_research",
    "vm_start_script",
    "vm_build_scriptwriter_task",
    "vm_ratify_script",
}


def _tool_names(tools) -> set[str]:
    return {getattr(t, "name", getattr(t, "__name__", "")) for t in tools}


def test_build_langchain_tools_exposes_all_required_tools() -> None:
    """build_langchain_tools() must register every tool in _REQUIRED_TOOLS."""
    names = _tool_names(build_langchain_tools())
    missing = _REQUIRED_TOOLS - names
    assert not missing, f"Missing tools in build_langchain_tools(): {sorted(missing)}"


def test_build_native_tools_exposes_all_required_tools() -> None:
    """build_native_tools() (used by the agent factory) must expose all tools."""
    names = _tool_names(build_native_tools())
    missing = _REQUIRED_TOOLS - names
    assert not missing, f"Missing tools in build_native_tools(): {sorted(missing)}"


def test_each_tool_has_a_name_attribute() -> None:
    """Every tool must carry a .name attribute (LangChain contract)."""
    for tool in build_langchain_tools():
        name = getattr(tool, "name", None)
        assert name, f"tool {tool!r} is missing a .name attribute"
        assert isinstance(name, str), f"tool.name must be str, got {type(name)}"


def test_each_tool_has_a_description() -> None:
    """Every tool must have a non-empty docstring / description."""
    for tool in build_langchain_tools():
        desc = getattr(tool, "description", None) or getattr(tool, "__doc__", None)
        assert desc and desc.strip(), (
            f"tool '{getattr(tool, 'name', tool)}' is missing a description"
        )
