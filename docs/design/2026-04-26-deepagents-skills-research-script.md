# DeepAgents SDK + Skills: Research & Script Milestones Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 DeepAgents-native video-maker 通过 SDK `skills=` 参数复用 `.claude/skills/video-maker/` 业务知识，端到端跑通 research + script 两个 milestone。

**Architecture:** Producer (main agent) 走 controller protocol；researcher / scriptwriter 两个 custom subagent 各自带 `skills=` 加载独立 SKILL.md（thin wrapper 引用 `.claude/skills/video-maker/agents/*.md`）；状态机骨架由 typed tools (`vm_*`) 提供，业务知识由 progressive disclosure 按需加载。

**Tech Stack:** Python 3.11+, `deepagents>=1.7.0`, `langchain-core`, `pytest`, FilesystemBackend (virtual_mode=True), pytest 在 `tests/deepagents_video_maker/` 下用 `uv run pytest` 执行。

---

## File Structure

**New:**
- `src/deepagents_video_maker/script_flow.py` — 镜像 `research_flow.py` 的 script milestone 编排
- `.deepagents/skills/video-researcher/SKILL.md` — thin wrapper，引用 `.claude/skills/video-maker/agents/researcher.md`
- `.deepagents/skills/video-scriptwriter/SKILL.md` — 同上，引用 scriptwriter.md
- `tests/deepagents_video_maker/test_ratify_script.py`
- `tests/deepagents_video_maker/test_script_flow.py`
- `tests/deepagents_video_maker/test_skill_files.py`
- `tests/deepagents_video_maker/test_agent_factory.py`
- `scripts/smoke_skills_research_script.py`

**Modified:**
- `src/deepagents_video_maker/ratify.py` — 追加 `ratify_script()`
- `src/deepagents_video_maker/langchain_tools.py` — 追加 `vm_start_script`, `vm_build_scriptwriter_task`, `vm_ratify_script`
- `src/deepagents_video_maker/agent.py` — 加 `skills=` 参数，subagent 列表精简到 researcher + scriptwriter，每项带 `skills=`
- `src/deepagents_video_maker/prompts/producer.md` — 重写为 controller-only（保留 6 步协议，删业务规则）
- `src/deepagents_video_maker/prompts/subagents/researcher.md` — 精简到 input/output contract + tool discipline
- `src/deepagents_video_maker/prompts/subagents/scriptwriter.md` — 同上

**Untouched (作为 source of truth 复用):**
- `.claude/skills/video-maker/SKILL.md` 及 `agents/`、`milestones/`、`ratify/` 整树

---

## Task 1: `ratify_script` 函数

**Files:**
- Test: `tests/deepagents_video_maker/test_ratify_script.py`
- Modify: `src/deepagents_video_maker/ratify.py`

- [ ] **Step 1: 写 failing test**

```python
# tests/deepagents_video_maker/test_ratify_script.py
from pathlib import Path
import json

from deepagents_video_maker.ratify import ratify_script


def _write_script(tmp_path: Path, scene_count: int = 3) -> Path:
    text = "# Script\n\n"
    for i in range(1, scene_count + 1):
        text += (
            f"## Scene {i}\n"
            f"type: narration\n"
            f"narration: hello scene {i}\n"
            f"scene_intent: setup\n"
            f"content_brief: brief {i}\n\n"
        )
    path = tmp_path / "script.md"
    path.write_text(text, encoding="utf-8")
    return path


def _write_manifest(tmp_path: Path, scene_count: int = 3) -> Path:
    data = {
        "scenes": [
            {"id": f"scene-{i}", "narration": f"hello scene {i}", "duration": 6}
            for i in range(1, scene_count + 1)
        ]
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_ratify_script_passes_when_complete(tmp_path):
    script = _write_script(tmp_path, scene_count=3)
    manifest = _write_manifest(tmp_path, scene_count=3)
    result = ratify_script(script, manifest)
    assert result.passed, result.issues


def test_ratify_script_fails_when_script_missing(tmp_path):
    manifest = _write_manifest(tmp_path)
    result = ratify_script(tmp_path / "missing.md", manifest)
    assert not result.passed
    assert any("exists" in c.id and not c.passed for c in result.checks)


def test_ratify_script_fails_when_manifest_invalid(tmp_path):
    script = _write_script(tmp_path)
    bad = tmp_path / "manifest.json"
    bad.write_text("not json", encoding="utf-8")
    result = ratify_script(script, bad)
    assert not result.passed


def test_ratify_script_fails_when_scene_count_mismatches(tmp_path):
    script = _write_script(tmp_path, scene_count=3)
    manifest = _write_manifest(tmp_path, scene_count=2)
    result = ratify_script(script, manifest)
    assert not result.passed
```

- [ ] **Step 2: 跑 test，确认 fail**

```bash
uv run pytest tests/deepagents_video_maker/test_ratify_script.py -v
```

Expected: `ImportError` 或 `AttributeError: module ... has no attribute 'ratify_script'`

- [ ] **Step 3: 实现 `ratify_script`**

在 `src/deepagents_video_maker/ratify.py` 末尾追加：

```python
import json


def ratify_script(
    script_path: str | Path,
    manifest_path: str | Path,
) -> RatifyResult:
    script = Path(script_path)
    manifest = Path(manifest_path)
    checks: list[RatifyCheck] = []

    script_exists = script.exists() and script.is_file()
    checks.append(RatifyCheck("script_exists", script_exists, f"{script} exists={script_exists}"))
    manifest_exists = manifest.exists() and manifest.is_file()
    checks.append(RatifyCheck("manifest_exists", manifest_exists, f"{manifest} exists={manifest_exists}"))
    if not (script_exists and manifest_exists):
        return _result(checks)

    text = script.read_text(encoding="utf-8")
    script_scene_count = len(re.findall(r"(?m)^##\s+Scene\b", text))
    checks.append(
        RatifyCheck(
            "script_min_scenes",
            script_scene_count > 0,
            f"script_scene_count={script_scene_count}",
            {"script_scene_count": script_scene_count},
        )
    )

    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        checks.append(RatifyCheck("manifest_parseable", False, f"json error: {exc}"))
        return _result(checks)
    checks.append(RatifyCheck("manifest_parseable", True, "json parseable"))

    scenes = data.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        checks.append(RatifyCheck("manifest_has_scenes", False, "manifest.scenes missing/empty"))
        return _result(checks)
    checks.append(RatifyCheck("manifest_has_scenes", True, f"manifest_scene_count={len(scenes)}"))

    for idx, scene in enumerate(scenes):
        for field in ("id", "narration", "duration"):
            if field not in scene:
                checks.append(
                    RatifyCheck(
                        f"manifest_scene_{idx}_field_{field}",
                        False,
                        f"scene[{idx}] missing field={field}",
                    )
                )
                return _result(checks)

    checks.append(
        RatifyCheck(
            "scene_count_match",
            len(scenes) == script_scene_count,
            f"manifest={len(scenes)} script={script_scene_count}",
            {"manifest_scene_count": len(scenes), "script_scene_count": script_scene_count},
        )
    )

    return _result(checks)
```

- [ ] **Step 4: 跑 test，确认 pass**

```bash
uv run pytest tests/deepagents_video_maker/test_ratify_script.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add src/deepagents_video_maker/ratify.py tests/deepagents_video_maker/test_ratify_script.py
git commit -m "feat(deepagents-vm): add ratify_script Layer 1 checks"
```

---

## Task 2: `script_flow` 模块

