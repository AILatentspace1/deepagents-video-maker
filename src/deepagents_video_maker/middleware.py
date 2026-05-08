"""LangGraph middleware for exposing video-maker progress to the web UI."""

from __future__ import annotations

import json
from typing import Any, Callable

from langchain.agents.middleware.types import (
    AgentMiddleware,
    AgentState,
    ContextT,
    ResponseT,
)
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from typing_extensions import NotRequired, TypedDict

from .ui_state import build_video_maker_ui_state


class VideoMakerUiAgentState(AgentState[ResponseT]):
    """Agent state extension consumed by `web-ui`."""

    video_maker: NotRequired[dict[str, Any]]


class VideoMakerUiStateMiddleware(AgentMiddleware[VideoMakerUiAgentState, ContextT, ResponseT]):
    """Project native tool progress into top-level LangGraph state."""

    state_schema = VideoMakerUiAgentState

    def wrap_tool_call(
        self,
        request: Any,
        handler: Callable[[Any], ToolMessage | Command[Any]],
    ) -> ToolMessage | Command[Any]:
        result = handler(request)
        try:
            return _attach_ui_state(result, _extract_output_dir(request, result))
        except Exception:
            return result

    async def awrap_tool_call(
        self,
        request: Any,
        handler: Callable[[Any], Any],
    ) -> ToolMessage | Command[Any]:
        result = await handler(request)
        try:
            return _attach_ui_state(result, _extract_output_dir(request, result))
        except Exception:
            return result


def _attach_ui_state(result: ToolMessage | Command[Any], output_dir: str | None) -> ToolMessage | Command[Any]:
    if not output_dir:
        return result
    try:
        video_maker = build_video_maker_ui_state(output_dir)
    except Exception:
        # Never break the tool call itself because the UI projection failed.
        return result

    if isinstance(result, Command):
        update = dict(result.update or {})
        update["video_maker"] = video_maker
        return Command(
            graph=result.graph,
            update=update,
            resume=result.resume,
            goto=result.goto,
        )
    return Command(update={"messages": [result], "video_maker": video_maker})


def _extract_output_dir(request: Any, result: ToolMessage | Command[Any]) -> str | None:
    name = request.tool_call.get("name", "")
    if not name.startswith("vm_"):
        return None
    args = request.tool_call.get("args") or {}
    output_dir = args.get("output_dir")
    if isinstance(output_dir, str) and output_dir:
        return output_dir

    message = _first_tool_message(result)
    if message is None:
        return None
    payload = _json_content(message.content)
    if isinstance(payload, dict):
        value = payload.get("output_dir")
        if isinstance(value, str) and value:
            return value
        state = payload.get("state")
        if isinstance(state, dict) and isinstance(state.get("output_dir"), str):
            return state["output_dir"]
    return None


def _first_tool_message(result: ToolMessage | Command[Any]) -> ToolMessage | None:
    if isinstance(result, ToolMessage):
        return result
    update = result.update or {}
    for message in update.get("messages", []):
        if isinstance(message, ToolMessage):
            return message
    return None


def _json_content(content: Any) -> Any:
    if isinstance(content, str):
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return None
    return content
