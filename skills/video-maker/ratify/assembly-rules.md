# Assembly Ratify Rules (Layer 1)

在 Producer 本地对 `{output_dir}` 做轻量级文件检查。`build-assembly` CLI 已内置大部分检查，这里只是失败时的 fallback 验证清单。

## 必需产物

| 文件 | 最小大小 |
|------|---------|
| `{output_dir}/manifest.json` | 存在即可 |
| `{output_dir}/artifacts/assembly/video-config.json` | 存在即可 |
| `{output_dir}/final/video.mp4` | ≥ 100 KB |
| `{output_dir}/final/thumbnail.jpg` | 存在（非致命） |

## 可选产物

- `{output_dir}/artifacts/assembly/composition.json` — 非致命，缺失时记 warning

## 失败策略

- video.mp4 缺失或 < 100 KB → 排查 Remotion 日志，`build-assembly --force` 重跑 render 阶段
- manifest / video-config 缺失 → 排查对应 CLI 命令的 stderr，修正后重跑