**Files:**
- Test: `tests/deepagents_video_maker/test_script_flow.py`
- Create: `src/deepagents_video_maker/script_flow.py`

- [ ] **Step 1: 写 failing test**

```python
# tests/deepagents_video_maker/test_script_flow.py
from pathlib import Path
import json

from deepagents_video_maker.models import (
    MilestoneState,
    MilestoneStatus,
    VideoMakerGoal,
    VideoMakerState,
)
from deepagents_video_maker.script_flow import (
    build_scriptwriter_task_description,
    ratify_and_update_script,
    start_script_milestone,
)


def _state(tmp_path: Path) -> VideoMakerState:
    return VideoMakerState(
        output_dir=str(tmp_path),
        milestones=[
            MilestoneState(id="research", status=MilestoneStatus.COMPLETED, current_run=1),
            MilestoneState(id="script"),
        ],
    )


def _goal(local_file: str = "ref.md") -> VideoMakerGoal:
    g = VideoMakerGoal(topic="quantum attention", source="local-file", local_file=local_file)
    g.duration = "1-3min"
    g.style = "professional"
    return g


def test_start_script_milestone_creates_run_dir(tmp_path):
    state = _state(tmp_path)
    run = start_script_milestone(state)
    assert Path(run.run_dir).exists()
    assert run.milestone == "script"
    assert state.milestone("script").status == MilestoneStatus.IN_PROGRESS


def test_build_scriptwriter_task_description_includes_research_path(tmp_path):
    state = _state(tmp_path)
    research_file = tmp_path / "artifacts/research/run-1/research.md"
    research_file.parent.mkdir(parents=True, exist_ok=True)
    research_file.write_text("# Research\n", encoding="utf-8")
    run = start_script_milestone(state)
    desc = build_scriptwriter_task_description(_goal(), state, run)
    assert "research_file" in desc
    assert "script.md" in desc
    assert "manifest.json" in desc


def test_ratify_and_update_script_marks_completed_when_artifacts_valid(tmp_path):
    state = _state(tmp_path)
    run = start_script_milestone(state)
    run_dir = Path(run.run_dir)
    (run_dir / "script.md").write_text(
        "## Scene 1\ntype: narration\nnarration: hi\nscene_intent: hook\ncontent_brief: x\n",
        encoding="utf-8",
    )
    (run_dir / "manifest.json").write_text(
        json.dumps({"scenes": [{"id": "s1", "narration": "hi", "duration": 5}]}),
        encoding="utf-8",
    )
    result = ratify_and_update_script(state, _goal())
    assert result.passed
    assert state.milestone("script").status == MilestoneStatus.COMPLETED


def test_ratify_and_update_script_increments_retry_when_artifact_missing(tmp_path):
    state = _state(tmp_path)
    start_script_milestone(state)
    result = ratify_and_update_script(state, _goal())
    assert not result.passed
    assert state.milestone("script").retry_count == 1
    assert state.milestone("script").status == MilestoneStatus.IN_PROGRESS
```

- [ ] **Step 2: 跑 test，确认 fail**

```bash
uv run pytest tests/deepagents_video_maker/test_script_flow.py -v
```

Expected: `ImportError: cannot import name 'start_script_milestone' from 'deepagents_video_maker.script_flow'`

- [ ] **Step 3: 实现 `script_flow.py`**

```python
# src/deepagents_video_maker/script_flow.py
"""Native Script milestone flow helpers, mirroring research_flow.py."""

from __future__ import annotations

import os
from pathlib import Path

from .artifacts import script_artifact_paths
from .models import MilestoneStatus, RatifyResult, RunInfo, VideoMakerGoal, VideoMakerState
from .ratify import ratify_script
from .session import create_milestone_run
from .state_store import update_milestone_status


def start_script_milestone(state: VideoMakerState) -> RunInfo:
    return create_milestone_run(state, "script")


def build_scriptwriter_task_description(
    goal: VideoMakerGoal,
    state: VideoMakerState,
    run_info: RunInfo,
) -> str:
    research_run = state.milestone("research").current_run or 1
    research_file = (
        Path(state.output_dir) / "artifacts" / "research" / f"run-{research_run}" / "research.md"
    )
    paths = script_artifact_paths(state.output_dir, run_info.run_number)
    return f"""You are the DeepAgents-native video-maker Scriptwriter subagent.

Input contract:
- topic: {goal.topic}
- duration: {goal.duration}
- style: {goal.style}
- aspect_ratio: {goal.aspect_ratio}
- bgm_file: {goal.bgm_file}
- sfx_enabled: {goal.sfx_enabled}
- research_file: {_to_virtual_path(research_file)}
- script_path: {_to_virtual_path(paths['script'])}
- manifest_path: {_to_virtual_path(paths['manifest'])}
- eval_mode: {goal.eval_mode}

Required behavior:
1. Read research_file with read_file. Do not ask Producer to inline content.
2. Write script.md (Markdown, scenes as `## Scene N`) and manifest.json (JSON with scenes[]).
3. Each manifest scene must include: id, narration, duration.
4. script.md scene count must equal manifest.scenes length.
5. Return only the output contract summary, not full script text.

