# DeepAgents-native Video-Maker 实现计划

日期：2026-04-25  
状态：draft  
目标：在 DeepAgents 原生 agent/subagent/filesystem/HITL 模型内重建 video-maker，而不是把 workflow 拆成手写 LangGraph nodes。

## 1. 设计立场

本计划区别于兼容 adapter 计划：

- 兼容 adapter：读取 `.claude/skills/video-maker`，让旧 Claude Code skill 在 DeepAgents 里先跑起来。
- DeepAgents-native：保留 video-maker 的 Producer/Crew 架构，但用 DeepAgents 原生能力重新组织 workflow、tools、subagents、artifacts、HITL 和 UI。

明确不做：

- 不把每个 milestone 拆成独立 LangGraph node。
- 不把 Producer 降级成固定 DAG executor。
- 不把 subagent 协作替换成纯 Python pipeline。

明确要做：

- Producer 仍是 DeepAgents 主 agent。
- Researcher / Scriptwriter / Evaluator / Reviewer / Editor 仍是 DeepAgents subagents。
- LangGraph 只作为 DeepAgents runtime/backend。
- milestone control 不再靠自由发挥的大 prompt，而是靠 DeepAgents-native controller protocol、typed tools、artifact gates、subagent contracts 和 state/todos 闭环。

## 2. 目标架构

```text
User
  ↓
DeepAgents UI
  ↓
LangGraph dev backend
  ↓
DeepAgents main agent: video-maker-producer
  ├─ controller protocol
  ├─ typed tools
  ├─ filesystem backend
  ├─ HITL interrupts
  └─ task subagents
       ├─ researcher
       ├─ scriptwriter
       ├─ evaluator
       ├─ reviewer
       ├─ editor
       ├─ scene-batch-generator
       └─ scene-patch-generator
```

核心分层：

```text
deepagents-native prompt layer
  - Producer controller prompt
  - Subagent role prompts

typed tool layer
  - session init
  - params derive
  - artifact gate
  - ratify
  - CLI execution
  - state/todos sync

artifact layer
  - goal.yaml
  - state.yaml
  - research.md
  - script.md
  - manifest.json
  - eval JSON
  - scene assets
  - final video

UI layer
  - chat
  - approval
  - milestone cockpit
  - artifact/media preview
```

## 3. Repository layout

当前 repo 主体是 TypeScript orchestrator：

```text
package.json
src/agent/*.ts
vitest
playwright
```

DeepAgents-native video-maker 作为 **Python sidecar package** 引入，服务于 LangGraph/DeepAgents backend；它不替换现有 TypeScript orchestrator，也不混入 `src/agent` 的 TS runtime。

新增 Python package：

```text
pyproject.toml
src/deepagents_video_maker/
  __init__.py
  agent.py
  controller.py
  models.py
  params.py
  session.py
  state_store.py
  artifacts.py
  ratify.py
  tools.py
  prompts/
    producer.md
    subagents/
      researcher.md
      scriptwriter.md
      evaluator.md
      reviewer.md
      editor.md
      scene-batch-generator.md
      scene-patch-generator.md
tests/deepagents_video_maker/
  test_params.py
  test_session.py
  test_state_store.py
  test_ratify_research.py
  test_artifact_gates.py
  test_interrupt_decisions.py
  test_tool_call_dropout_detection.py
```

测试命令：

```powershell
uv run pytest tests/deepagents_video_maker
```

`.claude/skills/video-maker/` 的定位：

```text
.claude/skills/video-maker/
```

迁移阶段不应过早弃用它：

- Phase 1-5：仍是业务知识和 CLI/template source of truth。
- Phase 6+：将稳定下来的规则逐步迁入 native prompts/tools。
- 全部迁完前，不删除或破坏原 skill。

DeepAgents UI backend 入口改为：

```text
deepagent-video-maker-ui/agent/agent.py
```

导入：

```python
from deepagents_video_maker.agent import create_video_maker_agent

agent = create_video_maker_agent(...)
```

## 4. Controller protocol

Controller protocol 是 DeepAgents-native 的核心。它不是 LangGraph node DAG，而是 Producer 必须遵守的步骤协议。

Producer 每次推进 milestone 时，必须遵守：

```text
1. inspect_state
2. decide_next_step
3. call_typed_tool_or_task
4. verify_artifact_gate
5. update_state_and_todos
6. continue_or_block
```

