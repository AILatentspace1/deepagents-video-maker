"""DeepAgents-native Video-Maker sidecar package."""

from .models import (
    ArtifactRef,
    MilestoneState,
    MilestoneStatus,
    RatifyCheck,
    RatifyResult,
    VideoMakerGoal,
    VideoMakerState,
)
from .agent import build_subagents, create_video_maker_agent

__all__ = [
    "ArtifactRef",
    "MilestoneState",
    "MilestoneStatus",
    "RatifyCheck",
    "RatifyResult",
    "VideoMakerGoal",
    "VideoMakerState",
    "build_subagents",
    "create_video_maker_agent",
]
