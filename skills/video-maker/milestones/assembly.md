---
required_vars: [output_dir, transition_style]
---

# Assembly 里程碑（CLI 驱动一次性组装）

逐场景 codegen 全部通过后，调 pipeline-cli 的 `build-assembly` 命令一次性完成：
manifest → import-json → composition → copy-assets → render → thumbnail → ratify。

```bash
PIPELINE_CLI="skills/video-maker/video-pipeline-cli"
REMOTION_TEMPLATE="skills/video-maker/remotion-template"

cd $PIPELINE_CLI && pnpm exec tsx src/index.ts build-assembly \
  --session "{output_dir}" \
  --template "$REMOTION_TEMPLATE"
```

- stdout 是 JSONL 进度事件 `{event:"progress",stage,status}`，stage 覆盖 manifest / import_json / composition / copy_assets / render / ratify
- 已存在的 manifest.json / video-config.json / video.mp4 会被跳过；`--force` 强制全部重跑
- render 失败 → exit non-zero + stderr；composition 失败为非致命（不阻断 render）
- ratify 在 CLI 内置（video.mp4 存在 && > 100KB）

产出：`{output_dir}/final/video.mp4` + `{output_dir}/final/thumbnail.jpg`。