Output contract:
script_path: {_to_virtual_path(paths['script'])}
manifest_path: {_to_virtual_path(paths['manifest'])}
scene_count: <number>
estimated_duration: <seconds>
blocking_issues: <none or list>
"""


def _to_virtual_path(path: str | Path) -> str:
    item = Path(path).resolve()
    root_env = os.environ.get("ORCHESTRATOR_SKILLS_ROOT")
    if root_env:
        try:
            return "/" + item.relative_to(Path(root_env).resolve()).as_posix()
        except ValueError:
            pass
    return str(path)


def ratify_and_update_script(state: VideoMakerState, goal: VideoMakerGoal) -> RatifyResult:
    milestone = state.milestone("script")
    paths = script_artifact_paths(state.output_dir, milestone.current_run or 1)
    result = ratify_script(paths["script"], paths["manifest"])
    ratify_payload = {
        "passed": result.passed,
        "issues": result.issues,
        "checks": [
            {"id": c.id, "passed": c.passed, "message": c.message, "metadata": c.metadata}
            for c in result.checks
        ],
    }
    if result.passed:
        update_milestone_status(state, "script", MilestoneStatus.COMPLETED, ratify=ratify_payload)
    else:
        milestone.retry_count += 1
        if milestone.retry_count > milestone.max_retries:
            update_milestone_status(
                state,
                "script",
                MilestoneStatus.BLOCKED,
                blocking_reason="script ratify failed after max retries",
                ratify=ratify_payload,
            )
            result.next_action = "block_for_user"
        else:
            update_milestone_status(
                state,
                "script",
                MilestoneStatus.IN_PROGRESS,
                blocking_reason="script ratify failed; retry required",
                ratify=ratify_payload,
            )
            result.next_action = "retry_milestone"
    return result
```

- [ ] **Step 4: 跑 test，确认 pass**

```bash
uv run pytest tests/deepagents_video_maker/test_script_flow.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add src/deepagents_video_maker/script_flow.py tests/deepagents_video_maker/test_script_flow.py
git commit -m "feat(deepagents-vm): add script_flow milestone helpers"
```

---

## Task 3: 暴露 script flow 为 langchain tools

**Files:**
- Test: `tests/deepagents_video_maker/test_langchain_tools.py`
- Modify: `src/deepagents_video_maker/langchain_tools.py`

- [ ] **Step 1: 写 failing test**

```python
# tests/deepagents_video_maker/test_langchain_tools.py
from deepagents_video_maker.langchain_tools import build_langchain_tools


def test_build_langchain_tools_includes_script_tools():
    names = {t.name for t in build_langchain_tools()}
    assert {"vm_start_script", "vm_build_scriptwriter_task", "vm_ratify_script"}.issubset(names)
```

- [ ] **Step 2: 跑 test，确认 fail**

```bash
uv run pytest tests/deepagents_video_maker/test_langchain_tools.py -v
```

Expected: AssertionError: missing names.

- [ ] **Step 3: 追加 3 个 `@_tool` wrapper**

在 `src/deepagents_video_maker/langchain_tools.py` 顶部 import 区追加：

```python
from .script_flow import (
    build_scriptwriter_task_description,
    ratify_and_update_script,
    start_script_milestone,
)
```

在 `vm_ratify_research` 后追加：

```python
@_tool
def vm_start_script(output_dir: str) -> dict[str, Any]:
    """Start the script milestone and create the next run dir."""
    state_path = Path(output_dir) / "state.yaml"
    state = load_state_yaml(state_path)
    run = start_script_milestone(state)
    save_state_yaml(state, state_path)
    return {"state": to_jsonable(state), "run": to_jsonable(run)}


@_tool
def vm_build_scriptwriter_task(
    output_dir: str,
    run_number: int = 1,
    prompt: str | None = None,
    topic: str | None = None,
    source: str | None = None,
    local_file: str | None = None,
    duration: str | None = None,
    style: str | None = None,
    aspect_ratio: str | None = None,
    eval_mode: str | None = None,
) -> dict[str, Any]:
    """Build strict task description for task(subagent_type='scriptwriter')."""
    goal = _goal_from_inputs(
        prompt=prompt,
        topic=topic,
        source=source,
        local_file=local_file,
        duration=duration,
        style=style,
        aspect_ratio=aspect_ratio,
        eval_mode=eval_mode,
    )
    state = load_state_yaml(Path(output_dir) / "state.yaml")
    run_dir = Path(output_dir) / "artifacts" / "script" / f"run-{run_number}"
    description = build_scriptwriter_task_description(
        goal,
        state,
        run_info=type(
            "RunInfoLike",
            (),
            {"milestone": "script", "run_number": run_number, "run_dir": str(run_dir)},
        )(),
    )
    return {"subagent_type": "scriptwriter", "description": description, "run_dir": str(run_dir)}


@_tool
def vm_ratify_script(
    output_dir: str,
    prompt: str | None = None,
    topic: str | None = None,
    source: str | None = None,
    local_file: str | None = None,
    duration: str | None = None,
    style: str | None = None,
    aspect_ratio: str | None = None,
    eval_mode: str | None = None,
) -> dict[str, Any]:
    """Ratify script.md + manifest.json and update script milestone state."""
    goal = _goal_from_inputs(
        prompt=prompt,
        topic=topic,
        source=source,
        local_file=local_file,
        duration=duration,
        style=style,
        aspect_ratio=aspect_ratio,
        eval_mode=eval_mode,
    )
    state_path = Path(output_dir) / "state.yaml"
    state = load_state_yaml(state_path)
    result = ratify_and_update_script(state, goal)
    save_state_yaml(state, state_path)
    return {"result": to_jsonable(result), "state": to_jsonable(state)}
```

修改 `build_langchain_tools()` 返回列表：

```python
def build_langchain_tools() -> list[Any]:
    return [
        vm_parse_video_request,
        vm_init_video_session,
        vm_start_research,
        vm_build_researcher_task,
        vm_ratify_research,
        vm_start_script,
        vm_build_scriptwriter_task,
        vm_ratify_script,
    ]
```

- [ ] **Step 4: 跑 test，确认 pass**

```bash
uv run pytest tests/deepagents_video_maker/test_langchain_tools.py -v
```

Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add src/deepagents_video_maker/langchain_tools.py tests/deepagents_video_maker/test_langchain_tools.py
git commit -m "feat(deepagents-vm): expose script flow as vm_* langchain tools"
```

---

## Task 4: Skill thin-wrapper 目录

**Files:**
- Create: `.deepagents/skills/video-researcher/SKILL.md`
- Create: `.deepagents/skills/video-scriptwriter/SKILL.md`
- Test: `tests/deepagents_video_maker/test_skill_files.py`

- [ ] **Step 1: 写 failing test**

```python
# tests/deepagents_video_maker/test_skill_files.py
from pathlib import Path

import re

SKILLS_ROOT = Path(__file__).resolve().parents[2] / ".deepagents" / "skills"

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def _frontmatter(text: str) -> dict[str, str]:
    match = FRONTMATTER_RE.match(text)
    assert match, "SKILL.md must start with frontmatter"
    out: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            out[key.strip()] = value.strip()
    return out


def test_video_researcher_skill_has_frontmatter():
    text = (SKILLS_ROOT / "video-researcher" / "SKILL.md").read_text(encoding="utf-8")
    fm = _frontmatter(text)
    assert fm["name"] == "video-researcher"
    assert "research" in fm["description"].lower()
    assert ".claude/skills/video-maker/agents/researcher.md" in text


def test_video_scriptwriter_skill_has_frontmatter():
    text = (SKILLS_ROOT / "video-scriptwriter" / "SKILL.md").read_text(encoding="utf-8")
    fm = _frontmatter(text)
    assert fm["name"] == "video-scriptwriter"
    assert "script" in fm["description"].lower()
    assert ".claude/skills/video-maker/agents/scriptwriter.md" in text
```

- [ ] **Step 2: 跑 test，确认 fail**

```bash
uv run pytest tests/deepagents_video_maker/test_skill_files.py -v
```

Expected: `FileNotFoundError`.

- [ ] **Step 3: 写 SKILL.md (researcher)**

```markdown
---
name: video-researcher
description: How to research a video topic from web/local files and write a structured research.md with sections, sources, and visual_strategy hints. Use when acting as the video-maker researcher subagent.
---

# video-researcher

## Source of truth

完整工作指令在 `.claude/skills/video-maker/agents/researcher.md`。
本 skill 是 thin wrapper：调用时用 `read_file` 加载该路径，按其指令执行。

## Tool mapping (DeepAgents semantics)

- Claude Code `Read` → DeepAgents `read_file`
- Claude Code `Write` → DeepAgents `write_file`
- Claude Code `Bash` → DeepAgents shell tool（如可用）

## Path discipline

`read_file` / `write_file` 只接受虚拟路径（以 `/` 开头），不要传 Windows 绝对路径。

## Output contract（最终消息必须包含）

- research_path
- summary（3-5 句）
- section_count
- source_count
- visual_strategy
- blocking_issues（none 或列表）

## Ratify rules referenced

`.claude/skills/video-maker/ratify/research-rules.md`
```

- [ ] **Step 4: 写 SKILL.md (scriptwriter)**

```markdown
---
name: video-scriptwriter
description: How to convert research.md into script.md and manifest.json with scene types (narration/data_card/quote_card/title_card/transition), narrative arc, and style spine. Use when acting as the video-maker scriptwriter subagent.
---

# video-scriptwriter

## Source of truth

完整工作指令在 `.claude/skills/video-maker/agents/scriptwriter.md`。
辅助文档：

- `.claude/skills/video-maker/milestones/script.md`（milestone 阶段细节）
- `.claude/skills/video-maker/ratify/script-rules.md`（Layer 1 校验）

调用时用 `read_file` 加载这些文件，按其指令执行。

## Path discipline

虚拟路径 only（以 `/` 开头）。

## Output contract（最终消息必须包含）

- script_path
- manifest_path
- scene_count
- estimated_duration
- blocking_issues（none 或列表）

## Hard rules

- script.md 中 `## Scene N` 数量必须等于 manifest.json `scenes[]` 长度
- 每个 manifest scene 必须含 id / narration / duration
- narration / data_card / quote_card 场景必须含 scene_intent + content_brief
- 不写 `layer_hint` 或 `beats`（已废弃字段）
```

- [ ] **Step 5: 跑 test，确认 pass**

```bash
uv run pytest tests/deepagents_video_maker/test_skill_files.py -v
```

Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add .deepagents/skills tests/deepagents_video_maker/test_skill_files.py
git commit -m "feat(deepagents-vm): add video-researcher/scriptwriter skill wrappers"
```

---

## Task 5: Producer prompt 精简为 controller-only

**Files:**
- Modify: `src/deepagents_video_maker/prompts/producer.md`
- Test: `tests/deepagents_video_maker/test_producer_prompt.py`

- [ ] **Step 1: 写 failing test**

```python
# tests/deepagents_video_maker/test_producer_prompt.py
from deepagents_video_maker.prompts import load_prompt


def test_producer_prompt_is_controller_only():
    text = load_prompt("producer")
    assert "vm_init_video_session" in text
    assert "vm_ratify_research" in text
    assert "vm_ratify_script" in text
    assert 'task(subagent_type="researcher")' in text
    assert 'task(subagent_type="scriptwriter")' in text
    assert "禁止" in text or "Forbidden" in text
    # Controller-only must stay tight; business rules live in skills.
    assert len(text) < 3500, f"producer prompt too long: {len(text)} chars"
```

- [ ] **Step 2: 跑 test，确认 fail（现有 producer.md 应该不含 vm_ratify_script）**

```bash
uv run pytest tests/deepagents_video_maker/test_producer_prompt.py -v
```

- [ ] **Step 3: 重写 `prompts/producer.md`**

```markdown
# Role: video-maker Producer (DeepAgents-native)

你是 video-maker workflow 的 main agent。你的全部职责是按 controller protocol 推进 milestone。
**业务知识不在此 prompt**，subagent 通过 skills 系统自行加载。

## Controller protocol（每次推进 milestone 严格按顺序）

1. inspect_state — 调 `vm_load_state(output_dir)` 或读取 `state.yaml`
2. decide_next_step — 内部推理，输出意图，但不能直接改 state
3. call_typed_tool_or_task — 必须真实调用 typed tool 或 `task(subagent_type=...)`
4. verify_artifact_gate — 必须调用对应 `vm_ratify_*` tool，不能用文本声称 pass
5. update_state_and_todos — 由 ratify 工具内部完成
6. continue_or_block — pass→进下一步；fail→retry 或 blocked

## Milestone sequence（本 phase 仅 research → script）

### Bootstrap
未初始化时：
1. `vm_parse_video_request(prompt)` 解析参数
2. `vm_init_video_session(...)` 创建 output_dir、goal.yaml、state.yaml

### Research milestone
1. `vm_start_research(output_dir)`
2. `vm_build_researcher_task(output_dir, run_number, ...)` 拿到 description
3. `task(subagent_type="researcher", description=<上一步返回的 description>)`
4. `vm_ratify_research(output_dir, run_number, ...)`
5. pass → 进 script；fail → 重新执行 step 2-4（受 max_retries 限制）

### Script milestone
1. `vm_start_script(output_dir)`
2. `vm_build_scriptwriter_task(output_dir, run_number, ...)`
3. `task(subagent_type="scriptwriter", description=<返回的 description>)`
4. `vm_ratify_script(output_dir, ...)`
5. pass → 报告 workflow paused（assets/assembly 后续 phase 实现）；fail → retry/blocked

## Forbidden patterns

- 输出 `<invoke name="task">` 或类似 XML/DSL 文本但不真实发出 tool call
- 在 `vm_ratify_*` 未通过时把 milestone 描述为 completed
- 用自然语言总结来代替 typed tool 调用
- 让 subagent 改 state.yaml 或 goal.yaml（只有 typed tools 能改）
- 在 prompt 内联 researcher/scriptwriter 的业务规则（去 skill 里查）

## Reporting

每完成一个 milestone，简短报告：
- milestone id
- pass/fail
- artifact paths
- next action
```

- [ ] **Step 4: 跑 test，确认 pass**

```bash
uv run pytest tests/deepagents_video_maker/test_producer_prompt.py -v
```

- [ ] **Step 5: Commit**

```bash
git add src/deepagents_video_maker/prompts/producer.md tests/deepagents_video_maker/test_producer_prompt.py
git commit -m "refactor(deepagents-vm): tighten producer prompt to controller-only"
```

---

## Task 6: Subagent prompts 精简为契约-only

**Files:**
- Modify: `src/deepagents_video_maker/prompts/subagents/researcher.md`
- Modify: `src/deepagents_video_maker/prompts/subagents/scriptwriter.md`
- Test: `tests/deepagents_video_maker/test_subagent_prompts.py`

- [ ] **Step 1: 写 failing test**

```python
# tests/deepagents_video_maker/test_subagent_prompts.py
from deepagents_video_maker.prompts import load_subagent_prompt


def test_researcher_prompt_is_contract_only():
    text = load_subagent_prompt("researcher")
    assert "video-researcher" in text  # 引用 skill 名
    assert "research_path" in text
    assert "blocking_issues" in text
    assert "ONE tool call at a time" in text or "一次只发一个" in text
    assert len(text) < 1500, f"researcher prompt too long: {len(text)} chars"


def test_scriptwriter_prompt_is_contract_only():
    text = load_subagent_prompt("scriptwriter")
    assert "video-scriptwriter" in text
    assert "script_path" in text
    assert "manifest_path" in text
    assert "scene_count" in text
    assert len(text) < 1500
```

- [ ] **Step 2: 跑 test，确认 fail**

```bash
uv run pytest tests/deepagents_video_maker/test_subagent_prompts.py -v
```

- [ ] **Step 3: 重写 `prompts/subagents/researcher.md`**

```markdown
# Role: video-maker Researcher subagent

加载 skill: `video-researcher`（已通过 skills 注入；按 SKILL.md 指令执行）。

## Tool discipline

Make ONE tool call at a time. Parallel tool calls trigger HumanInTheLoopMiddleware ValueError.

## Input contract（来自 task.description）

- topic, source, local_file?, excalidraw_file?, output_path
- required_sections, min_chars, visual_strategy

## Output contract（最终 AI message 必须含以下字段）

```
research_path: <path>
summary: <3-5 sentence summary>
section_count: <number>
source_count: <number>
visual_strategy: <image_heavy|image_light|image_none>
blocking_issues: <none or list>
```

## Failure handling

无法写入文件时返回 `blocking_issues`，禁止虚假声明完成。
```

- [ ] **Step 4: 重写 `prompts/subagents/scriptwriter.md`**

```markdown
# Role: video-maker Scriptwriter subagent

加载 skill: `video-scriptwriter`（已通过 skills 注入；按 SKILL.md 指令执行，包括 source-of-truth 文件链）。

## Tool discipline

ONE tool call at a time.

## Input contract

- topic, duration, style, aspect_ratio
- bgm_file, sfx_enabled
- research_file, script_path, manifest_path
- eval_mode

## Output contract

```
script_path: <path>
manifest_path: <path>
scene_count: <number>
estimated_duration: <seconds>
blocking_issues: <none or list>
```

## Hard rules（违反 = ratify 失败）

- script.md 的 `## Scene N` 数量 = manifest.json `scenes[]` 长度
- 每个 manifest scene 必须含 id / narration / duration
- narration/data_card/quote_card 必须含 scene_intent + content_brief
- 禁用 `layer_hint` / `beats`
```

- [ ] **Step 5: 跑 test，确认 pass**

```bash
uv run pytest tests/deepagents_video_maker/test_subagent_prompts.py -v
```

- [ ] **Step 6: Commit**

```bash
git add src/deepagents_video_maker/prompts/subagents tests/deepagents_video_maker/test_subagent_prompts.py
git commit -m "refactor(deepagents-vm): trim researcher/scriptwriter prompts to contract-only"
```

---

## Task 7: agent.py 装配 skills + 精简 subagent 列表

**Files:**
- Test: `tests/deepagents_video_maker/test_agent_factory.py`
- Modify: `src/deepagents_video_maker/agent.py`

- [ ] **Step 1: 写 failing test**

```python
# tests/deepagents_video_maker/test_agent_factory.py
from deepagents_video_maker.agent import (
    SUBAGENT_NAMES,
    build_native_tools,
    build_subagents,
    PROJECT_SKILLS_PATHS,
)


def test_subagent_names_only_research_and_script():
    assert SUBAGENT_NAMES == ["researcher", "scriptwriter"]


def test_each_subagent_has_skills():
    subs = build_subagents()
    by_name = {s["name"]: s for s in subs}
    assert "video-researcher" in by_name["researcher"]["skills"][0]
    assert "video-scriptwriter" in by_name["scriptwriter"]["skills"][0]
    for sub in subs:
        assert "system_prompt" in sub
        assert "description" in sub


def test_project_skills_paths_includes_deepagents_skills():
    assert any("/.deepagents/skills" in p for p in PROJECT_SKILLS_PATHS)


def test_build_native_tools_includes_script_tools():
    names = {t.name for t in build_native_tools()}
    assert "vm_start_script" in names
    assert "vm_ratify_script" in names
```

- [ ] **Step 2: 跑 test，确认 fail**

```bash
uv run pytest tests/deepagents_video_maker/test_agent_factory.py -v
```

Expected: `ImportError: cannot import name 'PROJECT_SKILLS_PATHS'` 和 `SUBAGENT_NAMES != ['researcher', 'scriptwriter']`。

- [ ] **Step 3: 重写 `src/deepagents_video_maker/agent.py`**

```python
"""Agent factory for the DeepAgents-native Video-Maker implementation."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from .langchain_tools import build_langchain_tools
from .prompts import load_prompt, load_subagent_prompt