禁止：

- 只输出“我将调用 researcher”但没有真实 `task`。
- 只说“文件已写入”但不经过 artifact gate。
- `research.md` 不存在时进入 script。
- 用自然语言替代 state transition。

### 4.1 Protocol actions

```text
parse_goal
derive_params
init_session
inspect_state
start_milestone
delegate_subagent
ratify_artifact
complete_milestone
retry_milestone
block_for_user
```

这些 action 通过 typed tools 和 prompt contract 共同实现。

### 4.2 Protocol boundary

为避免 controller protocol 再次退化成“靠 prompt 自觉执行”，每个 action 必须归类。

Prompt-only：

```text
decide_next_step
summarize_blocker
compose_user_question
```

这些 action 允许 Producer 用自然语言推理，但不能直接改变 workflow state。

Typed tools：

```text
parse_video_request
derive_video_params
init_video_session
load_video_state
save_video_state
start_milestone
create_milestone_run
ratify_research
ratify_script
ratify_assets
ratify_assembly
update_milestone_status
collect_artifacts
detect_tool_call_dropout
```

这些 action 必须通过工具调用完成，不能只用文本声称完成。

Subagent task：

```text
task(subagent_type="researcher")
task(subagent_type="scriptwriter")
task(subagent_type="evaluator")
task(subagent_type="reviewer")
task(subagent_type="editor")
task(subagent_type="scene-batch-generator")
task(subagent_type="scene-patch-generator")
```

这些 action 必须是真实 DeepAgents `task` tool call。禁止输出 XML/DSL 伪调用。

State transition rule：

```text
任何 milestone status 变化必须来自 typed tool result。
任何 milestone completed 必须先通过 artifact gate。
任何 artifact missing 都必须进入 retry 或 blocked。
```

## 5. Typed models

建议用 `pydantic` 或 dataclass。

```text
VideoMakerGoal
  topic
  source
  local_file
  notebook_url
  excalidraw_file
  duration
  style
  aspect_ratio
  quality_threshold
  eval_mode
  transition_style
  derived params

VideoMakerState
  output_dir
  workflow_status
  milestones
  todos
  artifacts

MilestoneState
  id
  status
  current_run
  retry_count
  max_retries
  started_at
  completed_at
  ratify

ArtifactRef
  kind
  path
  exists
  size
  metadata

RatifyResult
  pass
  checks
  issues
  next_action
```

## 6. Typed tools

### 6.1 Session/state tools

```text
parse_video_request(prompt) -> VideoMakerGoal
derive_video_params(goal) -> VideoMakerGoal
init_video_session(goal) -> VideoMakerState
load_video_state(output_dir) -> VideoMakerState
save_video_state(state) -> ArtifactRef
update_milestone_status(output_dir, milestone, status, patch) -> VideoMakerState
```

### 6.2 Artifact tools

```text
create_milestone_run(output_dir, milestone) -> RunInfo
artifact_exists(path) -> ArtifactRef
collect_artifacts(output_dir) -> ArtifactIndex
read_artifact_summary(path) -> ArtifactSummary
```

### 6.3 Ratify tools

```text
ratify_research(research_path, source) -> RatifyResult
ratify_script(script_path, manifest_path, contract_path?) -> RatifyResult
ratify_assets(output_dir) -> RatifyResult
ratify_assembly(final_video_path) -> RatifyResult
```

### 6.4 CLI tools

```text
run_video_cli(args, cwd) -> CliResult
run_tts(scene_path) -> CliResult
run_whisper(audio_path) -> CliResult
run_scene_render(scene_id) -> CliResult
run_assembly(output_dir) -> CliResult
```

### 6.5 HITL tools / interrupts

通过 DeepAgents/LangGraph interrupt 实现：

```text
approval_request(action) -> interrupt
scene_preview_approval(scene_id, preview_path) -> interrupt
```

UI 必须能处理：

- single approval
- batch approval
- edit args
- reject with feedback

必须覆盖真实已知错误：

```text
ValueError: Number of human decisions (1) does not match number of hanging tool calls (2).
```

规则：

