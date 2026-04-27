# Research: DeepAgents video-maker Skill — 端到端 AI 视频制作系统

## 1. Overview — 什么是 video-maker skill

**video-maker** 是 DeepAgents 生态中的核心生产技能（skill），它将一个自然语言视频创意自动转化为完整的 MP4 视频文件。该技能采用 **Producer-Crew 多 Agent 架构**，以 Claude Code 会话为 Producer（制片人），通过 Agent 工具派发专业子 Agent（Crew），完成从调研、脚本、素材生成到最终渲染的全流程。

**核心能力矩阵**：

| 维度 | 说明 |
|------|------|
| 输入 | 自然语言话题描述 + 可选参数（风格、时长、色彩主题、视觉策略） |
| 输出 | 完整 MP4 视频 + thumbnail + 结构化素材目录 |
| 最大时长 | 受 API token 和渲染资源约束，典型为 1-10 分钟 |
| 语言 | 默认中文，支持多语言 TTS |
| 素材策略 | 可选图片素材，也可纯图元渲染 |

**适用场景**：知识科普视频、产品介绍、数据报告可视化、教程讲解、品牌宣传短片。video-maker 填补了"文本大纲 → 成品视频"之间的自动化鸿沟，无需用户具备视频剪辑、配音或动画设计能力。

---

## 2. Architecture — Controller Protocol & Milestone Flow

### Producer-Crew 模式

系统采用平面式多 Agent 架构（非 LangGraph 图结构），核心角色：

```
User → Producer (SKILL.md ~120行) → Crew Agents
         ├── Researcher      (调研 Agent)
         ├── Scriptwriter    (脚本 Agent)
         ├── 无独立 Agent     (Assets 由 Producer 直接驱动 Pipeline CLI)
         └── Reviewer        (质量评审 Agent)
         └── Evaluator       (GAN 模式质量评估 Agent)
```

### Controller Protocol

Producer 通过**类型化 Agent 工具**与子 Agent 通信。每个 Agent 接收严格定义的 prompt 模板（含输入路径、控制参数），输出固定格式的 artifact 文件（Markdown / JSON）。跨里程碑通信通过**文件路径**而非内联摘要传递：

1. Producer 构建 Task（含输入路径）
2. 派发 Subagent（通过 Agent 工具）
3. Subagent 自行读取 artifact 文件（research.md / script.md / manifest.json）
4. Subagent 产出写入 `artifacts/{milestone}/run-{N}/`
5. Producer 执行 Ratify（L1 规则 + L2 LLM 评审）

### 里程碑流水线

三个顺序里程碑，每个通过 Ratify 验收后才进入下一个：

```
Research ──Ratify──→ Script ──Ratify──→ Assets (含逐场景渲染+组装) ──Ratify──→ Done
```

关键设计原则：
- **Subagent 自行读文件**：Producer 只传路径和控制参数，不裁剪 summary
- **每个里程碑的每次尝试存入独立 run-{N} 目录**：支持中断恢复和重试
- **Assembly 已合并入 Assets**：从 4 里程碑精简为 3 里程碑

### 状态管理

```
output/{timestamp}-video-{slug}/
├── goal.yaml           # 用户参数（不可变）
├── state.yaml          # 运行时状态（里程碑进度、retry count）
├── manifest.json       # 场景清单
├── artifacts/          # Agent 产出（research/script/assets）
├── scene-{NN}/         # 逐场景素材（audio.wav, captions.srt, image_*.png）
├── final/              # 最终输出（video.mp4, thumbnail.jpg）
└── ratify/             # 质量评审记录
```

---

## 3. Core Components — Subagent Types

### 5 个专业 Agent

| Agent | 职责 | 输入 | 输出 |
|-------|------|------|------|
| **Researcher** | 话题调研、数据收集、视觉策略判断 | topic, source, research_depth | `research.md` |
| **Scriptwriter** | 结构化分镜脚本编写 | research.md, duration, style | `script.md` |
| **Visual Director** | 图片 prompt 生成（可选） | script.md, 场景 visual_assets | `image_prompt_N.txt` |
| **Reviewer** | 质量评审（L2 LLM 评审） | milestone artifact + goal.yaml | 评分报告 |
| **Evaluator** | GAN 模式合约审查 + 迭代改进 | contract JSON + milestone artifact | 评分 + feedback |

