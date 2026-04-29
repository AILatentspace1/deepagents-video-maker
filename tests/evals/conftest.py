"""Shared fixtures for eval tests."""

from __future__ import annotations

import json
import os
import re
import pytest
from pathlib import Path

from deepagents_video_maker.models import VideoMakerGoal
from deepagents_video_maker.script_flow import start_script_milestone


SCRIPTWRITER_PROMPT_PATH = (
    Path(__file__).parents[2] / "skills" / "video-maker" / "agents" / "scriptwriter.md"
)
_DOT_ENV_PATH = Path(__file__).parents[2] / ".env"


def _load_dot_env() -> None:
    """Load .env into os.environ (no-op if missing)."""
    if not _DOT_ENV_PATH.exists():
        return
    for raw in _DOT_ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def _manifest_from_script(script_text: str) -> dict:
    """Parse script.md content and auto-generate a manifest dict with scenes[].

    Accepts both English (## Scene N) and Chinese (## 场景 N) headings, as well
    as bold/alternative formats seen from different LLMs.
    """
    DURATION_DEFAULTS = {
        "title_card": 3,
        "transition": 2,
        "data_card": 5,
        "quote_card": 5,
        "diagram_walkthrough": 12,
    }
    # Accept: ## Scene N, ## 场景 N, ## N: <title>, **Scene N:** (bold), ---Scene N---
    SCENE_HEADING_RE = re.compile(
        r"(?m)^(?:##\s+(?:Scene\b|场景\s*\d|\d+[:.])|\*\*Scene\s+\d+|\*\*场景\s*\d+)",
        re.IGNORECASE,
    )
    chunks = SCENE_HEADING_RE.split(script_text)
    # Find positions of headings to prefix back
    heading_positions = [m.start() for m in SCENE_HEADING_RE.finditer(script_text)]

    scenes = []
    for i, chunk in enumerate(chunks):
        if i == 0 and not heading_positions:
            continue  # content before first scene heading
        if i == 0:
            continue  # preamble (style_spine, title, etc.)

        scene_id = len(scenes) + 1

        # Narration patterns: YAML block literal, bold heading, or plain key
        narr_match = re.search(
            r"(?m)^(?:\*\*Narration:\*\*|narration:)\s*\|?\s*\n((?:[ \t]+.+\n?)+)",
            chunk,
        )
        if not narr_match:
            narr_match = re.search(r"(?m)^\*\*Narration:\*\*\s+(.+?)(?=\n\n|\n\*\*|\Z)", chunk, re.DOTALL)
        if not narr_match:
            narr_match = re.search(r"(?m)^narration:\s+(.+?)(?=\n\w|\Z)", chunk, re.DOTALL)
        if not narr_match:
            # Chinese narration key
            narr_match = re.search(r"(?m)^旁白[：:]\s*(.+?)(?=\n\n|\Z)", chunk, re.DOTALL)
        narration = re.sub(r"\s+", " ", narr_match.group(1)).strip() if narr_match else ""
        narration = narration.lstrip("|").strip()

        dur_match = re.search(r"(?m)^(?:\*\*Duration:\*\*|duration(?:_estimate)?:)\s*(\d+)", chunk)
        scene_type_match = re.search(r"(?m)^(?:\*\*Type:\*\*|type:)\s*(\S+)", chunk)
        scene_type = (scene_type_match.group(1).strip("*:,").lower() if scene_type_match else "narration")
        duration = int(dur_match.group(1)) if dur_match else DURATION_DEFAULTS.get(scene_type, 8)

        scenes.append({"id": scene_id, "narration": narration, "duration": duration})
    return {"scenes": scenes}


