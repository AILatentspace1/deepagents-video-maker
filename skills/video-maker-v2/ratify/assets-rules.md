# Assets Ratify Rules (Layer 1)

在 Producer 本地对 `{output_dir}` 的 scene-NN 目录做文件检查。v2 不使用 build-assets CLI 或 Layer 2 Evaluator；这里是 Producer 必须执行的 Layer 1 清单。

## 合约对照模式（首选）

读取 `artifacts/assets/assets-contract.json`，逐项对照：

1. 对每条 `contract.scenes`（skipped scene 不在合约中）遍历 `required_files`，每个文件必须存在
2. `audio.wav` size > `constraints.min_audio_size_kb` KB
3. `audio.srt`（captions）存在且为合法 SRT 格式
4. 有 `image_prompt.txt` 的 scene（narration / quote_card）：文件存在且非空

## 缩略图 prompt（可选）

5. `thumbnail/thumbnail_prompt.txt`、`thumbnail/thumbnail_alt_prompt.txt` 存在（非致命）

## 通过条件

所有 critical 检查通过 → pass。任一失败 → 修复后重跑对应的 Bash / Python helper 步骤。

## skipped scene

豁免所有文件检查。

## v2 额外检查

- 每个音频场景必须有 `scene-NN/audio.wav` 或 `audio-normalized.wav`，并已复制为 `remotion-template/public/audio/scene-NN.wav`。
- 每个音频场景必须有 `captions.srt` 或等价 SRT，并已复制为 `remotion-template/public/captions/scene-NN.srt`。
- 每个 generated content scene 必须有 `remotion-template/src/generated/SceneNN.tsx` 和 `scene-NN/SceneNN.tsx`。
- `remotion-template/src/generated/index.ts` 必须包含对应 registry 条目。
- `pnpm exec tsc --noEmit` 必须通过，除非用户明确接受失败并停止在可调试状态。