### Pipeline CLI（替代旧 Agent）

原 Sound Engineer Agent 已移除，音频处理由 Producer 通过 Pipeline CLI 直接完成：

| 命令 | 功能 |
|------|------|
| `pipeline-cli tts` | 文本转语音（支持 --scene N） |
| `pipeline-cli whisper` | 语音转字幕 SRT |
| `pipeline-cli bgm` | 背景音乐生成 |
| `pipeline-cli sfx` | 音效处理 |
| `pipeline-cli scene-cycle` | 单场景完整流水线 |
| `pipeline-cli assemble` | 最终视频组装 |
| `pipeline-cli loudnorm` | 音频归一化 -16 LUFS |
| `pipeline-cli codegen` | Scene Generator 生成 .tsx |

### Human-in-the-Loop (HITL) 中断点

- **逐场景审查**：每场景渲染后 AskUserQuestion，支持「通过/重做+反馈/跳过剩余」
- **Ratify L2 失败**：连续 2 次失败询问用户是否继续
- **图片导入暂停点**：等待用户确认或替换图片

---

## 4. Protocol — Typed Tools, HITL, Artifact Gates

### 类型化 Agent 工具

每个 Agent 有严格定义的工具签名（tool name + parameter schema），不存在模糊的通用工具：

```
vm_start_research(output_dir)       → Research 里程碑启动
vm_build_researcher_task(prompt, output_dir, run_number)  → 构建 Researcher 任务
vm_ratify_research(prompt, output_dir, run_number)        → 验收 Research
vm_build_scriptwriter_task(...)     → 构建 Scriptwriter 任务
...
```

### Artifact Gates（Ratify 二层验证）

```
Layer 1（规则检查）:
  - Research: min_chars >= 800, headings >= 3, URL refs >= 1
  - Script: file_exists, scenes >= 3, 无连续 3+ 同类型场景
  - Assets: audio.wav > 10KB, captions.srt valid, video.mp4 > 100KB

Layer 2（LLM 评审 — 二选一）:
  - Reviewer agent（Research + legacy 模式）
  - Evaluator agent（Script/Assets GAN 模式，含合约驱动 + 迭代改进）
```

### HITL 设计

- **非阻塞**：大部分流程自动完成
- **关键决策点中断**：场景审查、重试超限、图片导入
- **跳过机制**：C 选项跳过剩余审查，实现批量确认

### GAN 模式协议

`eval_mode: "gan"` 激活合约驱动的质量提升系统：

1. 从 artifact 确定性派生 contract JSON
2. Evaluator 审查合约（完整性和合理性）
3. 失败则附带 feedback 重试（max 2 轮）
4. 分数回退 > 5 则回滚
5. 合约通过后注入下游 Agent 的 feedback_section

---

## 5. Milestone: Research — 调研里程碑

### 流程

```
Producer 读取 goal.yaml
  → vm_start_research(output_dir)
  → vm_build_researcher_task(prompt, output_dir, run_number=1)
  → Subagent(researcher) 执行调研
  → 写入 artifacts/research/run-1/research.md
  → vm_ratify_research(prompt, output_dir, run_number=1)
```

### Researcher 输入契约

| 字段 | 说明 |
|------|------|
| topic | 视频话题 |
| source | 信息来源（local-file / web） |
| local_file | 本地文件路径（source=local-file 时） |
| output_path | research.md 输出路径 |
| required_sections | 必需的章节数量 |
| min_chars | 最少字符数 |
| visual_strategy | image_heavy / image_light / image_none |

### Researcher 输出要求

- `# Research: ...` 标题
- 至少 3 个 `## ` 二级标题
- 核心事实、关键数据、视觉素材线索、叙事结构建议
- 参考来源或本地文件来源说明

### Ratify 标准

- **L1**：字数 > 800, 标题数 >= 3, URL 引用 >= 1
- **L2**：Reviewer 评审 4 维度（completeness, accuracy, freshness, visual_cues）

### 跨里程碑传递