def _extract_script_text(text: str) -> str | None:
    """Extract the script.md content from an LLM response, using multiple strategies.

    Handles:
    - Proper ```script.md fenced block
    - Empty ```script.md block (nested inner fences close it early)
    - Raw markdown output with style_spine / ## Scene headings
    - Content wrapped in other fenced blocks
    """
    # Strategy 1: ```script.md block with real content
    for m in re.finditer(r"```script\.md\n(.*?)```", text, re.DOTALL):
        content = m.group(1).strip()
        if content and ("## Scene" in content or "## 场景" in content or "```style_spine" in content):
            return content

    # Strategy 2: Empty ```script.md block due to nested inner fences.
    # The actual script content follows AFTER the outer block's closing ```.
    m = re.search(r"```script\.md\n```", text)
    if m:
        after = text[m.end():].strip()
        if after and ("```style_spine" in after or re.search(r"^##\s+(Scene\b|场景)", after, re.MULTILINE)):
            return after

    # Strategy 3: style_spine block present — everything from it (or preceding title) onward
    spine_m = re.search(r"```style_spine\n", text)
    if spine_m:
        start = spine_m.start()
        # Walk back to pick up an H1 title if within 300 chars
        before = text[:start]
        title_m = re.search(r"(?m)^#\s+.+$", before[-300:])
        if title_m:
            start = start - len(before[-300:]) + title_m.start()
        candidate = text[start:].strip()
        if "## Scene" in candidate or "## 场景" in candidate:
            return candidate

    # Strategy 4: Find ## Scene headings directly, walk back to title
    scene_m = re.search(r"(?m)^##\s+(?:Scene\b|场景)\s*\d", text)
    if scene_m:
        before = text[:scene_m.start()]
        title_m = re.search(r"(?m)^#\s+.+$", before[-500:])
        offset = max(0, len(before) - 500)
        start = offset + title_m.start() if title_m else scene_m.start()
        return text[start:].strip()

    # Strategy 5: Any fenced block containing ## Scene
    for m in re.finditer(r"```[^\n]*\n(.*?)```", text, re.DOTALL):
        content = m.group(1).strip()
        if "## Scene" in content:
            return content

    return None


