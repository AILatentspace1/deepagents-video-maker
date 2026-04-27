# 可定制化 Workflow 架构设计

日期：2026-04-25  
状态：draft  
目标：在 DeepAgents-native Python sidecar 的基础上，引入三层分离设计，使新 workflow（如 podcast-maker、blog-writer）可在不改动 runtime 代码的情况下通过声明式配置实现。

## 1. 问题与动机

`2026-04-25-deepagents-native-video-maker-implementation.md` 的 Phase 1-8 计划把 milestone 序列、subagent contract、ratify 规则、artifact gate 全部硬编在 Python 里（`controller.py / tools.py / prompts/`）。

这与现有 `.claude/skills/video-maker/` SKILL 版本相比反而是退步：

| 维度 | SKILL 版本（当前） | Native 计划（原版） |
|------|------------------|-------------------|
| milestone 序列 | `_pipeline.yaml` 声明式 | `controller.py` 硬编 |
| subagent prompt | `agents/*.md` 单独文件 | `prompts/subagents/*.md` 但与 runtime 强耦合 |
| ratify 规则 | `ratify/*.md` 单独文件 | `tools.py / ratify.py` 硬编 |
| 新增 workflow | 新建 skill 目录 | 需改 Python 代码 |

**核心要求**：把 workflow definition（数据）和 workflow runtime（通用 Python）解耦，继承 SKILL 版本已有的声明式模式。

## 2. 三层架构

```text
┌─────────────────────────────────────────────┐
│  Layer 1: Workflow Definition Layer          │
│  (per-workflow, data + markdown)             │
│  workflows/<name>/pipeline.yaml             │
│  workflows/<name>/milestones/*.md           │
│  workflows/<name>/agents/*.md              │
│  workflows/<name>/ratify/*.yaml            │
│  workflows/<name>/params.py  (可选)        │
├─────────────────────────────────────────────┤
│  Layer 2: Workflow Runtime Layer             │
│  (通用 Python，所有 workflow 共用)           │
│  src/deepagents_video_maker/controller.py   │
│  src/deepagents_video_maker/tools.py        │
│  src/deepagents_video_maker/subagent_factory│
│  src/deepagents_video_maker/ratify_engine   │
├─────────────────────────────────────────────┤
│  Layer 3: Plugin Hook Layer                  │
│  (可选 Python，escape hatch)                │
│  workflows/<name>/hooks/params_resolver.py  │
│  workflows/<name>/hooks/custom_tools.py     │
│  workflows/<name>/hooks/ratify_callbacks.py │
└─────────────────────────────────────────────┘
```

## 3. Layer 1：Workflow Definition Layer

### 3.1 目录结构

```text
workflows/
└── video-maker/
    ├── pipeline.yaml           # milestone 序列 + 转移规则
    ├── milestones/
    │   ├── research.md         # milestone-level prompt（注入 producer）
    │   ├── script.md
    │   ├── assets.md
    │   └── assembly.md
    ├── agents/
    │   ├── researcher.md       # subagent prompt + contract（YAML frontmatter）
    │   ├── scriptwriter.md
    │   ├── evaluator.md
    │   ├── reviewer.md
    │   ├── editor.md
    │   ├── scene-batch-generator.md
    │   └── scene-patch-generator.md
    ├── ratify/
    │   ├── research.yaml       # gate 规则（schema 声明 + callback ref）
    │   ├── script.yaml
    │   ├── assets.yaml
    │   └── assembly.yaml
    └── params.py               # 参数派生（可选 escape hatch）
```

### 3.2 `pipeline.yaml` 格式

```yaml
workflow_id: video-maker
version: "1.0"

params_resolver: params.py          # 可选，指向 Layer 3 hook

milestones:
  - id: research
    subagent: researcher
    outputs:
      - kind: research_md
        path: "research.md"
    ratify: ratify/research.yaml
    retry:
      max_retries: 2
      strategy: retry_with_feedback
    hitl: none

  - id: script
    depends_on: [research]
    subagent: scriptwriter
    outputs:
      - kind: script_md
        path: "script.md"
      - kind: manifest_json
        path: "manifest.json"
    ratify: ratify/script.yaml
    retry:
      max_retries: 2
      strategy: retry_with_feedback
    hitl: none

  - id: assets
    depends_on: [script]
    subagent: scene-batch-generator
    outputs:
      - kind: scene_tsx
        path: "generated/scene-*.tsx"
        pattern: glob
    ratify: ratify/assets.yaml
    retry:
      max_retries: 3
      strategy: scene_patch
      patch_subagent: scene-patch-generator
    hitl:
      trigger: per_scene_preview
      approval_mode: batch

  - id: assembly
    depends_on: [assets]
    subagent: null                  # 纯 CLI，无 LLM subagent
    cli_tool: run_assembly
    outputs:
      - kind: final_video
        path: "final/video.mp4"
    ratify: ratify/assembly.yaml
    hitl: none
```