- 同一个 interrupt 中如果有 `N` 个 `action_requests`，resume payload 必须包含 `N` 个 decisions。
- 单项 approve 模式必须能为其他 pending actions 生成明确 decision，或禁止单项提交并提示使用 batch approve。
- batch approve 必须一次性提交所有 pending decisions。
- resume 后必须验证 thread 不再停留在相同 interrupt error。

## 7. Subagent contracts

### 7.1 Researcher

Input：

```text
topic
source
local_file
excalidraw_file
output_path
required_sections
min_chars
visual_strategy
```

Required behavior：

- 读取输入路径。
- 写入 `research.md`。
- 返回 JSON-ish summary，不返回全文。

Output contract：

```text
research_path
summary
section_count
source_count
visual_strategy
blocking_issues
```

Artifact gate：

- `research.md` exists
- size > 800 chars
- `## ` heading >= 3
- local-file source 可跳过 URL 强制要求

### 7.2 Scriptwriter

Input：

```text
research_path
output_dir
duration
style
aspect_ratio
eval_mode
feedback
```

Output：

```text
script_path
manifest_path
scene_count
estimated_duration
blocking_issues
```

Gate：

- `script.md` exists
- `manifest.json` exists
- scene count > 0
- manifest schema valid

### 7.3 Evaluator / Reviewer

Output：

```text
eval_path
pass
score
issues
recommendations
```

Gate：

- JSON parseable
- contains pass/score/issues

### 7.4 Editor / scene generators

Output：

```text
scene_files
preview_paths
compile_result
lint_result
blocking_issues
```

Gate：

- generated files exist
- compile/lint pass
- preview exists before HITL approval

## 8. Milestone flow

### 8.1 Research

```text
inspect_state
start_milestone(research)
create_milestone_run
task(researcher)
ratify_research
complete_milestone or retry_milestone
```

Hard rule：

```text
research.md 不存在 => 不能进入 script
```

### 8.2 Script

```text
start_milestone(script)
task(scriptwriter)
ratify_script
if eval_mode=gan:
  task(evaluator)
  apply feedback if needed
complete_milestone or retry_milestone
```

### 8.3 Assets

```text
start_milestone(assets)
generate audio/captions/images
task(scene-batch-generator)
for each scene:
  compile/lint/render preview
  HITL approve/reject/edit
complete_milestone or retry_milestone
```

### 8.4 Assembly

```text
start_milestone(assembly)
run assembly CLI
ratify final video
complete workflow
```

## 9. UI requirements

DeepAgents-native UI 应从通用 chat 逐步升级为 workflow cockpit。

### 9.1 Required panels

```text
Chat
Pending Approval
Goal Params
Milestone Timeline
Subagent Activity
Artifacts
Media Preview
Ratify/Eval Results
```

### 9.2 Milestone timeline

状态：

```text
pending
in_progress
interrupted
blocked
completed
failed
```

### 9.3 Artifact preview

支持：

- Markdown preview
- JSON preview
- image preview
- audio preview
- video preview
- scene preview screenshots

## 10. Observability

LangSmith tracing 要求：

Root：

```text
video-maker-producer
```

Tool/task spans：

```text
parse_goal
init_session
researcher
ratify_research
scriptwriter
evaluator
ratify_script
assets
scene_preview_approval
assembly
```

Metadata：

```text
session_id
output_dir
milestone
run_number
artifact_paths
model
provider
```

## 11. Test plan

### 11.1 Unit tests

```text
tests/deepagents_video_maker/test_params.py
tests/deepagents_video_maker/test_session.py
tests/deepagents_video_maker/test_state_store.py
tests/deepagents_video_maker/test_ratify_research.py
tests/deepagents_video_maker/test_artifact_gates.py
tests/deepagents_video_maker/test_subagent_contracts.py
tests/deepagents_video_maker/test_interrupt_decisions.py
tests/deepagents_video_maker/test_tool_call_dropout_detection.py
```

### 11.2 Smoke tests

1. local-file research only
2. local-file research + script
3. interrupted write approval resume
4. multiple approval decisions
5. subagent says done but artifact missing
6. resume incomplete session
7. tool-call dropout: AI outputs pseudo `<invoke name="task">` text but no real tool call

### 11.3 Regression cases from current failures

#### HITL decision mismatch

Input：

```text
interrupt.action_requests.length = 2
UI clicks approve
```

Expected：

```text
resume payload decisions.length = 2
no ValueError
thread continues
```

