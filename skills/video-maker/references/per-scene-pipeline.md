# Per-Scene Pipeline Reference

本文件定义每个 codegen 场景（narration/data_card/quote_card）从生成到渲染的完整流程。

## 流水线步骤

```
TTS → Whisper → [image_prompt] → Scene Generator codegen → Copy to template → Compile → Lint → Export → Render
```

### Step 1: TTS
```bash
pipeline-cli tts --script {script_file} --output {output_dir} --scene {N}
```
输出: `scene-{NN}/audio.wav` + `scene-{NN}/text.txt`

### Step 2: Whisper
```bash
pipeline-cli whisper --output {output_dir} --scene {N}
```
输出: `scene-{NN}/captions.srt` + `scene-{NN}/captions.json`（自动同时生成两种格式）

**字幕格式说明**:
- `captions.srt` — 标准 SRT 格式（用于人工审查）
- `captions.json` — Remotion 格式 `[{text, startFrame, endFrame}]`（用于渲染）
- Whisper 命令自动生成两种格式。copy-assets 优先拷贝 `.json`，回退 `.srt`

### Step 3: Image Prompt（仅 narration 场景）
Producer 从 script.md 提取 visual_prompt → 拼接 composition directive → 写入 `scene-{NN}/image_prompt.txt`

### Step 4: Scene Generator Codegen
派发 Editor agent（codegen 模式）→ 生成 `scene-{NN}/Scene{NN}.tsx`

**必须使用 `padding: theme.spacing.safeArea`**（安全距离），详见 agents/editor.md。

### Step 5: Copy to Template
```bash
cp {output_dir}/scene-{NN}/Scene{NN}.tsx {remotion_template}/src/generated/
```
**所有** codegen 场景的 .tsx 必须拷贝到 `src/generated/` 目录。

### Step 6: Compile Gate
```bash
pipeline-cli compile-scene --scene {N} --output-dir {output_dir}
```

### Step 7: Lint Gate
```bash
pipeline-cli lint-scene --scene {N} --output-dir {output_dir}
```
检查: StyleKit import、无硬编码颜色/字号/字体、有 safeArea。

### Step 8: Copy Assets to public/
```bash
pipeline-cli copy-assets --manifest {manifest} --session {session_dir} --template {template_dir}
```
拷贝所有 audio/*.wav + captions/*.json 到 remotion-template/public/

### Step 9: Export video-config.json
```bash
cd {remotion_template} && video-cli export --output {video-config.json}
```
**自动行为**（由 buildVideoConfig 实现）:
- 扫描 `src/generated/Scene*.tsx` → 为匹配的 scene 注入 `generatedComponent: './generated/Scene{NN}'`
- 自动生成 `src/generated/index.ts` 静态 import registry（Remotion bundler 不支持动态 import）

### Step 10: Render
```bash
pipeline-cli render --template-dir {template_dir} --config {video-config.json} --output {output.mp4} --gl angle
```

## Remotion 音频渲染机制

每个场景的旁白音频由 **VideoMaker Shell** 统一渲染（不是由 codegen 组件内部播放）:
- `VideoMaker.tsx` 在每个 `TransitionSeries.Sequence` 内渲染 `<Audio src={staticFile(scene.audioFile)} />`
- `audioOffsetFrames` 控制音频延迟播放（pre-roll 留白）
- BGM 由 `<BgmTrack>` 组件全局渲染，自动 ducking
- SFX 由 `<SfxTrigger>` 组件按 cue 时间点触发

**codegen 组件（Scene{NN}.tsx）不需要也不应该渲染 `<Audio>`** — 音频由 Shell 层处理。

## diagram_walkthrough 回退策略

当 `.excalidraw` 文件不存在或 SVG 导出失败时:
1. **降级为 codegen narration** — 将 type 改为 narration，用 Scene Generator 生成替代视觉内容
2. 保留原有旁白文本不变
3. content_brief 描述原 diagram 要传达的信息（如"四步流水线垂直排列"）
4. **不要**留白屏或默认白色背景
