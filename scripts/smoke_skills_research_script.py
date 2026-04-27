"""Manual smoke for DeepAgents-native research+script controller tools.

Default mode is deterministic and does not call an LLM: it exercises the same
typed tools/artifact gates that the Producer must use, writes minimal valid
artifacts, and verifies state.yaml plus ratify evidence files.

Use --reuse-output with --delete-research to validate retry behavior on an
existing output directory.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
os.environ.setdefault("ORCHESTRATOR_SKILLS_ROOT", str(PROJECT_ROOT))


def load_env_files() -> None:
    """Load simple KEY=VALUE pairs before LangSmith tracing initializes."""

    for env_path in [PROJECT_ROOT / ".env"]:
        if not env_path.exists():
            continue
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key.startswith("LANGSMITH_") or key.startswith("LANGCHAIN_"):
                os.environ[key] = value
            else:
                os.environ.setdefault(key, value)
    if os.environ.get("LANGSMITH_TRACING", "").lower() == "true":
        os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
        # Smoke scripts exit quickly; make callback flushing synchronous.
        os.environ.setdefault("LANGCHAIN_CALLBACKS_BACKGROUND", "false")


def _traceable(name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    try:
        from langsmith import traceable

        return traceable(
            name=name,
            project_name=os.environ.get("LANGSMITH_PROJECT") or None,
            metadata={"smoke": "skills_research_script"},
        )
    except Exception:
        return lambda func: func

from deepagents_video_maker.langchain_tools import (  # noqa: E402
    vm_build_researcher_task,
    vm_build_scriptwriter_task,
    vm_init_video_session,
    vm_ratify_research,
    vm_ratify_script,
    vm_start_research,
    vm_start_script,
)


def _invoke(tool, **kwargs):
    if hasattr(tool, "invoke"):
        return tool.invoke(kwargs)
    return tool(**kwargs)


def _milestone_status(state_data: dict, milestone_id: str) -> str:
    return next(m["status"] for m in state_data["milestones"] if m["id"] == milestone_id)


def _milestone_retry(state_data: dict, milestone_id: str) -> int:
    return int(next(m["retry_count"] for m in state_data["milestones"] if m["id"] == milestone_id))


@_traceable("skills_research_script_smoke")
def run_smoke(args: argparse.Namespace) -> Path:
    topic = "skills research script smoke"
    if args.reuse_output:
        output_dir = Path(args.reuse_output)
    else:
        init = _invoke(
            vm_init_video_session,
            topic=topic,
            source="local-file",
            local_file="/docs/ARCHITECTURE-VIDEO-MAKER.md",
            duration="1-3min",
            style="professional",
            aspect_ratio="16:9",
            root_dir=str(PROJECT_ROOT),
            timestamp=args.timestamp,
        )
        output_dir = Path(init["output_dir"])

    if args.delete_research:
        research = output_dir / "artifacts" / "research" / "run-1" / "research.md"
        research.unlink(missing_ok=True)
        ratified = _invoke(
            vm_ratify_research,
            output_dir=str(output_dir),
            run_number=1,
            topic=topic,
            source="local-file",
            local_file="/docs/ARCHITECTURE-VIDEO-MAKER.md",
        )
        state_data = yaml.safe_load((output_dir / "state.yaml").read_text(encoding="utf-8"))
        assert ratified["result"]["passed"] is False
        assert _milestone_retry(state_data, "research") > 0 or _milestone_status(
            state_data, "research"
        ) == "blocked"
        print(f"OK failure-path retry validated: {output_dir}")
        return output_dir

    _invoke(vm_start_research, output_dir=str(output_dir))
    research_task = _invoke(
        vm_build_researcher_task,
        output_dir=str(output_dir),
        run_number=1,
        topic=topic,
        source="local-file",
        local_file="/docs/ARCHITECTURE-VIDEO-MAKER.md",
    )
    research_path = Path(research_task["run_dir"]) / "research.md"
    research_path.write_text(
        "# Research\n\n## A\n" + ("内容" * 450) + "\n## B\nx\n## C\nx\n",
        encoding="utf-8",
    )
    assert _invoke(
        vm_ratify_research,
        output_dir=str(output_dir),
        run_number=1,
        topic=topic,
        source="local-file",
        local_file="/docs/ARCHITECTURE-VIDEO-MAKER.md",
    )["result"]["passed"]

    _invoke(vm_start_script, output_dir=str(output_dir))
    script_task = _invoke(
        vm_build_scriptwriter_task,
        output_dir=str(output_dir),
        run_number=1,
        topic=topic,
        source="local-file",
        local_file="/docs/ARCHITECTURE-VIDEO-MAKER.md",
    )
    script_dir = Path(script_task["run_dir"])
    (script_dir / "script.md").write_text(
        "## Scene 1\n"
        "type: narration\n"
        "narration: hello\n"
        "scene_intent: hook\n"
        "content_brief: brief\n",
        encoding="utf-8",
    )
    (script_dir / "manifest.json").write_text(
        json.dumps({"scenes": [{"id": "s1", "narration": "hello", "duration": 5}]}),
        encoding="utf-8",
    )
    assert _invoke(
        vm_ratify_script,
        output_dir=str(output_dir),
        run_number=1,
        topic=topic,
        source="local-file",
        local_file="/docs/ARCHITECTURE-VIDEO-MAKER.md",
    )["result"]["passed"]

    state_data = yaml.safe_load((output_dir / "state.yaml").read_text(encoding="utf-8"))
    assert _milestone_status(state_data, "research") == "completed"
    assert _milestone_status(state_data, "script") == "completed"
    assert (output_dir / "ratify" / "research-run-1.json").exists()
    assert (output_dir / "ratify" / "script-run-1.json").exists()
    print(f"OK research+script smoke passed: {output_dir}")
    return output_dir


def main() -> None:
    load_env_files()
    parser = argparse.ArgumentParser()
    parser.add_argument("--reuse-output", default=None, help="Reuse existing output dir.")
    parser.add_argument("--delete-research", action="store_true", help="Delete research.md first.")
    parser.add_argument("--timestamp", default="20260426-000000")
    args = parser.parse_args()
    output_dir = run_smoke(args)
    project = os.environ.get("LANGSMITH_PROJECT", "(unset)")
    tracing = os.environ.get("LANGSMITH_TRACING", "(unset)")
    print(f"LangSmith tracing: {tracing}; project: {project}; trace name: skills_research_script_smoke")
    print(f"Smoke output_dir: {output_dir}")


if __name__ == "__main__":
    main()
