# Manifest Schema

本文件定义 manifest.json 的完整格式。Producer 在 §7.4 生成 manifest 时读取此文件。

## manifest.json 结构

```json
{
  "topic": "{goal.yaml 的 topic 原文}",
  "style_spine": {
    "primary_color": "{从 lut_style 映射表查得}",
    "accent_color": "{从 lut_style 映射表查得}",
    "lut_style": "{goal.yaml 的 lut_style}",
    "style_keywords": ["{从 topic 提取的 1-3 个关键词}"]
  },
  "thumbnail": {
    "main": {
      "bg_image": "{absolute_path}/thumbnail/thumbnail_bg.png",
      "bg_prompt": "{absolute_path}/thumbnail/thumbnail_prompt.txt"
    },
    "alt": {
      "bg_image": "{absolute_path}/thumbnail/thumbnail_alt_bg.png",
      "bg_prompt": "{absolute_path}/thumbnail/thumbnail_alt_prompt.txt"
    }
  },
  "scenes": [
    {
      "scene": 1,
      "type": "narration",
      "title": "...",
      "audio": "{absolute_path}/audio.wav",
      "captions": "{absolute_path}/captions.json",
      "image": "{absolute_path}/image.png",
      "image_prompt": "{absolute_path}/image_prompt.txt",
      "broll": "{absolute_path}/broll.mp4 或 null",
      "broll_duration": "{ffprobe提取的秒数 或 null}",
      "broll_status": "completed 或 null",
      "status": "completed"
    }
  ],
  "audio_design": {
    "bgm": {
      "track_id": "{从 script.md Audio Design 的 bgm_track}",
      "base_volume": 0.15
    },
    "sfx_cues": [
      {
        "scene": 1,
        "event": "intro_stinger",
        "sfx": "intro-stinger",
        "at": "0%"
      }
    ]
  }
}
```

## Scene 类型 → 字段映射

| type | audio | captions | image | image_prompt |
|------|-------|----------|-------|-------------|
| narration | .wav path | .json path | .png path (或 null) | .txt path |
| data_card / quote_card | .wav path | .json path | null | null |
| title_card / transition | null | null | null | null |

- 用户跳过图片时：所有 image 字段和 `thumbnail.*.bg_image` 设为 `null`
- `bg_prompt` 始终有值（prompt 文件总会生成）

## audio_design 生成规则

- Producer 读取 script.md 末尾的 `## Audio Design` 段落
- 提取 `bgm_track:` 值 → 写入 `audio_design.bgm.track_id`
- 提取 `sfx_cues:` YAML 列表 → 逐条写入 `audio_design.sfx_cues` 数组
- `base_volume` 取 goal.yaml 的 `bgm_volume` 值（默认 0.15）
- 如果 script.md 不含 `## Audio Design`（向后兼容）→ 不写 `audio_design` 字段
- **SFX 文件守卫**：在 asset copy 阶段检查 `assets/sfx/` 下是否有 .wav 文件。如果没有，Producer 必须在写入 video-config.json 前移除 `sfxCues` 字段，避免 Remotion 引用不存在的音效文件导致渲染崩溃

## style_spine 色值映射表

| lut_style | primary_color | accent_color |
|-----------|--------------|-------------|
| tech_cool | #0f172a | #0ea5e9 |
| warm_human | #1c1917 | #f59e0b |
| docu_natural | #1a1a2e | #22c55e |
| news_neutral | #18181b | #6366f1 |
| pastel_dream | #faf5ff | #c084fc |
| cinematic_drama | #0c0a09 | #ef4444 |
| none | #1a1a2e | #e94560 |

style_keywords：从 topic 中提取 1-3 个关键词（名词/形容词）。例如 "AI Agent 趋势 2025" → `["AI", "Agent", "趋势"]`。

## Fallback 规则

- lut_style=none → 使用 none 行默认色值，ColorGrade intensity=0
- style_spine 字段缺失（兼容旧 manifest）→ 同 none 默认色值，Editor 应在日志中输出 WARN
