"""LangGraph entrypoint for the Video-Maker DeepAgent.

Run from this directory:

    langgraph dev

The exported `agent` graph is consumed by Deep Agents UI with assistant ID
`video-maker`.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from scripts.deepagents_video_maker import build_agent, load_env_files, resolve_model  # noqa: E402


load_env_files()

model = os.environ.get("DEEPAGENTS_MODEL", "deepseek:deepseek-v4-flash")
os.environ.setdefault("ORCHESTRATOR_SKILLS_ROOT", str(PROJECT_ROOT))

if os.environ.get("DEEPAGENTS_VIDEO_MAKER_NATIVE", "true").lower() == "true":
    from deepagents_video_maker.agent import create_video_maker_agent  # noqa: E402

    agent = create_video_maker_agent(
        resolve_model(model),
        project_root=PROJECT_ROOT,
        interrupt=False,
        checkpointer=None,
    )
else:
    agent = build_agent(
        model,
        interrupt=False,
        checkpointer=False,
    )
