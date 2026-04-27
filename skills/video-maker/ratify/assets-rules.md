# Assets Ratify Rules (Layer 1)

在 Producer 本地对 `{output_dir}` 的 scene-NN 目录做文件检查。`build-assets` CLI 已在 `--with-qa` 路径上内置 Layer 2 Evaluator；这里是 Layer 1 的 fallback 清单。

## 合约对照模式（首选）

读取 `artifacts/assets/assets-contract.json`，逐项对照：

1. 对每条 `contract.scenes`（skipped scene 不在合约中）遍历 `required_files`，每个文件必须存在
2. `audio.wav` size > `constraints.min_audio_size_kb` KB
3. `audio.srt`（captions）存在且为合法 SRT 格式
4. 有 `image_prompt.txt` 的 scene（narration / quote_card）：文件存在且非空

## 缩略图 prompt（可选）

5. `thumbnail/thumbnail_prompt.txt`、`thumbnail/thumbnail_alt_prompt.txt` 存在（非致命）

## 通过条件

所有 critical 检查通过 → pass。任一失败 → 修复后 `build-assets --force` 重跑对应 scene。

## skipped scene

豁免所有文件检查。
