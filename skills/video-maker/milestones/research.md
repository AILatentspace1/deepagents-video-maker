---
required_vars: [topic, duration, style, source, notebook_url, local_file, depth_searches, depth_min_chars, depth_min_sources, output_dir, feedback_section, visual_strategy]
---

# Research 里程碑

## 派发 Researcher

读取 `skills/video-maker/agents/researcher.md` 模板，渲染变量：
- `{topic}`, `{duration}`, `{style}`, `{source}`, `{notebook_url}`, `{local_file}`, `{visual_strategy}` → 从 goal.yaml
- `{depth_searches}`, `{depth_min_chars}`, `{depth_min_sources}` → research_depth 派生
- `{output_dir}` → `{session_root}/artifacts/research/run-{N}`
- `{feedback_section}` → 首次为空，重试时为上次 feedback

## Ratify Research

**Layer 1** — 读取 `ratify/research-rules.md`：
1. `wc -c research.md` → > 800 chars
2. `grep -c "^## " research.md` → >= 3
3. `grep -c "https\?://" research.md` → >= 1

**Layer 2**（仅 `quality_threshold > 0` 时）— 派发 Reviewer（维度：completeness, accuracy, freshness, visual_cues）
