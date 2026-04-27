---
required_vars: [topic, duration, style, aspectRatio, lut_style, research_file, project_root, output_dir, bgm_file, sfx_enabled, template_bgm_track, feedback_section, eval_mode]
---

# Script 里程碑

## 派发 Scriptwriter

读取 `agents/scriptwriter.md` 模板，渲染变量：
- `{topic}`, `{duration}`, `{style}`, `{aspectRatio}`, `{lut_style}` → 从 goal.yaml
- `{research_file}` → `{session_root}/artifacts/research/run-{latest}/research.md`（路径，不读内容）
- `{project_root}` → 项目根目录绝对路径（scriptwriter 自行执行 `scene catalog` CLI）
- `{output_dir}`, `{bgm_file}`, `{sfx_enabled}`, `{template_bgm_track}`, `{feedback_section}`
- `{excalidraw_file}` → 如果 goal.yaml 中有 excalidraw_file，传入路径；否则为空

**路径验证**：派发前用 `ls {research_file}` 验证文件存在。失败则报错，不派发。

## Diagram Scene 规则

当 `{excalidraw_file}` 非空时，Scriptwriter 需要：
1. 在 prompt 中告知 Scriptwriter 有 .excalidraw 图表可用
2. Scriptwriter 调用解析器获取 groups 列表（group id + label）
3. 为每个 group 规划一个 `diagram_walkthrough` scene，撰写旁白文本
4. diagram scenes 应与 narration scenes 自然穿插（先引入→diagram 讲解→总结）
5. script.md 中标注 `scene_type: diagram_walkthrough` + `excalidraw_file` + `visible_groups` + `highlight_group` + `diagram_variant`

## eval_mode 分支

### 当 eval_mode == "gan"

**Phase 1 — 合约生成**

基于 research.md 和 goal.yaml，Producer 生成 `script-contract.json`（schema 见 `references/contract-schema.md`）。

**生成规则**：

```
target_scene_count:
  1-3min → { min: 10, max: 16 }
  3-5min → { min: 18, max: 27 }
  5-10min → { min: 28, max: 43 }

target_duration_frames:
  duration_seconds = parse(duration) 的中位数秒数
  min = duration_seconds * 0.6 * 30   # 30fps
  max = duration_seconds * 1.2 * 30

narrative_structure:
  opening_type: style 含 storytelling → "story", 否则 → "hook"
  closing_type: 默认 "cta"

audience:
  goal.yaml 有 audience 字段 → 直接用
  否则: style=professional → "technical", style=casual → "general"

key_topics:
  从 research.md 的 ## 一、核心事实 中提取 narrative_role 标签
  至少 2 个，最多 7 个
  优先选 [hook], [climax], [development] 标记的话题

constraints:
  max_consecutive_same_type: 3  (固定)
  min_visual_break_scenes: 1    (固定)
```

**验证**：生成后检查 — version=1, key_topics.length >= 2, target_scene_count.min >= 2, target_duration_frames.min >= 300。任一不满足则修正后重新生成。

写入 `{output_dir}/script-contract.json`。

**Phase 2 — 合约审查**

派发 Evaluator（读取 `agents/evaluator.md`），传入：
- `{milestone}` = "script"
- `{artifact_file}` = ""（合约审查阶段无 artifact）
- `{contract_file}` = `{output_dir}/script-contract.json` 路径
- `{goal_summary}` = goal.yaml 摘要

Evaluator 输出 `contract-review.json`。若 `overall: "rejected"`：
1. 根据 rejected items 的 suggestion 修改 contract
2. 重新派发 Evaluator 审查（最多 2 轮）
3. 2 轮后仍 rejected → 用当前 contract 继续（记录 warning）

**Phase 3 — 派发 Scriptwriter**

（同下方"派发 Scriptwriter"节，增加合约上下文）

在 Scriptwriter prompt 的 `{feedback_section}` 中注入：
```
## Script Contract（必须遵守）
{contract_file_path}

你的脚本必须满足以上合约的所有约束。Evaluator 会逐项验证。
```

**Phase 4 — Ratify（GAN 模式）**

**Layer 1** — 读取 `ratify/script-rules.md`：文件存在、scene 数量、无连续 3+ 同类型、narration 检查（与 legacy 相同）

**Layer 2** — 跳过 Reviewer，改为派发 Evaluator：
- `{milestone}` = "script"
- `{artifact_file}` = `{output_dir}/script.md` 路径
- `{contract_file}` = `{output_dir}/script-contract.json` 路径
- `{goal_summary}` = goal.yaml 摘要
- `{research_context}` = `{session_root}/artifacts/research/run-{latest}/research.md` 路径（evaluator 自行读取，用于数据溯源验证）

Evaluator 输出评估 JSON。

**Phase 5 — 迭代循环（max 2 轮）**

```
round = 0
best_score = 0
best_script = null

WHILE round < 2:
  evaluator_result = Phase 4 的输出

  IF evaluator_result.pass == true:
    记录 "Script PASSED at round {round}"
    BREAK

  current_score = evaluator_result.weighted_total

  IF round > 0 AND current_score < best_score - 5:
    恢复 best_script → {output_dir}/script.md
    记录 "Score dropped {best_score} → {current_score}, rolling back"
    BREAK

  IF current_score > best_score:
    best_score = current_score
    best_script = 当前 script.md 内容备份

  构造 evaluator_feedback:
    - 提取 iteration_fixes（按 priority 排序）
    - 提取 contract_violations
    - 格式化为 Scriptwriter 可理解的修复指令

  重新派发 Scriptwriter（定向修复模式）:
    - {feedback_section} 中注入 evaluator_feedback
    - {evaluator_feedback} 变量传入修复指令

  重新执行 Layer 1 检查
  重新派发 Evaluator → 更新 evaluator_result

  round++

IF round >= 2 AND NOT pass:
  记录 "Script eval budget exhausted (best score: {best_score}), proceeding with best version"
  恢复 best_script（如果当前不是最优）
```

### 当 eval_mode != "gan"（legacy 模式）

走原有 Ratify 流程，不变。

## 派发 Scriptwriter

读取 `agents/scriptwriter.md` 模板，渲染变量：
- `{topic}`, `{duration}`, `{style}`, `{aspectRatio}`, `{lut_style}` → 从 goal.yaml
- `{research_file}` → `{session_root}/artifacts/research/run-{latest}/research.md`（路径，不读内容）
- `{project_root}` → 项目根目录绝对路径（scriptwriter 自行执行 `scene catalog` CLI）
- `{output_dir}`, `{bgm_file}`, `{sfx_enabled}`, `{template_bgm_track}`, `{feedback_section}`

## Ratify Script（legacy 模式）

**Layer 1** — 读取 `ratify/script-rules.md`：文件存在、scene 数量、无连续 3+ 同类型、narration 检查
**Layer 2**（仅 `quality_threshold > 0` 时）— 派发 Reviewer（维度：narrative_flow, pacing, visual_variety, audience_fit）