### 3.3 `agents/*.md` frontmatter contract

每个 agent markdown 文件以 YAML frontmatter 声明 input/output contract，prompt 正文作为 subagent system prompt 模板：

```markdown
---
agent_id: researcher
input_schema:
  topic: string
  source: string
  local_file: string?
  excalidraw_file: string?
  output_path: string
  required_sections: list[string]
  min_chars: int
  visual_strategy: enum[image_heavy, image_light, image_none]

output_contract:
  research_path: string
  summary: string
  section_count: int
  source_count: int
  visual_strategy: string
  blocking_issues: list[string]

artifact_gate:
  - check: file_exists
    path: "{{research_path}}"
  - check: min_size
    path: "{{research_path}}"
    bytes: 800
  - check: heading_count
    path: "{{research_path}}"
    pattern: "^## "
    min: 3
---

你是一个专业的视频调研专家...（prompt 正文）
```

### 3.4 `ratify/*.yaml` 格式

```yaml
ratify_id: research
checks:
  - name: file_exists
    type: artifact_exists
    path: "research.md"

  - name: min_size
    type: file_size
    path: "research.md"
    min_bytes: 800

  - name: heading_structure
    type: regex_count
    path: "research.md"
    pattern: "^## "
    min: 3

  - name: no_placeholder
    type: regex_not_match
    path: "research.md"
    pattern: "\\[TODO\\]|\\[PLACEHOLDER\\]"

# 可选：指向 Layer 3 callback
custom_callback: hooks/ratify_callbacks.py::check_research_sources
```

## 4. Layer 2：Workflow Runtime Layer

Runtime 层不写任何 workflow 特定逻辑，全部从 `pipeline.yaml` + `agents/*.md` + `ratify/*.yaml` 读取配置执行。

### 4.1 核心模块职责

```text
src/deepagents_video_maker/
├── workflow_loader.py      # 加载 workflows/<name>/ 目录，解析 pipeline.yaml + agents + ratify
├── controller.py           # 通用 protocol executor（从 pipeline.yaml 读状态机）
├── subagent_factory.py     # 从 agents/*.md frontmatter + prompt 生成 DeepAgents subagent
├── ratify_engine.py        # 从 ratify/*.yaml 执行 gate checks（dispatch 到内置 check 类型）
├── tools.py                # 通用 typed tools（init_session/save_state/collect_artifacts/...）
├── models.py               # Pydantic models（WorkflowDefinition, MilestoneState, RatifyResult...）
└── plugin_registry.py      # 注册/发现 Layer 3 hook
```

### 4.2 `controller.py` 核心逻辑

```python
class WorkflowController:
    def __init__(self, workflow_def: WorkflowDefinition, state: VideoMakerState):
        self.workflow = workflow_def
        self.state = state

    def next_milestone(self) -> MilestoneDefinition | None:
        """从 pipeline.yaml 的 depends_on 图计算下一个可执行 milestone。"""
        ...

    def execute_milestone(self, milestone: MilestoneDefinition) -> MilestoneResult:
        """通用执行：dispatch subagent / cli_tool → ratify → update state。"""
        ...
```

`controller.py` 不知道"research"、"script"、"assets"这些名字 — 这些都在 `pipeline.yaml` 里。

### 4.3 `subagent_factory.py`

```python
def create_subagent(agent_def: AgentDefinition, inputs: dict) -> SubagentTask:
    """
    从 agents/*.md 的 frontmatter contract + prompt 正文
    + inputs 渲染出 DeepAgents subagent task。
    """
    prompt = render_template(agent_def.prompt_template, inputs)
    return SubagentTask(
        subagent_type=agent_def.agent_id,
        system_prompt=prompt,
        input_schema=agent_def.input_schema,
        output_contract=agent_def.output_contract,
    )
```

