"""Deterministic request parsing and parameter derivation."""

from __future__ import annotations

import re
from typing import Any

from .models import VideoMakerGoal


_KEY_ALIASES = {
    "topic": "topic",
    "话题": "topic",
    "source": "source",
    "素材来源": "source",
    "local_file": "local_file",
    "localfile": "local_file",
    "本地文件": "local_file",
    "excalidraw_file": "excalidraw_file",
    "excalidraw": "excalidraw_file",
    "duration": "duration",
    "时长": "duration",
    "style": "style",
    "风格": "style",
    "aspectratio": "aspect_ratio",
    "aspect_ratio": "aspect_ratio",
    "画面比例": "aspect_ratio",
    "quality_threshold": "quality_threshold",
    "eval_mode": "eval_mode",
    "transition_style": "transition_style",
}


def parse_video_request(text: str) -> VideoMakerGoal:
    """Parse simple key=value / key: value prompts without an LLM."""

    values: dict[str, Any] = {}
    for raw_line in re.split(r"[\n；;,，]+", text):
        line = raw_line.strip().strip("。")
        if not line:
            continue
        match = re.match(r"^([\w\u4e00-\u9fff-]+)\s*[:=：]\s*(.+)$", line)
        if not match:
            continue
        key, value = match.group(1).strip(), match.group(2).strip().strip("；;。")
        normalized_key = _KEY_ALIASES.get(key.lower(), _KEY_ALIASES.get(key))
        if not normalized_key:
            continue
        values[normalized_key] = value

    topic = values.pop("topic", "").strip()
    if not topic:
        # Fall back to the first meaningful sentence for manual smoke use.
        topic = text.strip().splitlines()[0].strip("。；; ") if text.strip() else "Untitled video"

    if "aspectRatio" in values:
        values["aspect_ratio"] = values.pop("aspectRatio")
    if "quality_threshold" in values:
        values["quality_threshold"] = int(values["quality_threshold"])

    goal = VideoMakerGoal(topic=topic, **values)
    return derive_video_params(goal)


def derive_video_params(goal: VideoMakerGoal) -> VideoMakerGoal:
    """Apply deterministic defaults from video-maker parameter rules."""

    if goal.research_depth == "auto":
        goal.research_depth = {
            "1-3min": "light",
            "3-5min": "standard",
            "5-10min": "deep",
        }.get(goal.duration, "light")

    if goal.template == "auto":
        if goal.style == "professional":
            goal.template = "news-clean"
        elif goal.style == "casual":
            goal.template = "pastel-pop"
        elif goal.style == "storytelling":
            goal.template = "warm-story"
        else:
            goal.template = "tech-noir"

    if goal.lut_style == "auto":
        if goal.style == "professional":
            goal.lut_style = "news_neutral"
        elif goal.style == "casual":
            goal.lut_style = "docu_natural"
        elif goal.style == "storytelling":
            goal.lut_style = "warm_human"
        else:
            goal.lut_style = "tech_cool"

    if goal.visual_strategy == "auto":
        tech_markers = ["AI", "agent", "数据", "编程", "skill", "架构", "SaaS"]
        goal.visual_strategy = (
            "image_light"
            if any(marker.lower() in goal.topic.lower() for marker in tech_markers)
            else "image_heavy"
        )

    goal.progress_bar_style = "minimal"
    goal.transition_style = goal.transition_style or "fade"
    return goal
