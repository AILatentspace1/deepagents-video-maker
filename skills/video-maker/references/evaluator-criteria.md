# Evaluator Criteria Reference

## Skeptical Evaluation Principles

1. **假设缺陷存在** — 不要问"有没有问题"，而是问"问题在哪里"
2. **要求证据** — "看起来还行"不是通过的理由。引用场景编号、文本、数据
3. **对照合约** — 逐项验证 contract 承诺 vs 实际交付
4. **高分需要理由** — 倾向给 80+ 时，停下来重新审视
5. **修复建议要可执行** — 指定具体场景编号 + 修改动作

## Script 评估维度

### narrative_flow（叙事逻辑，权重 0.25）

衡量场景间的逻辑连贯性和因果关系链。

| 分数段 | 等级 | 描述 |
|--------|------|------|
| 90-100 | Excellent | 每个场景自然引出下一个，因果链完整，观众无需猜测"为什么突然到这里" |
| 75-89 | Good | 大部分场景连贯，1-2 处过渡稍显突兀但不影响理解 |
| 60-74 | Fair | 整体有逻辑线，但 2+ 处明显跳跃，需要观众自行补充上下文 |
| 40-59 | Poor | 场景间关系松散，像是独立话题的罗列而非连贯叙事 |
| 0-39 | Fail | 无逻辑结构，场景随机排列 |

**常见失败模式**: 场景间缺过渡句、从技术细节突然跳到情感故事、结尾与开头无呼应

### pacing（节奏，权重 0.20）

衡量场景时长分布的均衡度。

| 分数段 | 等级 | 描述 |
|--------|------|------|
| 90-100 | Excellent | 场景时长变化系数 CV < 0.2，有适当的快慢节奏交替 |
| 75-89 | Good | CV < 0.4，无明显过长/过短场景 |
| 60-74 | Fair | 1 个场景占总时长 >40%，或有场景 <3s |
| 40-59 | Poor | 2+ 个场景严重失衡，观众会感到拖沓或匆忙 |
| 0-39 | Fail | 所有内容挤在 1-2 个超长场景，其余场景形同虚设 |

**常见失败模式**: 一个场景塞了太多内容、intro/outro 过长挤压正文、缺少呼吸空间

### visual_variety（视觉多样性，权重 0.20）

衡量场景类型的多样性。

| 分数段 | 等级 | 描述 |
|--------|------|------|
| 90-100 | Excellent | 3+ 种场景类型交替使用，无连续 2 个相同类型 |
| 75-89 | Good | 2+ 种场景类型，最多连续 2 个相同类型 |
| 60-74 | Fair | 有类型变化，但出现 3 个连续相同类型 |
| 40-59 | Poor | 大部分场景是同一类型（如全是 narration）|
| 0-39 | Fail | 所有场景都是同一类型，无任何视觉变化 |

**常见失败模式**: 全 narration 无 data_card/quote_card 打断、连续 3+ 个相同类型

### audience_fit（受众匹配，权重 0.15）

衡量内容深度与目标受众的匹配度。

| 分数段 | 等级 | 描述 |
|--------|------|------|
| 90-100 | Excellent | 术语和深度完美匹配目标受众，有适当的解释层次 |
| 75-89 | Good | 基本匹配，偶尔术语过深或过浅 |
| 60-74 | Fair | 部分内容偏离目标受众水平 |
| 40-59 | Poor | 内容深度明显不匹配（对 beginner 用了大量专业术语，或对 expert 过于浅显）|
| 0-39 | Fail | 完全错位，目标受众无法理解或会感到被低估 |

### content_coverage（内容覆盖，权重 0.20）

衡量 contract 中 key_topics 的覆盖率。

| 分数段 | 等级 | 描述 |
|--------|------|------|
| 90-100 | Excellent | 100% key_topics 覆盖，每个话题有实质内容（非一笔带过）|
| 75-89 | Good | 90%+ 覆盖，遗漏的话题是次要的 |
| 60-74 | Fair | 70-89% 覆盖，有 1 个重要话题缺失 |
| 40-59 | Poor | 50-69% 覆盖，多个重要话题缺失 |
| 0-39 | Fail | <50% 覆盖，大部分 contract 要求未满足 |

**数据溯源规则（自动触发 contract violation）**：
- data_card 中的数字、百分比、对比数据**必须**能在 research.md 中找到出处
- 编造数据（research 中不存在的具体数字）→ severity=**critical**，自动 FAIL
- "合理推测"或"大约估计"不能替代实际数据
- 如果 research 中没有精确数字，data_card 应使用 research 中有的数据，或改用 narration 场景口头描述

## Assets 合约审查维度

Assets 合约审查在 assets-contract.json 生成后执行，验证合约本身的合理性（不评估实际产出）。

### scene_count_match（场景数一致性，权重 0.30）

