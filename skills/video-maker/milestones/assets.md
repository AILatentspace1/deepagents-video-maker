---
required_vars: [topic, duration, script_file, aspectRatio, width, height, output_dir, composition_mode, quick_mode, bgm_file, feedback_section, transition_style]
---

# Assets 里程碑（CLI 驱动 + Batch Codegen）

`{script_file}` = `{session_root}/artifacts/script/run-{latest}/script.md`。

## Step 1: 一次性素材准备（build-assets CLI，拆两段 + 人工暂停）

### Step 1a：Contract + image_prompt + SFX（跳过 TTS/Whisper）

调 pipeline-cli 的 `build-assets --skip-tts --skip-whisper`：派生 `assets-contract.json` + `scene-NN/image_prompt.txt` + SFX。**不生成 TTS 音频**。

```bash
PIPELINE_CLI="skills/video-maker/video-pipeline-cli"
cd $PIPELINE_CLI && pnpm exec tsx src/index.ts build-assets \
  --skip-tts --skip-whisper \
  --script "{session_root}/artifacts/script/run-{latest}/script.md" \
  --goal "{output_dir}/goal.yaml" \
  --output "{output_dir}"
```

失败 exit != 0 → 排查后 `--force` 重跑。

### Step 1b：人工暂停 — 等待用户放置音频 + 图片

Step 1a 结束后，**停止执行**，告知用户：

```
[PAUSED] Step 1a complete.

请在以下目录放置文件：
  音频：{output_dir}/artifacts/assets/scene-NN/audio.wav  （每个有 narration 的场景）
  图片：{output_dir}/artifacts/assets/scene-NN/scene.png   （有 image_prompt.txt 的场景）

image_prompt.txt 已写入各 scene 目录，用于生成图片。

放置完成后，请告知我继续（例如回复"音频和图片已放好"）。
```

**不要** 自动继续 Step 1c；等用户明确回复"已放好"或"继续"后再进入下一步。

### Step 1c：Whisper + Loudnorm + BGM（第二次 build-assets）

用户确认文件就位后，再次调 `build-assets`（**不加 skip 标志**）。由于 audio.wav 已存在，TTS 自动 skip 并运行 loudnorm（-16 LUFS 归一化）；Whisper 生成字幕；BGM 按真实 ffprobe 时长生成。

```bash
cd $PIPELINE_CLI && pnpm exec tsx src/index.ts build-assets \
  --script "{session_root}/artifacts/script/run-{latest}/script.md" \
  --goal "{output_dir}/goal.yaml" \
  --output "{output_dir}"
```

`--force` 强制重跑；stdout JSONL 进度事件供订阅；失败 exit != 0。

## Step 2: Excalidraw 导入（有 diagram_walkthrough 场景时）

`goal.yaml` 的 `excalidraw_file` 非空时：

```bash
REMOTION_TEMPLATE="skills/video-maker/remotion-template"
cd $REMOTION_TEMPLATE && pnpm exec tsx src/cli/index.ts diagram import "{excalidraw_file}" --auto --variant step-reveal
```

失败降级：`diagram_walkthrough` 场景走 narration codegen。

## Step 3: Batch Codegen（替代原逐场景循环）

所有 narration / data_card / quote_card 场景**一次性**生成 .tsx。title_card / transition / diagram_walkthrough 由 Shell 内置，不进 batch。

### 3.1 图片批量导入（一次性，替代原逐场景暂停）

AskUserQuestion 一次性处理所有有 `visual_assets` 的场景：
- A：从 Downloads 批量导入（`scripts/copy-images-from-downloads.py --target {output_dir} --all`）
- B：已手动放入图片
- C：跳过所有图片（相关场景降级为无图布局）

### 3.2 构造 batch 输入

遍历 script.md 非 skipped 内容场景，构造 JSON：

```json
{
  "batch_scenes": [
    {
      "id": 1,
      "type": "narration",
      "narrative_role": "hook",
      "scene_intent": "...",
      "content_brief": "...",
      "visual_assets": [...],
      "audio_file": "audio/scene-01.wav",
      "captions_file": "captions/scene-01.srt",
      "duration_frames": 180
    },
    ...
  ]
}
```

### 3.3 分批（场景数 > 15）

调 `lib/batcher.ts` 的 `chunkScenes`：

```typescript
import { chunkScenes } from "{PIPELINE_CLI}/src/lib/batcher.js";
const chunks = chunkScenes(batch_scenes);  // 默认 maxBatchSize=15
```

> 硬上限 30 场景；超过请先拆分视频

### 3.4 逐批派发 Scene Batch Generator