#### Tool-call dropout

Input：

```text
last AI message has no tool_calls
content contains "<sop_invocation>" or "<invoke name=\"task\">" or "DSML"
state.yaml says research in_progress
research.md missing
```

Expected：

```text
detect_tool_call_dropout -> true
milestone status -> blocked or retry
no silent idle success
UI shows blocker reason
```

## 12. Implementation phases

### Phase 1 — Python sidecar foundation

交付：

```text
pyproject.toml
src/deepagents_video_maker/
tests/deepagents_video_maker/
```

实现：

- typed models
- params derive
- session init
- state read/write
- artifact refs
- deterministic request parser for key-value prompts
- pytest configuration

验收：

- 不调用 LLM 也能创建 session。
- `goal.yaml` / `state.yaml` 合法。
- `uv run pytest tests/deepagents_video_maker` 可运行。

### Phase 2 — Typed tools and artifact gates

实现：

```text
init_video_session
create_milestone_run
ratify_research
collect_artifacts
update_milestone_status
detect_tool_call_dropout
```

验收：

- research gate 可独立测试。
- state transition 不依赖 fragile text edit。
- tool-call dropout 可独立检测。

### Phase 3 — Native producer prompt and subagent prompts

交付：

```text
src/deepagents_video_maker/prompts/producer.md
src/deepagents_video_maker/prompts/subagents/*.md
```

实现：

- controller protocol 写入 producer prompt。
- subagent prompts 改成 contract-first。
- prompts 仍可参考 `.claude/skills/video-maker/agents/*.md`，但不直接照搬大段自由 workflow。
- 明确哪些步骤必须调用 typed tools，哪些步骤必须调用 `task`。

验收：

- Producer prompt 中禁止伪 tool call。
- Subagent prompt 明确 output contract。

### Phase 4 — DeepAgents agent factory

实现：

```text
create_video_maker_agent(model, interrupt, backend)
```

替换：

```text
scripts/deepagents_video_maker.py
deepagent-video-maker-ui/agent/agent.py
```

验收：

- backend assistant 仍为 `video-maker`。
- 可从 UI 创建 thread。

### Phase 5 — Research milestone native flow

实现：

- Producer 调用 `init_video_session`
- Producer 调用 `task(researcher)`
- Producer 调用 `ratify_research`
- Producer 更新 state/todos

验收：

- local-file prompt 能稳定生成 `research.md`。
- 没有 `research.md` 时不会进入 script。
- 如果 Producer 输出伪 tool call 文本但未真实调用 `task`，系统进入 blocked/retry。

### Phase 6 — Script + evaluator native flow

实现：

- Scriptwriter contract
- manifest gate
- evaluator contract
- retry feedback loop

验收：

- research pass 后生成 script/manifest。
- eval fail 时进入 retry 或 blocked。

### Phase 7 — Assets / scene HITL

实现：

- scene generation contracts
- render preview gate
- UI approval resume

验收：

- 每个 scene preview 进入 HITL。
- approve 后继续下一 scene。
- 多 action approval 不再触发 decision count mismatch。

### Phase 8 — Assembly and final verification

实现：

- assembly CLI wrapper
- final video ratify
- final summary

验收：

- `final/video.mp4` 存在。
- workflow status = completed。

### Phase 9 — UI cockpit

实现：

- milestone timeline
- artifact preview
- media preview
- ratify/eval panel

验收：

- 用户不用翻 chat 就能知道当前状态、产物和阻塞点。

## 13. First concrete next step

建议从 Phase 1 开始，先只做 Python sidecar foundation：

```text
pyproject.toml
src/deepagents_video_maker/models.py
src/deepagents_video_maker/params.py
src/deepagents_video_maker/session.py
src/deepagents_video_maker/state_store.py
src/deepagents_video_maker/artifacts.py
```

并先加测试：

```text
tests/deepagents_video_maker/test_params.py
tests/deepagents_video_maker/test_session.py
tests/deepagents_video_maker/test_ratify_research.py
tests/deepagents_video_maker/test_tool_call_dropout_detection.py
```

第一阶段不接 LLM，不改 UI，不改 backend，只把 native implementation 的可测试基础打好。

Phase 1 完成标准：

```powershell
uv run pytest tests/deepagents_video_maker
```

必须通过。
