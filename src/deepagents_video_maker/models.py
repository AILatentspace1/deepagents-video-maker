"""Typed models for the DeepAgents-native Video-Maker sidecar.

Phase 1 intentionally uses stdlib dataclasses instead of a runtime dependency
such as pydantic. These models are deterministic and unit-testable without LLMs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal


class MilestoneStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    INTERRUPTED = "interrupted"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkflowStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(slots=True)
class VideoMakerGoal:
    topic: str
    source: Literal["websearch", "notebooklm", "local-file", "manual"] = "websearch"
    local_file: str = ""
    notebook_url: str = ""
    excalidraw_file: str = ""
    duration: Literal["1-3min", "3-5min", "5-10min"] = "1-3min"
    style: Literal["professional", "casual", "storytelling"] = "professional"
    aspect_ratio: Literal["16:9", "9:16", "3:4", "1:1"] = "16:9"
    quality_threshold: int = 0
    eval_mode: Literal["gan", "legacy"] = "gan"
    transition_style: str = "fade"
    template: str = "auto"
    lut_style: str = "auto"
    research_depth: str = "auto"
    visual_strategy: str = "auto"
    composition_mode: str = "auto"
    progress_bar_style: str = "minimal"
    enable_video_qa: bool = False
    bgm_file: str = ""
    bgm_volume: float = 0.15
    sfx_enabled: bool = True

    def slug(self, max_len: int = 30) -> str:
        raw = self.topic.strip().lower()
        chars = []
        prev_dash = False
        for char in raw:
            if char.isascii() and char.isalnum():
                chars.append(char)
                prev_dash = False
            elif "\u4e00" <= char <= "\u9fff":
                # Keep Chinese topics readable enough in output paths.
                chars.append(char)
                prev_dash = False
            else:
                if not prev_dash:
                    chars.append("-")
                prev_dash = True
        slug = "".join(chars).strip("-")
        return (slug or "video")[:max_len].strip("-") or "video"


@dataclass(slots=True)
class MilestoneState:
    id: str
    status: MilestoneStatus = MilestoneStatus.PENDING
    current_run: int | None = None
    retry_count: int = 0
    max_retries: int = 2
    started_at: str | None = None
    completed_at: str | None = None
    ratify: dict[str, Any] | None = None
    blocking_reason: str | None = None


@dataclass(slots=True)
class ArtifactRef:
    kind: str
    path: str
    exists: bool
    size: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_path(cls, kind: str, path: str | Path) -> "ArtifactRef":
        item = Path(path)
        return cls(
            kind=kind,
            path=str(item),
            exists=item.exists(),
            size=item.stat().st_size if item.exists() and item.is_file() else 0,
        )


@dataclass(slots=True)
class RatifyCheck:
    id: str
    passed: bool
    message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RatifyResult:
    passed: bool
    checks: list[RatifyCheck]
    issues: list[str] = field(default_factory=list)
    next_action: Literal["complete_milestone", "retry_milestone", "block_for_user"] = (
        "complete_milestone"
    )


@dataclass(slots=True)
class RunInfo:
    milestone: str
    run_number: int
    run_dir: str


@dataclass(slots=True)
class VideoMakerState:
    output_dir: str
    workflow_status: WorkflowStatus = WorkflowStatus.IN_PROGRESS
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    milestones: list[MilestoneState] = field(default_factory=list)
    artifacts: dict[str, ArtifactRef] = field(default_factory=dict)
    todos: list[dict[str, str]] = field(default_factory=list)

    def milestone(self, milestone_id: str) -> MilestoneState:
        for item in self.milestones:
            if item.id == milestone_id:
                return item
        raise KeyError(f"unknown milestone: {milestone_id}")


@dataclass(slots=True)
class EvalSample:
    """A single (script, score, suggestions) training data entry produced by the GAN Evaluator.

    Accumulated during Phase 1 inference-time iteration; used as training data
    for Phase 2 Generator fine-tuning and Phase 3 Evaluator fine-tuning.
    """

    session_id: str
    topic: str
    style: str
    duration: str
    eval_round: int
    script_text: str
    eval_score: float
    eval_pass: bool
    dimensions: list[dict[str, Any]] = field(default_factory=list)
    iteration_fixes: list[dict[str, Any]] = field(default_factory=list)
    contract_violations: list[dict[str, Any]] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
