# State Schema

本文件定义 goal.yaml 和 state.yaml 的完整模板。Producer 在初始化阶段（§3）读取此文件创建文件。

> **里程碑序列**定义在 `milestones/_pipeline.yaml` 中。以下模板中的 milestones 列表与 pipeline 保持一致。

## goal.yaml 模板（不可变，后续不修改）

```yaml
topic: "{topic}"
source: "{source}"
notebook_url: "{notebook_url}"
local_file: "{local_file}"
duration: "{duration}"
style: "{style}"
aspectRatio: "{aspectRatio}"
lut_style: "{lut_style}"
research_depth: "{research_depth}"
quick_mode: false
quality_threshold: "{quality_threshold}"
composition_mode: "{composition_mode}"
progress_bar_style: "{progress_bar_style}"
enable_video_qa: {enable_video_qa}
excalidraw_file: ""
transition_style: "fade"
bgm_file: ""
bgm_volume: 0.15
sfx_enabled: true
visual_strategy: "{visual_strategy}"
```

## state.yaml 初始模板

```yaml
workflow: video-maker-v2
workflow_status: in_progress
created: "{ISO_TIMESTAMP}"
started_at: "{ISO_TIMESTAMP}"
completed_at: ~
total_duration_seconds: ~

milestones:
  - id: research
    agent: researcher
    status: pending
    retry_count: 0
    max_retries: 2
    current_run: ~
    started_at: ~
    completed_at: ~
    ratify: ~

  - id: script
    agent: scriptwriter
    status: pending
    retry_count: 0
    max_retries: 2
    current_run: ~
    started_at: ~
    completed_at: ~
    ratify: ~

  - id: assets
    agents:
      visual_director:
        status: pending
        retry_count: 0
        current_run: ~
      sound_engineer:
        status: pending
        retry_count: 0
        current_run: ~
    join_status: pending
    max_retries: 2
    started_at: ~
    completed_at: ~
    ratify: ~

  - id: assembly
    agent: editor
    status: pending
    retry_count: 0
    max_retries: 2
    current_run: ~
    started_at: ~
    completed_at: ~
    ratify: ~
```