Scriptwriter 通过文件路径自行读取完整 research.md（不裁剪 summary），保持信息完整性。

---

## 6. Milestone: Script — 脚本里程碑

### 流程

```
Producer 读取 research.md + goal.yaml
  → 生成 script-contract.json（GAN 模式）
  → Evaluator 审查合约（max 2 轮）
  → 合约注入 Scriptwriter prompt
  → 派发 Scriptwriter
  → 写入 artifacts/script/run-1/script.md
  → Evaluator 评审产出（加权总分 >= 75 通过）
  → 失败附带反馈重试，分数下降 > 5 则回滚
```

### 脚本结构

每个场景包含丰富元数据：

```
type: narration / data_card / quote_card / title_card / transition
narrative_role: hook / context / climax / detail / cta
narration: 旁白文稿
scene_intent: 场景意图说明
content_brief: 内容要点
visual_assets[]: 可选图片素材（Mayer 决策矩阵决定）
duration_estimate: 预估时长
data_semantic / quote: 数据或引用原文
composition_hint: 构图提示
```

### 视觉策略三层级联

1. **Researcher**：判断话题级 `visual_strategy`（image_heavy / image_light / image_none）
2. **Scriptwriter**：按 Mayer 原则决策矩阵决定每场景的 `visual_assets[]`（可选数组，非必选）
3. **Editor**：按 role 选择布局模板（Template A-E）

关键改进：视觉素材从"必选"变为"按需"，无 visual_assets 的场景使用纯 primitives 渲染。

### Ratify 标准

- **L1**：文件存在、scene 数量合规、无连续 3+ 同类型场景
- **L2（GAN）**：Evaluator 评审 5 维度（narrative_flow, pacing, visual_variety, audience_fit, content_coverage），迭代最多 2 轮
- **L2（Legacy）**：Reviewer 评审 4 维度

---

## 7. Milestone: Assets — 素材里程碑

Assets 采用**逐场景流水线**架构，Producer 直接驱动 Pipeline CLI。

### Phase 0: GAN 合约审查

`eval_mode="gan"` 时：
1. 从 script.md 确定性派生 `assets-contract.json`
2. 合约内容：每场景的 `required_files`、`composition_hint`、`estimated_audio_duration_ms`、`data_card_fields`
3. Evaluator 审查合约（max 2 轮）
4. 合约通过后注入 Visual Director 的 feedback_section

### Phase 1: 全局准备

- **SFX**: `pipeline-cli sfx` — 从 script.md 解析 sfx_cues，拷贝到输出目录
- **BGM**: `pipeline-cli bgm` — 从 script.md 解析 bgm_track，按预估总时长生成

### Phase 2: 逐场景流水线

每场景串行执行：

```
TTS (pipeline-cli tts --scene N)
  → Whisper 字幕 (pipeline-cli whisper --scene N)
  → 图片生成（如有 visual_assets）
    → Producer 生成 image_prompt_N.txt
    → 图片导入暂停点（HITL）
  → scene-cycle (pipeline-cli scene-cycle --scene N)
    → copy-assets → loudnorm → 解析 script.md
    → codegen 生成 .tsx 文件
    → video-cli import → export → render-scene
  → 逐场景审查 AskUserQuestion（A:通过 / B:重做 / C:跳过剩余）
```

### 逐场景优势

- 每场景独立完成，中间可审查调整
- TTS/Whisper 结果立即可用于 scene-cycle
- 支持 `--scene N` 过滤，按需处理单个场景

### 图片素材流程

```
script.md visual_assets[]
  → pipeline-cli parseVisualAssets() → ParsedScene.visualAssets
  → manifest.ts → ManifestSceneEntry.images[]
  → import-json.ts → ImportScene.imageFiles[]
  → copy-assets.ts → public/images/scene-NN_N.png
  → GeneratedSceneShell → VisualAssetsContext.Provider
  → useSceneContext().visualAssets → ImageFrame (6 Ken Burns effects)
```

### ImageFrame Ken Burns 效果