### 4.4 `ratify_engine.py`

```python
class RatifyEngine:
    # 内置 check 类型注册表
    _built_in_checks: dict[str, CheckFn] = {
        "artifact_exists": check_file_exists,
        "file_size": check_file_size,
        "regex_count": check_regex_count,
        "json_schema": check_json_schema,
        ...
    }

    def ratify(self, ratify_def: RatifyDefinition, context: dict) -> RatifyResult:
        results = [self._run_check(c, context) for c in ratify_def.checks]
        if ratify_def.custom_callback:
            results.append(self._run_callback(ratify_def.custom_callback, context))
        return RatifyResult.from_checks(results)
```

## 5. Layer 3：Plugin Hook Layer

在不改动 runtime 的情况下，为特定 workflow 注入自定义逻辑。

```text
workflows/video-maker/hooks/
├── params_resolver.py      # 自定义参数推导（replace 或 extend 默认逻辑）
├── custom_tools.py         # 注册额外 typed tool
└── ratify_callbacks.py     # ratify 自定义 callback（复杂 Python 逻辑）
```

### 5.1 注册方式

通过 workflow `pipeline.yaml` 的 `params_resolver` 字段 + ratify `custom_callback` 字段按需引入，不改 runtime 模块，不用 entry-point。

### 5.2 使用约束

- Hook 必须无副作用（不直接写 state）
- Hook 输出须符合明确 return type（TypedDict / Pydantic）
- Hook 失败视为 ratify fail，进入 retry/blocked，不 silently 跳过

## 6. 新 workflow 如何接入

以 `podcast-maker` 为例，只需：

```text
workflows/podcast-maker/
├── pipeline.yaml           # 定义 research→transcript→audio→assembly 序列
├── agents/
│   ├── researcher.md
│   └── transcript-writer.md
├── ratify/
│   ├── research.yaml
│   └── transcript.yaml
└── params.py               # podcast 专属参数派生（duration/speaker_count...）
```

runtime 代码零改动，`WorkflowController` 加载 `podcast-maker/pipeline.yaml` 就能运行。

## 7. 与原 Native 计划的映射

| 原 Native 计划 | 三层架构映射 |
|--------------|------------|
| `prompts/producer.md` | runtime `controller.py` + 各 workflow `pipeline.yaml` 注入的 milestone prompts |
| `prompts/subagents/*.md` | `workflows/<name>/agents/*.md` (Layer 1) |
| `ratify.py ratify_research()` | `workflows/<name>/ratify/research.yaml` + `ratify_engine.py` dispatch |
| `tools.py` typed tools | `tools.py` 保留但不写 workflow 特定逻辑 |
| `models.py` | 保留，新增 `WorkflowDefinition / AgentDefinition / RatifyDefinition` |

原计划的 Phase 1-8 步骤保持不变，只需在实现时把 workflow 特定内容导向 Layer 1 文件而不是 Python 硬编。

## 8. 分步实现建议

**Phase 1（保守版，第一步）**：
只外置 milestone 序列和 subagent 名字到 `pipeline.yaml`，ratify 和 agent contract 仍可先用 Python，等跑通 video-maker 后再声明化。

**Phase 2**：
`agents/*.md` frontmatter contract 上线，`subagent_factory.py` 从 markdown 读 schema 而不是硬编。

**Phase 3**：
`ratify/*.yaml` 上线，`ratify_engine.py` dispatch 内置 check 类型，减少 `ratify.py` 里的 if-else。

**第二个 workflow 落地时**：
Layer 3 plugin hook 按需引入，不提前设计。

## 9. 主要 Tradeoff

| 优点 | 风险 |
|------|------|
| 新 workflow 不改 Python | schema 设计不当会导致频繁 escape 到 Python |
| 声明式配置可 diff/review | YAML 越复杂越难调试 |
| runtime 可独立测试 | 初期工程投入比直接硬编高 |
| 继承现有 SKILL 版本的可维护性 | |

**原则**：三层架构不是一次全上，从 `pipeline.yaml` milestone 序列开始，逐步声明化。有第二个 workflow 需求之前，不要过度设计 plugin 系统。