对每个 chunk（顺序执行，非并发——style_summary 要求有序）：

```
Agent(
  subagent_type: "general-purpose",
  prompt: 读取 agents/scene-batch-generator.md 渲染下列变量后的内容:
    - topic, aspect_ratio, theme_ts_path, remotion_template, script_file
    - batch_scenes_json: 本批 chunk.scenes 序列化
    - is_first_batch: chunk.index == 0
    - previous_style_summary: 若非第一批，取 chunks[i-1] 的 style_summary
)
```

Agent 输出 JSON（`{ style_summary, scenes: [{id, tsx}] }`）写到 tmp 文件 `{output_dir}/artifacts/codegen/run-{ts}/batch-{i}.json`。

### 3.5 解析并落盘 .tsx

```bash
cd $PIPELINE_CLI && pnpm exec tsx src/index.ts scene-batch \
  --input "{output_dir}/artifacts/codegen/run-{ts}/batch-{i}.json" \
  --output "{output_dir}" \
  --template "$REMOTION_TEMPLATE"
```

- JSON 解析失败 → `raw.txt` 落盘，Producer 看了决定重派或人工
- 成功 → scene-NN/SceneNN.tsx 和 remotion-template/src/generated/SceneNN.tsx 都写好

保存每批的 style_summary（从 batch JSON 读出）供下一批使用。

### 3.6 跨 chunk 循环

对每个 chunk i = 0..chunks.length - 1 执行 3.4 + 3.5。最终拿到完整 style_summaries 数组（用于 patch 场景时传参）+ motif 摘要（整批最常见的视觉选择，人工或 CLI 汇总）。

## Step 4: Compile / Lint（整批一次）

```bash
cd $PIPELINE_CLI && pnpm exec tsx src/index.ts compile-all-scenes --output-dir {output_dir} --json > compile-result.json
cd $PIPELINE_CLI && pnpm exec tsx src/index.ts lint-all-scenes    --output-dir {output_dir} --json > lint-result.json
```

合并两个 JSON 得 `failed_scenes = compile.failed ∪ lint.failed`（按 scene id）。

## Step 5: 失败决策

```
failed_count = failed_scenes.length

if failed_count == 0:
    → 跳到 Step 7 (render)

elif failed_count <= 5:
    → 派发 Scene Patch Generator（仅修这些）
       prompt: agents/scene-patch-generator.md 渲染变量:
         - failed_scenes_json (含 previous_tsx + compile_errors + lint_violations)
         - batch_style_summary (整批汇总)
         - passing_scenes_motif_summary (通过场景的 motif 摘要)
       输出 { patched_scenes, notes } → scene-batch --input 落盘覆盖
    → 回 Step 4 重跑 compile/lint

elif failed_count > 5:
    → 整体重写：重派 Scene Batch Generator（整批 chunks），带失败列表作为 feedback 段
    → 回 Step 4 重跑 compile/lint

上限 2 轮；超过 → AskUserQuestion 让用户人工介入
```

## Step 6: Ratify Assets

```bash
cd $PIPELINE_CLI && pnpm exec tsx src/index.ts ratify \
  --milestone assets \
  --contract "{output_dir}/artifacts/assets/assets-contract.json" \
  --output "{output_dir}"
```

可选 Layer 2：`build-assets --with-qa` 时已内联。

## Step 7: Render All Scenes

```bash
cd $PIPELINE_CLI && pnpm exec tsx src/index.ts render-all-scenes \
  --output-dir {output_dir} \
  --template-dir "$REMOTION_TEMPLATE" \
  --render-concurrency 3 \
  --gl angle
```

并发 3（4060Ti 16GB），产出 `{output_dir}/clips/scene-NN.mp4`。失败场景 → 回 Step 5 patch 流程。

## Step 8: Human Approval（整体级别，一次性）

AskUserQuestion 展示所有 clips + 拼好的 preview.mp4：

- A：全部通过 → 进入 assembly 里程碑
- B：整体反馈 → 用户输入反馈文字 → 回 Step 3 带反馈重新 batch codegen（整批）
- C：指定场景重做 → 用户列出场景编号 + 每个的反馈 → 走 patch 流程（回 Step 5）

## 失败处理

- `build-assets` 失败 → 排查后 `--force` 重跑
- Scene Batch Generator 输出 malformed JSON → `raw.txt` 落盘；排查后重派该 chunk
- 2 轮 patch / 整体重写仍不通过 → AskUserQuestion 人工介入
- render 失败 → `compile/lint` 已绿但渲染挂掉通常是 staticFile 路径或 asset 缺失，检查 `scene-NN/` 目录