| Effect | 动画 | 典型用途 |
|--------|------|---------|
| zoom-in | scale 1.0→1.15 | hook 聚焦 |
| zoom-out | scale 1.15→1.0 | climax 全景揭示 |
| pan-left | translateX 0→-30px | 展示宽场景 |
| pan-right | translateX 0→+30px | 叙事推进 |
| parallax | translateY 0→-20px | 层次深度感 |
| static | 无动画 | CTA 稳定收束 |

---

## 8. Milestone: Assembly — 最终组装

### 组装流程

Assembly 已合并入 Assets 里程碑，作为 Phase 3 自动执行：

```
validate → export → audio-buffer patch → Remotion render (含转场+BGM) → thumbnail
```

使用 `assemble` CLI 命令一键完成。

### 内置验证

- video.mp4 > 100KB（L1 规则检查）
- L2 Reviewer 评估（可选，非必须）
- 场景间自动添加转场效果
- BGM 全局覆盖 + auto-ducking（根据场景时间线二进制搜索自动降音量）

### 输出产物

| 文件 | 说明 |
|------|------|
| `final/video.mp4` | 完整视频 |
| `final/thumbnail.jpg` | 缩略图 |
| `manifest.json` | 场景素材清单（含每场景 images[] 引用） |

---

## 9. Design Philosophy — 设计哲学

### 为什么选择 DeepAgents-native 而非 LangGraph

| 维度 | DeepAgents-native | LangGraph |
|------|-------------------|-----------|
| 架构 | 平面式 Producer-Crew | 图式节点边 |
| Agent 定义 | 纯 Markdown prompt + 类型化工具 | Python node + edge |
| 状态 | YAML 文件系统持久化 | Python 内存对象 |
| HITL | 文件系统级中断点 | 需自定义中断逻辑 |
| 调试 | 文件目录可直接审查每步产出 | 需 LangSmith 等工具 |
| 依赖 | 仅 Claude Code + 基础 CLI | LangChain 全家桶 |

**核心理由**：
1. **可审查性**：每步产出的 research.md / script.md 是纯文本文件，可人工审查、版本控制、局部重试
2. **鲁棒性**：文件系统状态支持中断恢复，非内存状态不丢失
3. **Agent 独立性**：Agent 由独立 Markdown prompt 定义，改 prompt 无需改代码
4. **简单性**：不引入图引擎的复杂概念（条件边、状态归约、并行分支调度）

### 硬规则

1. **类型化工具**：所有 Agent 工具必须有明确的输入输出 schema，不存在"万能执行"工具
2. **Subagent 自行读文件**：Producer 不内联 artifact 内容，只传路径
3. **跨里程碑不裁剪 summary**：下游 Agent 通过文件路径读取完整 artifact
4. **逐场景渲染**：串行而非批处理，支持中间审查和定向重做
5. **三层级联视觉策略**：从话题级到场景级到元素级，逐层降维决策

### 质量保证体系

```
L1 规则检查（确定性）→ 快速失败
L2 LLM 评审（概率性）→ 深度质量评估
↑ 两者结合形成 GAN 风格的质量提升循环
```

### 视觉素材策略演进

从早期版本"每场景必配图"升级为"Mayer 原则驱动按需选图"：
- 减少不必要的图片生成（节省 API 成本和用户等待时间）
- 避免"为了配图而配图"的语义噪声
- 纯 primitives 场景渲染依然保持视觉一致性（StyleKit ThemeProvider）

### 系统可扩展性

- 新增里程碑：只需添加 yaml entry + prompt 文件（声明式 pipeline）
- 替换 Agent：修改 agents/*.md 即可，无需改动 Producer 逻辑
- 新增场景类型：在 Remotion 模板引擎中添加新组件 + 注册到 Scene Generator
- 跨会话学习：Reflexion 系统持久化 Editor 经验教训，跨 session 自动加载

---

## 参考来源

- **Local Source**: `/docs/ARCHITECTURE-VIDEO-MAKER.md` — Video-Maker Skill 完整架构文档
- **Local Source**: `/docs/video-maker-architecture.excalidraw` — 架构可视化 Excalidraw 图
- **Design Reference**: Mayer's Multimedia Learning Principles（视觉素材决策矩阵理论基础）
- **Implementation**: pipeline-cli codegen + Remotion template engine + video-cli render pipeline