def invoke_scriptwriter(llm, goal: VideoMakerGoal, research_content: str, run_dir: Path) -> tuple[bool, str]:
    """Call the scriptwriter LLM and write script.md + manifest.json to *run_dir*.

    Returns (success, error_message).
    Manifest is auto-generated by parsing scene blocks from the script — no second
    LLM call required and the manifest always has the correct ``scenes[]`` schema.
    """
    from langchain_core.messages import HumanMessage, SystemMessage

    raw = SCRIPTWRITER_PROMPT_PATH.read_text(encoding="utf-8")

    for placeholder, value in {
        "{topic}": goal.topic,
        "{duration}": goal.duration,
        "{style}": goal.style,
        "{aspectRatio}": goal.aspect_ratio,
        "{bgm_file}": goal.bgm_file or "none",
        "{sfx_enabled}": str(goal.sfx_enabled).lower(),
        "{lut_style}": goal.lut_style or "auto",
        "{template_bgm_track}": "auto",
        "{project_root}": ".",
        "{research_file}": "see <research> block below",
        "{script_path}": str(run_dir / "script.md"),
        "{manifest_path}": str(run_dir / "manifest.json"),
    }.items():
        raw = raw.replace(placeholder, value)

    user = (
        "Research content is provided inline (no file reading needed for this eval):\n\n"
        f"<research>\n{research_content}\n</research>\n\n"
        "Generate the complete script now. "
        "Output the script as plain markdown starting directly with the ```style_spine block. "
        "Do NOT wrap the entire script in an outer code fence. "
        "Scene headings MUST use exactly `## Scene N` format (English, double-hash, "
        "space, the word 'Scene', space, a number)."
    )

    try:
        response = llm.invoke([SystemMessage(content=raw), HumanMessage(content=user)])
        content = response.content
        if isinstance(content, list):
            text = " ".join(
                b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"
            )
        else:
            text = str(content)
    except Exception as exc:
        return False, f"LLM call failed: {exc}"

    script_text = _extract_script_text(text)
    if script_text is None:
        return False, f"Could not extract script from response. Preview: {text[:600]}"
    if not script_text:
        return False, f"Extracted script is empty. Response length: {len(text)}"

    # Auto-generate manifest from parsed scene blocks
    manifest = _manifest_from_script(script_text)
    if not manifest["scenes"]:
        return False, (
            f"No scene headings found in extracted script "
            f"(tried ## Scene N, ## 场景 N patterns). "
            f"Script preview: {script_text[:500]}"
        )

    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "script.md").write_text(script_text, encoding="utf-8")
    (run_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return True, ""


def pytest_addoption(parser):
    """Add command-line options for evals."""
    parser.addoption(
        "--model",
        action="store",
        default="claude-sonnet-4-6",
        help="Model to use for agent tests",
    )
    parser.addoption(
        "--evals-report-file",
        action="store",
        default=None,
        help="Path to write eval summary JSON",
    )


@pytest.fixture
def model(request):
    """Get model from indirect parametrization or command line."""
    if hasattr(request, "param"):
        return request.param
    return request.config.getoption("--model")


@pytest.fixture
def llm_client(model):
    """LangChain ChatAnthropic client for live scriptwriter eval tests."""
    _load_dot_env()
    api_key = os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        pytest.skip("ANTHROPIC_AUTH_TOKEN / ANTHROPIC_API_KEY not set")
    try:
        from langchain_anthropic import ChatAnthropic
    except ImportError:
        pytest.skip("langchain_anthropic not installed")

    base_url = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
    return ChatAnthropic(
        model=model,
        api_key=api_key,
        base_url=base_url,
        max_tokens=8192,
        timeout=180,
        max_retries=2,
    )


def pytest_sessionfinish(session, exitstatus):
    """Write eval summary JSON to --evals-report-file if specified."""
    report_file = session.config.getoption("--evals-report-file", default=None)
    if not report_file:
        return

    tr = session.config.pluginmanager.get_plugin("terminalreporter")
    if tr:
        passed = len(tr.stats.get("passed", []))
        failed = len(tr.stats.get("failed", []))
        error = len(tr.stats.get("error", []))
    else:
        passed = failed = error = 0

    summary = {
        "exit_status": int(exitstatus),
        "passed": passed,
        "failed": failed + error,
        "total": passed + failed + error,
    }

    Path(report_file).parent.mkdir(parents=True, exist_ok=True)
    Path(report_file).write_text(json.dumps(summary, indent=2), encoding="utf-8")


@pytest.fixture
def evals_report_file(request):
    """Get eval report path from command line."""
    return request.config.getoption("--evals-report-file")


@pytest.fixture
def sample_research_content():
    """Sample research report for scriptwriter tests."""
    return """# Research Report: AI Agent Evolution

## 1. Executive Summary
AI Agents are transforming how we work. From simple chatbots to autonomous systems, the technology has advanced rapidly in 2024-2025.

## 2. Data Points
- Global AI Agent investment: $150B in 2024
- Market leaders: Google (35%), Microsoft (25%), Amazon (10%), Others (30%)
- Growth rate: 300% year-over-year

## 3. Visual Strategy
visual_strategy: image_light
Recommend images for: hook scene, climax scene

## 4. Key Findings
AI Agents now handle complex multi-step tasks. They can plan, use tools, and learn from feedback.

## 5. Technical Architecture
Modern agents use LLM + planning + tool execution loops.

## 6. Style Spine
lut_style: tech_cool
tone: professional, confident

## 7. Narrative Flow
Hook → Evolution → Impact → Future → CTA

## 8. Additional Data
- Average task completion rate: 85%
- User satisfaction: 92%

## 9. Quotes
"AI Agents are not just responding anymore, they're acting." - Dr. Sarah Chen, MIT AI Lab
"""