SUBAGENT_NAMES = ["researcher", "scriptwriter"]

_REPO_ROOT = Path(__file__).resolve().parents[2]

PROJECT_SKILLS_PATHS: list[str] = [
    str(_REPO_ROOT / ".deepagents" / "skills"),
]

_SUBAGENT_DESCRIPTIONS = {
    "researcher": "Research a video topic from web/local sources and write structured research.md.",
    "scriptwriter": "Convert research.md into script.md + manifest.json with scene-typed structure.",
}

_SUBAGENT_SKILL_DIRS = {
    "researcher": str(_REPO_ROOT / ".deepagents" / "skills" / "video-researcher"),
    "scriptwriter": str(_REPO_ROOT / ".deepagents" / "skills" / "video-scriptwriter"),
}


def build_subagents() -> list[dict[str, Any]]:
    return [
        {
            "name": name,
            "description": _SUBAGENT_DESCRIPTIONS[name],
            "system_prompt": load_subagent_prompt(name),
            "skills": [_SUBAGENT_SKILL_DIRS[name]],
        }
        for name in SUBAGENT_NAMES
    ]


def build_native_tools() -> list[Callable[..., Any]]:
    return build_langchain_tools()


def create_video_maker_agent(
    model: Any,
    *,
    project_root: str | Path | None = None,
    interrupt: bool = False,
    backend: Any | None = None,
    checkpointer: Any | None = None,
):
    try:
        from deepagents import create_deep_agent
        from deepagents.backends import FilesystemBackend
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("DeepAgents runtime is required") from exc

    root = Path(project_root or _REPO_ROOT).resolve()
    effective_backend = backend or FilesystemBackend(root_dir=root, virtual_mode=True)

    return create_deep_agent(
        model=model,
        tools=build_native_tools(),
        system_prompt=load_prompt("producer"),
        subagents=build_subagents(),
        skills=PROJECT_SKILLS_PATHS,
        backend=effective_backend,
        checkpointer=checkpointer,
        interrupt_on=({"write_file": True, "edit_file": True} if interrupt else None),
        name="video-maker-producer",
    )
