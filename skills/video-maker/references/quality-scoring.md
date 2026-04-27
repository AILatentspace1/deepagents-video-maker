# Quality Scoring

本文件定义质量报告合成的评分公式和报告格式。Producer 在 Assembly Ratify 后读取此文件。

## 1. ContentScore 计算

从 Reviewer JSON 的 `quality_scores` 提取 4 个原始分（0-100），加权合成：

```
ContentScore = hook_strength * 0.4 + pacing * 0.25 + visual_density * 0.25 + readability * 0.1
```

## 2. TechScore / LoudnessScore（辅助数据，不影响门禁）

Assembly Layer 1 的 ffprobe 和 ffmpeg loudnorm 结果仅作为 **参考数据** 写入报告，不参与门禁判定。Remotion 固定输出分辨率 + two-pass loudnorm 后，这两项几乎永远达标。

## 3. TotalScore

```
TotalScore = ContentScore
```

## 4. Grade 映射

| TotalScore | Grade |
|-----------|-------|
| >= 90 | Excellent |
| >= 75 | Good |
| >= 60 | Fair |
| < 60 | Needs Work |

## 5. quality-report.json

写入 `{output_dir}/quality-report.json`，包含 ContentScore、Grade、各维度 suggestions（从 Reviewer dimensions 提取），最多 3 条 top_suggestions。

> 写入时机：在 threshold 判定之前写入，即使即将 fail 也先写报告。

## 6. quality_threshold 检查

从 goal.yaml 读取 `quality_threshold`（int, 0-100, 默认 0）。

- `quality_threshold == 0` → 跳过门禁，直接 pass
- `TotalScore >= quality_threshold` → pass
- `TotalScore < quality_threshold` → ratify fail，进入失败处理流程
