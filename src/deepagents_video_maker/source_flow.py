"""Video-maker-v2 Source Intake flow helpers."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

from .artifacts import source_manifest_path
from .models import MilestoneStatus, RatifyResult, VideoMakerGoal, VideoMakerState
from .ratify import ratify_source_manifest
from .session import create_milestone_run
from .state_store import update_milestone_status


def start_source_intake_milestone(state: VideoMakerState):
    return create_milestone_run(state, "source_intake")


def write_source_manifest(goal: VideoMakerGoal, state: VideoMakerState) -> Path:
    path = source_manifest_path(state.output_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    items = _manifest_items(goal, state=state)
    lines = [
        "# Source Manifest",
        "",
        f"source_type: {goal.source}",
        f"topic: {goal.topic}",
        f"created_at: {datetime.now().isoformat(timespec='seconds')}",
        f"root: {goal.source_folder if goal.source == 'folder' else ''}",
        "",
        "## Reading Policy",
        "- Scriptwriter must read this manifest first.",
        "- Scriptwriter chooses relevant files to read; Producer must not load the whole folder into context.",
        "- Single file >20KB: read selectively and quote only relevant passages in reasoning/output.",
        "- CSV/JSON: inspect header/schema and representative rows before deciding whether to read more.",
        "- Binary/image/audio/video: record path and intended use; do not transcribe/analyze unless explicitly needed.",
        "- If a needed claim/data/quote is not present in listed sources, mark it as unavailable; do not invent it.",
        "",
        "## Items",
        "",
    ]
    if not items and goal.source == "manual":
        lines.extend(
            [
                "### 1. manual",
                "- type: manual",
                "- path: manual",
                "- size_bytes: unknown",
                "- readable: yes",
                f"- note: {goal.topic}",
                "",
            ]
        )
    for idx, item in enumerate(items, start=1):
        lines.extend(
            [
                f"### {idx}. {item['name']}",
                f"- type: {item['type']}",
                f"- path: {item['path']}",
                f"- size_bytes: {item['size_bytes']}",
                f"- readable: {item['readable']}",
                f"- note: {item['note']}",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def ratify_and_update_source_intake(state: VideoMakerState, goal: VideoMakerGoal) -> RatifyResult:
    manifest = write_source_manifest(goal, state)
    result = ratify_source_manifest(manifest, source=goal.source)
    ratify_payload = {
        "passed": result.passed,
        "issues": result.issues,
        "checks": [
            {"id": c.id, "passed": c.passed, "message": c.message, "metadata": c.metadata}
            for c in result.checks
        ],
    }
    if result.passed:
        update_milestone_status(state, "source_intake", MilestoneStatus.COMPLETED, ratify=ratify_payload)
    else:
        milestone = state.milestone("source_intake")
        milestone.retry_count += 1
        update_milestone_status(
            state,
            "source_intake",
            MilestoneStatus.IN_PROGRESS if milestone.retry_count <= milestone.max_retries else MilestoneStatus.BLOCKED,
            blocking_reason="source manifest ratify failed",
            ratify=ratify_payload,
        )
        if milestone.status == MilestoneStatus.BLOCKED:
            result.next_action = "block_for_user"
    ratify_dir = Path(state.output_dir) / "ratify"
    ratify_dir.mkdir(parents=True, exist_ok=True)
    (ratify_dir / "source-intake.json").write_text(
        json.dumps(ratify_payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return result


def _manifest_items(
    goal: VideoMakerGoal, *, state: VideoMakerState | None = None
) -> list[dict[str, object]]:
    if goal.source == "folder" and goal.source_folder:
        root = Path(goal.source_folder)
        if not root.exists():
            return [_error_item("folder", str(root), "source folder does not exist")]
        files = [
            path
            for path in root.rglob("*")
            if path.is_file()
            and ".git" not in path.parts
            and ".venv" not in path.parts
            and "node_modules" not in path.parts
            and "output" not in path.parts
        ]
        if not files:
            return [_error_item("folder", str(root), "source folder is empty")]
        return [_item_from_file(path, root) for path in sorted(files)[:200]]
    if goal.source == "folder":
        return [_error_item("folder", "", "source_folder is required for folder source")]
    if goal.source == "local-file" and goal.local_file:
        path = Path(goal.local_file)
        if not path.exists() or not path.is_file():
            return [_error_item("local-file", str(path), "local file does not exist")]
        return [_item_from_file(path, path.parent if path.parent else Path("."))]
    if goal.source == "local-file":
        return [_error_item("local-file", "", "local_file is required for local-file source")]
    if goal.source == "websearch":
        cache_path = _websearch_cache_path(state.output_dir) if state is not None else None
        return _websearch_items(goal, cache_path=cache_path)
    if goal.source == "manual":
        return []
    return []


def _error_item(source_type: str, path: str, note: str) -> dict[str, object]:
    return {
        "name": f"ERROR: {note}",
        "type": source_type,
        "path": path or "missing",
        "size_bytes": "unknown",
        "readable": "no",
        "note": f"ERROR: {note}",
    }


def _websearch_cache_path(output_dir: str) -> Path:
    return Path(output_dir) / "artifacts" / "source" / "websearch-results.json"


def run_websearch_and_cache(topic: str, output_dir: str | Path) -> dict[str, object]:
    """Run Tavily websearch, persist results, and return a structured summary.

    Called by the ``vm_websearch`` typed tool so the search appears as a
    distinct visible step in the producer chat timeline.
    """
    goal = VideoMakerGoal(topic=topic, source="websearch")
    cache_path = _websearch_cache_path(str(output_dir))
    items = _websearch_items(goal, cache_path=cache_path, force_fresh=True)
    error = any(str(i.get("note", "")).startswith("ERROR:") for i in items)
    return {
        "status": "error" if error else "ok",
        "item_count": len(items),
        "items": items,
        "cache_path": str(cache_path),
    }


def _websearch_items(
    goal: VideoMakerGoal,
    *,
    cache_path: Path | None = None,
    force_fresh: bool = False,
) -> list[dict[str, object]]:
    # Use cached results when available (avoids redundant API call after vm_websearch).
    if cache_path and not force_fresh and cache_path.exists():
        try:
            raw = json.loads(cache_path.read_text(encoding="utf-8"))
            if isinstance(raw, list) and raw:
                return raw
        except Exception:
            pass

    tavily_key = _tavily_api_key()
    if not tavily_key:
        return [
            _error_item(
                "websearch",
                "websearch",
                "websearch source intake requires TAVILY_API_KEY",
            )
        ]
    try:
        from tavily import TavilyClient

        client = TavilyClient(api_key=tavily_key)
        # advanced depth gives richer per-result content; scriptwriter needs
        # real numbers/quotes to ground data_card scenes — 240 chars is not enough.
        response = client.search(query=goal.topic, max_results=8, search_depth="advanced")
    except Exception as exc:  # pragma: no cover - depends on external provider/network
        return [_error_item("websearch", "websearch", f"websearch failed: {exc}")]

    results = response.get("results", []) if isinstance(response, dict) else []
    items: list[dict[str, object]] = []
    for result in results:
        if not isinstance(result, dict):
            continue
        url = str(result.get("url", "")).strip()
        if not url:
            continue
        title = str(result.get("title", url)).strip() or url
        # Prefer richer raw_content when Tavily returns it; fall back to content.
        raw = result.get("raw_content") or result.get("content") or ""
        snippet = str(raw).strip().replace("\n", " ")
        items.append(
            {
                "name": title,
                "type": "url",
                "path": url,
                "size_bytes": "unknown",
                "readable": "yes",
                # 2000 chars gives scriptwriter meaningful context for claims/stats.
                "note": snippet[:2000] or "websearch result",
            }
        )

    # Persist to cache so vm_ratify_source_intake reuses without re-calling Tavily.
    if cache_path and items:
        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(
                json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8"
            )
        except Exception:
            pass

    return items or [_error_item("websearch", "websearch", "websearch returned no URL results")]


def _tavily_api_key() -> str:
    key = os.environ.get("TAVILY_API_KEY", "").strip()
    if key:
        return key
    root = Path(os.environ.get("ORCHESTRATOR_SKILLS_ROOT", "") or Path.cwd())
    env_path = root / ".env"
    if not env_path.is_file():
        return ""
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        if name.strip() == "TAVILY_API_KEY":
            return value.strip().strip('"').strip("'")
    return ""


def _item_from_file(path: Path, root: Path) -> dict[str, object]:
    try:
        rel = path.relative_to(root)
    except ValueError:
        rel = path
    suffix = path.suffix.lower()
    file_type = {
        ".md": "markdown",
        ".txt": "text",
        ".csv": "csv",
        ".json": "json",
        ".png": "image",
        ".jpg": "image",
        ".jpeg": "image",
        ".gif": "image",
        ".mp3": "audio",
        ".wav": "audio",
        ".mp4": "video",
        ".mov": "video",
    }.get(suffix, "other")
    readable = "yes" if file_type in {"markdown", "text", "csv", "json"} else "partial"
    size = path.stat().st_size if path.exists() else "unknown"
    return {
        "name": str(rel).replace("\\", "/"),
        "type": file_type,
        "path": str(path),
        "size_bytes": size,
        "readable": readable,
        "note": "indexed for Scriptwriter source selection",
    }