```

- [ ] **Step 4: 跑 test，确认 pass**

```bash
uv run pytest tests/deepagents_video_maker/test_agent_factory.py -v
```

Expected: 4 passed.

- [ ] **Step 5: 跑全量回归**

```bash
uv run pytest tests/deepagents_video_maker -v
```

Expected: 全 pass，没有 regression。

- [ ] **Step 6: Commit**

```bash
git add src/deepagents_video_maker/agent.py tests/deepagents_video_maker/test_agent_factory.py
git commit -m "feat(deepagents-vm): wire skills= into agent factory; trim subagents to research+script"
```

---

## Task 8: 端到端 smoke 脚本（手动验收）

**Files:**
- Create: `scripts/smoke_skills_research_script.py`

- [ ] **Step 1: 写脚本**

```python
# scripts/smoke_skills_research_script.py
"""Manual smoke: run create_video_maker_agent end-to-end on research+script.

Usage:
    set HTTP_PROXY=http://127.0.0.1:7897
    set HTTPS_PROXY=http://127.0.0.1:7897
    uv run python scripts/smoke_skills_research_script.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_REF = REPO_ROOT / ".tmp" / "smoke-attention.md"


def _ensure_sample() -> Path:
    SAMPLE_REF.parent.mkdir(parents=True, exist_ok=True)
    if not SAMPLE_REF.exists():
        SAMPLE_REF.write_text(
            "# Attention Is All You Need\n\n"
            "## Overview\nTransformer abandons RNN/CNN in favor of self-attention.\n\n"
            "## Key Idea\nScaled dot-product attention; multi-head attention.\n\n"
            "## Why It Matters\nEnables parallel training and long-range dependencies.\n",
            encoding="utf-8",
        )
    return SAMPLE_REF


def main() -> int:
    os.environ.setdefault("ORCHESTRATOR_SKILLS_ROOT", str(REPO_ROOT))
    sample = _ensure_sample()

    from deepagents_video_maker.agent import create_video_maker_agent
    from langchain.chat_models import init_chat_model

    model = init_chat_model("anthropic:claude-sonnet-4-6")
    agent = create_video_maker_agent(model=model, project_root=REPO_ROOT)

    prompt = (
        f'make a 60s explainer video on "transformer attention" '
        f"from local file {sample}"
    )
    result = agent.invoke({"messages": [{"role": "user", "content": prompt}]})
    last = result["messages"][-1]
    print("=== final message ===")
    print(getattr(last, "content", last))

    output_root = REPO_ROOT / "output"
    runs = sorted(output_root.glob("*-video-*"))
    if not runs:
        print("FAIL: no output dir created")
        return 1
    latest = runs[-1]
    research = latest / "artifacts" / "research" / "run-1" / "research.md"
    script = latest / "artifacts" / "script" / "run-1" / "script.md"
    manifest = latest / "artifacts" / "script" / "run-1" / "manifest.json"
    for path in (research, script, manifest):
        marker = "[OK]" if path.exists() else "[ERROR]"
        print(f"{marker} {path}")
    return 0 if all(p.exists() for p in (research, script, manifest)) else 1


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: 手动执行 smoke**

```bash
HTTP_PROXY=http://127.0.0.1:7897 HTTPS_PROXY=http://127.0.0.1:7897 \
  uv run python scripts/smoke_skills_research_script.py
```

Expected: 末尾 3 行都是 `[OK]`，并且 trace 里能看到 `task(name="researcher")` 和 `task(name="scriptwriter")` 真实 tool call。

- [ ] **Step 3: 失败路径手动验证**

```bash
# 删除 research.md 后再跑，验证 ratify 进入 retry
rm output/<latest>/artifacts/research/run-1/research.md
HTTP_PROXY=http://127.0.0.1:7897 HTTPS_PROXY=http://127.0.0.1:7897 \
  uv run python scripts/smoke_skills_research_script.py
```

Expected: state.yaml 中 `research.retry_count > 0` 或 `status=blocked`。

- [ ] **Step 4: Commit**

```bash
git add scripts/smoke_skills_research_script.py
git commit -m "test(deepagents-vm): add manual smoke for research+script via skills"
```

---

## Codex Review Patch (2026-04-27)

Codex 独立 review 发现 9 个 P1 + 7 个 P2 问题。**executing agent 必须在跑每个 task 前先读这一节，合并对应 delta。**

### P0 (User finding) — main agent 不能拿整个 .deepagents/skills/ 目录

**问题：** plan 让 `create_deep_agent(skills=PROJECT_SKILLS_PATHS=[".deepagents/skills/"])`（File Structure / Task 7），但 `.deepagents/skills/` 下已有 `video-maker/SKILL.md`，描述是 "End-to-end video production workflow ... Producer/Crew video orchestration"。Progressive disclosure 会让 main Producer 一进入视频任务就匹配并加载这个完整业务 skill，**直接污染 controller-only Producer**，与 plan §Architecture 和 Task 5 producer prompt 的硬约束（"业务知识不在此 prompt"）冲突。

**修复方案：main agent 不传 `skills=`，所有业务 skill 只由 custom subagent 各自配 `skills=`。**

#### Task 7 patch 增量（覆盖原 Task 7 patch 中的 PROJECT_SKILLS_PATHS 部分）

```python
# src/deepagents_video_maker/agent.py
# 删除 PROJECT_SKILLS_PATHS 全局列表
# create_deep_agent 调用不再传 skills=
return create_deep_agent(
    model=model,
    tools=build_native_tools(),
    system_prompt=load_prompt("producer"),
    subagents=build_subagents(),       # 每个 subagent 自带 skills=
    # ⚠ 不传 skills= 给 main agent
    backend=effective_backend,
    checkpointer=checkpointer,
    interrupt_on=({"write_file": True, "edit_file": True} if interrupt else None),
    name="video-maker-producer",
)
```

#### Test 调整（覆盖原 Task 7 patch 中的 `test_project_skills_paths_includes_deepagents_skills`）

```python
def test_main_agent_does_not_load_business_skills():
    """Producer must stay controller-only; business skills go to subagents."""
    import inspect
    from deepagents_video_maker import agent as agent_mod
    # PROJECT_SKILLS_PATHS 不应存在 OR 必须为空 list
    paths = getattr(agent_mod, "PROJECT_SKILLS_PATHS", [])
    assert paths == [], f"main agent must not load skills, got {paths}"

def test_each_subagent_carries_its_own_skill():
    subs = build_subagents()
    by_name = {s["name"]: s for s in subs}
    # researcher only sees its own wrapper, not video-maker producer skill
    rs = by_name["researcher"]["skills"]
    assert len(rs) == 1
    assert "video-researcher" in rs[0]
    assert "video-maker" not in Path(rs[0]).name  # 严防匹配到 producer wrapper

    ss = by_name["scriptwriter"]["skills"]
    assert len(ss) == 1
    assert "video-scriptwriter" in ss[0]
    assert "video-maker" not in Path(ss[0]).name
```

#### 清理动作（Task 4 之前执行）

`.deepagents/skills/video-maker/SKILL.md` 是早期 thin wrapper 实验产物，已被 native subagent prompts + 新的 wrapper skill (`video-researcher` / `video-scriptwriter`) 替代。**作为 Task 0 的一部分删除**：

```bash
git rm -r .deepagents/skills/video-maker/
git commit -m "chore(deepagents-vm): remove obsolete video-maker producer wrapper skill"
```

加 regression test：

```python
# tests/deepagents_video_maker/test_skill_files.py 末尾追加
def test_no_producer_business_skill_in_skills_root():
    """Main Producer must not have a business skill in .deepagents/skills/.
    Only subagent wrappers belong here."""
    if SKILLS_ROOT.exists():
        for skill_dir in SKILLS_ROOT.iterdir():
            if not skill_dir.is_dir():
                continue
            assert skill_dir.name in {"video-researcher", "video-scriptwriter"}, (
                f"unexpected skill dir {skill_dir.name}; only subagent wrappers allowed"
            )
```

#### File Structure delta

修改 plan §File Structure：
- 删除 `PROJECT_SKILLS_PATHS` 提及
- 在 "Untouched" 上方加 "Removed: `.deepagents/skills/video-maker/` (obsolete producer wrapper)"

#### Codex finding 全表追加 1 行

| # | 严重性 | 问题 | 修复位置 |
|---|---|---|---|
| 0 | P0 | main agent 误加载 video-maker 业务 skill 污染 Producer | 本 P0 节 |

### Task 0 (NEW) — Dependencies + virtual-path bootstrap

**Files:**
- Modify: `pyproject.toml`
- Modify: `src/deepagents_video_maker/agent.py` (仅 `create_video_maker_agent` 顶部)

- [ ] **Step 1: 追加 deepagents 依赖到 `pyproject.toml`**

```toml
[project]
dependencies = [
  "deepagents>=1.7.0",
  "langchain>=0.3.0",
  "langchain-core>=0.3.0",
  "langchain-anthropic>=0.3.0",
  "PyYAML>=6.0",
]
```

`uv sync` 验证安装成功。

- [ ] **Step 2: agent factory 必须显式 export `ORCHESTRATOR_SKILLS_ROOT`**

`research_flow._to_virtual_path` / `script_flow._to_virtual_path` 依赖此环境变量；不设的话 subagent 会拿到 Windows 绝对路径，与 SKILL.md "虚拟路径 only" 矛盾。Task 7 的 `create_video_maker_agent` 在确定 `root` 之后立刻：

```python
import os
os.environ.setdefault("ORCHESTRATOR_SKILLS_ROOT", str(root))
```

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml
git commit -m "chore(deepagents-vm): add deepagents/langchain runtime deps"
```

### Task 1 patch — `ratify_script` 加防御 + 业务规则

**额外检查（在原实现上追加）：**

```python
# manifest 顶层必须是 dict
if not isinstance(data, dict):
    checks.append(RatifyCheck("manifest_is_object", False, f"manifest top-level must be object, got {type(data).__name__}"))
    return _result(checks)
checks.append(RatifyCheck("manifest_is_object", True, "manifest top-level is object"))

# 每个 scene 必须是 dict
for idx, scene in enumerate(scenes):
    if not isinstance(scene, dict):
        checks.append(RatifyCheck(f"scene_{idx}_is_object", False, f"scene[{idx}] not an object"))
        return _result(checks)

# duration 必须是正数
for idx, scene in enumerate(scenes):
    duration = scene.get("duration")
    if not isinstance(duration, (int, float)) or duration <= 0:
        checks.append(RatifyCheck(f"scene_{idx}_duration", False, f"scene[{idx}].duration must be positive number, got {duration!r}"))
        return _result(checks)

# scene id 唯一
ids = [s.get("id") for s in scenes]
if len(set(ids)) != len(ids):
    checks.append(RatifyCheck("scene_ids_unique", False, f"duplicate scene ids: {ids}"))
    return _result(checks)
checks.append(RatifyCheck("scene_ids_unique", True, "all scene ids unique"))

# script.md 业务规则（参考 .claude/skills/video-maker/ratify/script-rules.md 规则 5/6）
SCENE_BLOCK = re.compile(r"(?ms)^##\s+Scene\b.*?(?=^##\s+Scene\b|\Z)")
TYPE_RE = re.compile(r"(?m)^type:\s*(\w+)")
for block in SCENE_BLOCK.findall(text):
    type_match = TYPE_RE.search(block)
    stype = type_match.group(1) if type_match else ""
    if stype in {"narration", "data_card", "quote_card"}:
        for required in ("scene_intent:", "content_brief:"):
            if required not in block:
                checks.append(RatifyCheck("scene_required_fields", False, f"{stype} scene missing {required}"))
                return _result(checks)
        for forbidden in ("layer_hint:", "beats:"):
            if forbidden in block:
                checks.append(RatifyCheck("scene_forbidden_fields", False, f"{stype} scene contains forbidden {forbidden}"))
                return _result(checks)
checks.append(RatifyCheck("script_business_rules", True, "scene_intent/content_brief/no-layer_hint OK"))
```

**追加 test：**

```python
def test_ratify_script_fails_when_manifest_is_list(tmp_path):
    script = _write_script(tmp_path)
    bad = tmp_path / "manifest.json"
    bad.write_text("[1, 2, 3]", encoding="utf-8")
    result = ratify_script(script, bad)
    assert not result.passed
    assert any(c.id == "manifest_is_object" and not c.passed for c in result.checks)


def test_ratify_script_fails_when_duration_invalid(tmp_path):
    script = _write_script(tmp_path, scene_count=1)
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"scenes": [{"id": "s1", "narration": "x", "duration": -1}]}), encoding="utf-8")
    result = ratify_script(script, manifest)
    assert not result.passed


def test_ratify_script_fails_when_scene_missing_intent(tmp_path):
    script = tmp_path / "script.md"
    script.write_text("## Scene 1\ntype: narration\nnarration: x\n", encoding="utf-8")  # no scene_intent
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"scenes": [{"id": "s1", "narration": "x", "duration": 5}]}), encoding="utf-8")
    result = ratify_script(script, manifest)
    assert not result.passed


def test_ratify_script_fails_when_scene_uses_layer_hint(tmp_path):
    script = tmp_path / "script.md"
    script.write_text(
        "## Scene 1\ntype: narration\nnarration: x\nscene_intent: hook\ncontent_brief: y\nlayer_hint: bg\n",
        encoding="utf-8",
    )
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"scenes": [{"id": "s1", "narration": "x", "duration": 5}]}), encoding="utf-8")
    result = ratify_script(script, manifest)
    assert not result.passed
```

### Task 2 patch — precondition + 真实 RunInfo + ratify 持久化

**`start_script_milestone` 加 precondition：**

```python
def start_script_milestone(state: VideoMakerState) -> RunInfo:
    research = state.milestone("research")
    if research.status != MilestoneStatus.COMPLETED:
        raise RuntimeError(
            f"cannot start script milestone: research status={research.status.value} (must be completed)"
        )
    return create_milestone_run(state, "script")
```

追加测试 `test_start_script_milestone_requires_research_completed`：状态为 `IN_PROGRESS` 时调用应抛 `RuntimeError`。

**ratify 持久化：** `ratify_and_update_script` 在 `update_milestone_status` 之后写一份 `ratify/script-run-{N}.json`：

```python
import json as _json
ratify_dir = Path(state.output_dir) / "ratify"
ratify_dir.mkdir(parents=True, exist_ok=True)
(ratify_dir / f"script-run-{milestone.current_run}.json").write_text(
    _json.dumps(ratify_payload, indent=2, ensure_ascii=False), encoding="utf-8"
)
```

`research_flow.ratify_and_update_research` 同步加 `ratify/research-run-{N}.json` 写入（plan 之外的 bug fix，否则 ratify 证据全部丢失）。

追加测试断言文件存在且 JSON 可解析。

### Task 3 patch — 保留全参数 + 真实 RunInfo

**`vm_build_scriptwriter_task` 必须带 `_goal_from_inputs` 全套字段（与 `vm_build_researcher_task` 对齐）：**

```python
@_tool
def vm_build_scriptwriter_task(
    output_dir: str,
    run_number: int = 1,
    prompt: str | None = None,
    topic: str | None = None,
    source: str | None = None,
    local_file: str | None = None,
    notebook_url: str | None = None,
    excalidraw_file: str | None = None,
    duration: str | None = None,
    style: str | None = None,
    aspect_ratio: str | None = None,
    quality_threshold: int | None = None,
    eval_mode: str | None = None,
    transition_style: str | None = None,
) -> dict[str, Any]:
    goal = _goal_from_inputs(
        prompt=prompt, topic=topic, source=source, local_file=local_file,
        notebook_url=notebook_url, excalidraw_file=excalidraw_file,
        duration=duration, style=style, aspect_ratio=aspect_ratio,
        quality_threshold=quality_threshold, eval_mode=eval_mode,
        transition_style=transition_style,
    )
    state = load_state_yaml(Path(output_dir) / "state.yaml")
    run_dir = Path(output_dir) / "artifacts" / "script" / f"run-{run_number}"
    from .models import RunInfo
    run_info = RunInfo(milestone="script", run_number=run_number, run_dir=str(run_dir))
    description = build_scriptwriter_task_description(goal, state, run_info)
    return {"subagent_type": "scriptwriter", "description": description, "run_dir": str(run_dir)}
```

**新增 `vm_load_state` tool（producer prompt 引用了它）：**

```python
@_tool
def vm_load_state(output_dir: str) -> dict[str, Any]:
    """Load state.yaml from an existing video-maker output directory."""
    state = load_state_yaml(Path(output_dir) / "state.yaml")
    return {"state": to_jsonable(state), "output_dir": output_dir}
```

并加进 `build_langchain_tools()`。

`vm_ratify_script` 同步保留 `notebook_url` / `excalidraw_file` / `quality_threshold` / `transition_style` 参数。

### Task 4 patch — virtual path 验证

SKILL.md wrapper 用 source-of-truth 路径时，必须用 `/.claude/skills/...`（前导斜杠虚拟路径），不要写 `.claude/skills/...`。Edit 生成的两个 SKILL.md 中所有 `.claude/skills/video-maker/...` 引用都改为 `/.claude/skills/video-maker/...`。

测试追加：

```python
def test_skill_wrappers_reference_virtual_paths():
    for name in ("video-researcher", "video-scriptwriter"):
        text = (SKILLS_ROOT / name / "SKILL.md").read_text(encoding="utf-8")
        # 任何 .claude/skills 引用必须以 / 开头
        for line in text.splitlines():
            if ".claude/skills" in line:
                assert "/.claude/skills" in line, f"{name} has non-virtual path: {line}"
```

### Task 7 patch — append 而非覆盖现有 test 文件

`tests/deepagents_video_maker/test_agent_factory.py` 和 `test_langchain_tools.py` **已存在**。Step 1 的 test 块必须用 `Edit` 工具**追加**到文件末尾，不要 `Write` 覆盖（会删除现有 prompt contract 覆盖）。

执行前先 `Read` 现有 test 文件，新断言加在文件末尾，import 区如有重复保留首份。

**真实实例化烟测**（Task 7 step 5 之后追加）：

```python
def test_create_video_maker_agent_smoke():
    """Verify create_deep_agent accepts our shape (skills=, subagents with skills=)."""
    pytest.importorskip("deepagents")
    from deepagents_video_maker.agent import create_video_maker_agent

    class _DummyModel:
        def bind_tools(self, *_a, **_kw): return self
        def invoke(self, *_a, **_kw): raise NotImplementedError
    # 不真实跑 LLM，只断言工厂调用不抛异常
    agent = create_video_maker_agent(model=_DummyModel(), project_root=tmp_path)
    assert agent is not None
```

如果 deepagents 拒绝 dummy model，把这个 test 标 `@pytest.mark.integration` 并放到 smoke 脚本里跑。

### Task 8 patch — failure path 改为 reuse + PowerShell 命令

**failure-path 重写**（原方案每次新 timestamp 目录，删旧文件无效）：

```python
# scripts/smoke_skills_research_script.py 接受 --reuse-output <dir>
# 用法：第一次跑生成 output/<id>，记录 id；第二次 reuse 同 id 删文件再跑，验证同一 state retry
```

加参数解析：

```python
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--reuse-output", default=None, help="Reuse existing output dir instead of creating new")
parser.add_argument("--delete-research", action="store_true", help="Delete research.md to test retry")
args = parser.parse_args()
```

reuse 时 prompt 改成 `"resume work in {output_dir}"`，并验证 `state.yaml` 里 `research.retry_count > 0`。

**PowerShell 命令**（CLAUDE.md：bash 优先，但 user OS=Windows，写两份）：

```powershell
# Step 2 PowerShell
$env:HTTP_PROXY="http://127.0.0.1:7897"; $env:HTTPS_PROXY="http://127.0.0.1:7897"
uv run python scripts/smoke_skills_research_script.py
```

```powershell
# Step 3 PowerShell — failure path
$latest = (Get-ChildItem output -Directory -Filter "*-video-*" | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName
uv run python scripts/smoke_skills_research_script.py --reuse-output $latest --delete-research
```

**state 校验追加（smoke step 2 内）：**

```python
import yaml  # PyYAML 已加进 deps
state_data = yaml.safe_load((latest / "state.yaml").read_text(encoding="utf-8"))
research_status = next(m["status"] for m in state_data["milestones"] if m["id"] == "research")
script_status = next(m["status"] for m in state_data["milestones"] if m["id"] == "script")
assert research_status == "completed", f"research status={research_status}"
assert script_status == "completed", f"script status={script_status}"

# ratify 证据文件
assert (latest / "ratify" / "research-run-1.json").exists()
assert (latest / "ratify" / "script-run-1.json").exists()
```

### P2 收尾

- `update_milestone_status` 在状态 `COMPLETED` 时设置 `completed_at = datetime.now().isoformat(timespec="seconds")`，且通过时清 `blocking_reason = None`。追加测试覆盖。
- Task 5 producer prompt 删除/替换 `vm_load_state` 引用（如选不实现）— 但本 patch 选实现路径（见 Task 3 patch 新增 tool），prompt 保持不变。

### Codex finding 全表

| # | 严重性 | 问题 | 修复位置 |
|---|---|---|---|
| 1 | P1 | wrapper 引用被禁的 .claude 路径 | Task 4 patch（虚拟路径） |
| 2 | P1 | 虚拟路径前缀缺失 | Task 4 patch |
| 3 | P1 | start_script 不检查 research completed | Task 2 patch |
| 4 | P1 | ratify_script 对 list manifest 崩溃 | Task 1 patch |
| 5 | P1 | ratify 不持久化 | Task 2 patch |
| 6 | P1 | _to_virtual_path env 依赖 | Task 0 patch |
| 7 | P1 | vm_load_state 不存在 | Task 3 patch |
| 8 | P1 | agent factory test 不实例化 | Task 7 patch |
| 9 | P1 | pyproject deps 空 | Task 0 patch |
| 10 | P1 | smoke failure-path 无效 | Task 8 patch |
| 11 | P2 | scene field 类型不验证 | Task 1 patch |
| 12 | P2 | scriptwriter wrapper 缺参数 | Task 3 patch |
| 13 | P2 | RunInfoLike 伪类型 | Task 3 patch |
| 14 | P2 | completed_at / blocking_reason 状态机不全 | P2 收尾 |
| 15 | P2 | smoke state.yaml 不校验 | Task 8 patch |
| 16 | P2 | PowerShell 命令缺失 | Task 8 patch |
| 17 | P2 | test 文件覆盖 vs 追加 | Task 7 patch |

---

## Self-Review

**Spec coverage:**
- §3.1 frontmatter 兼容 → Task 4 (`test_video_*_skill_has_frontmatter`) ✓
- §3.2 thin wrapper 引用 .claude/skills → Task 4 SKILL.md 内容 ✓
- §4.1 主 agent skills= → Task 7 (`test_project_skills_paths_includes_deepagents_skills`) ✓
- §4.2 subagent skills= → Task 7 (`test_each_subagent_has_skills`) ✓
- §4.3 producer prompt controller-only → Task 5 ✓
- §4.4 subagent prompts 契约-only → Task 6 ✓
- §5.2 ratify_script 等新 tools → Task 1, Task 3 ✓
- §6 实现步骤全 8 步 → Task 1-8 ✓
- §7 验收标准（skill 加载、真实 task 调用、ratify pass、状态准确）→ Task 7 (factory test) + Task 8 (smoke) ✓

**Placeholder scan:** 无 TBD/TODO/"添加适当错误处理"。所有代码块都是完整可执行内容。

**Type consistency:**
- `RatifyResult` / `RatifyCheck` 来自 `models.py`（已存在）
- `start_script_milestone` / `build_scriptwriter_task_description` / `ratify_and_update_script` 在 Task 2 创建，Task 3 import，签名一致 ✓
- `vm_start_script` / `vm_build_scriptwriter_task` / `vm_ratify_script` 名字在 Task 3 实现，Task 7 测试断言，名字一致 ✓
- `SUBAGENT_NAMES` / `PROJECT_SKILLS_PATHS` 在 Task 7 创建并测试，与 agent.py 一致 ✓
- `_SUBAGENT_SKILL_DIRS` 路径与 Task 4 创建的 `.deepagents/skills/video-{researcher,scriptwriter}` 一致 ✓

---

## Execution Handoff

Plan 已保存到 `docs/plans/2026-04-26-deepagents-skills-research-script.md`。

**两种执行方式：**

1. **Subagent-Driven（推荐）** — 每个 Task 派发 fresh subagent，task 之间双阶段 review，迭代快，污染主 context 少
2. **Inline Execution** — 在当前 session 顺序跑，checkpoint 处暂停 review

要走哪种？