| 分数段 | 描述 |
|--------|------|
| 100 | `total_scenes` == script.md 中非 skipped 场景数 |
| 0 | 数量不匹配 |

### required_files_match（文件清单正确性，权重 0.30）

| 分数段 | 描述 |
|--------|------|
| 100 | 每个场景的 `required_files` 与 type 匹配（narration→3 files, data_card→2 files, etc.） |
| 50 | 部分场景文件清单错误 |
| 0 | 大量场景文件清单错误 |

### composition_hint_valid（构图值合法性，权重 0.20）

| 分数段 | 描述 |
|--------|------|
| 100 | 所有 `composition_hint` 值在合法列表中 |
| 0 | 存在非法 composition_hint 值 |

### audio_duration_reasonable（音频时长合理性，权重 0.20）

| 分数段 | 描述 |
|--------|------|
| 100 | 所有场景 `estimated_audio_duration_ms` 在 2000-30000ms 范围 |
| 50 | 部分场景超出合理范围 |
| 0 | 大量场景时长不合理 |

### Assets 产出评估维度（Layer 2）

Assets 产出评估在 VD/SE 完成后执行。Producer 预收集数据（ffprobe 获取音频实际时长）后传入 Evaluator。

| 维度 | 权重 | 描述 |
|------|------|------|
| deliverable_completeness | 0.40 | 每场景的必需文件是否齐全（对照合约 required_files）|
| audio_duration_match | 0.25 | 实际音频时长与 estimated_audio_duration_ms 偏差 < 50% |
| composition_compliance | 0.20 | composition_hint 是否合法，是否匹配合约 |
| caption_format_valid | 0.15 | captions.srt 格式正确，image_prompt.txt 含 composition_rule 注释 |

**降级策略**: 如果 ffprobe 获取音频时长失败，跳过 audio_duration_match 维度并加 warning，其余维度权重等比放大。

---

## Assembly 评估维度

> TBD — Phase 2 实现。参见 `quality-scoring.md` 的双层评分公式。

## Pass/Fail 规则

- 所有维度 >= 60: 单维度通过
- 任何维度 < 40: 自动 FAIL
- weighted_total >= 75: 总分通过
- severity=critical 的 contract violation: 自动 FAIL
- severity=major 的 contract violation 存在 2+ 个: 自动 FAIL
- iteration_fixes 非空: 自动 FAIL（有修复建议 = 有问题 = 不应通过）
- 数据编造（data_card 数字在 research 中无出处）: severity=critical

## 评分校准示例

### 好脚本示例（总分 83）

```json
{
  "dimensions": [
    { "name": "narrative_flow", "score": 85, "weight": 0.25,
      "evidence": "Scene 1(hook: 惊人数据) → Scene 2(背景解释) → Scene 3(技术原理) → Scene 4(实际案例) → Scene 5(未来展望) → Scene 6(CTA)，每步自然过渡" },
    { "name": "pacing", "score": 80, "weight": 0.20,
      "evidence": "6 场景平均 8s，CV=0.18，Scene 3 略长(12s)但内容密度高可接受" },
    { "name": "visual_variety", "score": 90, "weight": 0.20,
      "evidence": "narration→data_card→narration→quote_card→narration→data_card，无连续同类型" },
    { "name": "audience_fit", "score": 78, "weight": 0.15,
      "evidence": "目标 general 受众，大部分术语有解释，但 Scene 3 的 'transformer architecture' 未展开" },
    { "name": "content_coverage", "score": 82, "weight": 0.20,
      "evidence": "5/6 key_topics 覆盖，'deployment challenges' 仅在 Scene 5 一句带过" }
  ],
  "weighted_total": 83.2,
  "pass": true
}
```

### 差脚本示例（总分 52）

```json
{
  "dimensions": [
    { "name": "narrative_flow", "score": 45, "weight": 0.25,
      "evidence": "Scene 1 讲历史，Scene 2 突然跳到代码实现，Scene 3 回到历史人物，无逻辑线" },
    { "name": "pacing", "score": 55, "weight": 0.20,
      "evidence": "Scene 2 占总时长 52%（25s/48s），其余 4 场景平均 5.75s，严重失衡" },
    { "name": "visual_variety", "score": 40, "weight": 0.20,
      "evidence": "5 个场景中 4 个是 narration，仅 Scene 4 是 quote_card，Scene 1-3 连续 narration" },
    { "name": "audience_fit", "score": 65, "weight": 0.15,
      "evidence": "目标 beginner，但 Scene 2 大量使用 API endpoint 和 JSON schema 术语未解释" },
    { "name": "content_coverage", "score": 50, "weight": 0.20,
      "evidence": "3/6 key_topics 覆盖，缺少 'pricing comparison'、'migration guide'、'community ecosystem'" }
  ],
  "weighted_total": 50.5,
  "pass": false
}
```
