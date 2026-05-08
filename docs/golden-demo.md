# Golden Demo — AI Agent Intro

This demo is the canonical product proof for `deepagents-video-maker`.

It is intentionally local and folder-source based so it can run without
`TAVILY_API_KEY`, web search drift, or external source availability.

## Demo input

- Topic: `AI Agent Intro`
- Source: `folder`
- Source fixture: [`E:\workspace\deepagents-video-maker\tests\fixtures\golden_demo_source`](E:\workspace\deepagents-video-maker\tests\fixtures\golden_demo_source)
- Duration: `1-3min`
- Style: `professional`
- Aspect ratio: `16:9`

## Deterministic smoke

```powershell
$env:UV_CACHE_DIR='E:\workspace\deepagents-video-maker\.uv-cache'
uv run python scripts/run_golden_demo_smoke.py
```

Expected result:

- `output/golden-demo-smoke-video-ai-agent-intro/goal.yaml`
- `output/golden-demo-smoke-video-ai-agent-intro/state.yaml`
- `output/golden-demo-smoke-video-ai-agent-intro/artifacts/source/source-manifest.md`
- `output/golden-demo-smoke-video-ai-agent-intro/artifacts/script/run-1/script-contract.json`
- `output/golden-demo-smoke-video-ai-agent-intro/artifacts/script/run-1/script.md`

This stops at the script review checkpoint. That is intentional: Build Scenes
and Render Package require explicit approval.

## Approved script fixture

The checked-in approved script lives at:

[`E:\workspace\deepagents-video-maker\tests\fixtures\golden_demo_approved_script.md`](E:\workspace\deepagents-video-maker\tests\fixtures\golden_demo_approved_script.md)

Use it as the stable downstream fixture when testing Build Scenes or Render
Package without invoking an LLM.

## Full product path

```text
Source Intake
  -> source-manifest.md
Script
  -> script-contract.json + script.md
User review checkpoint
  -> explicit approval
Build Scenes
  -> remotion-project/package.json + remotion-project/src/index.ts
Render Package
  -> final/video.mp4 + optional final/thumbnail.jpg
Publish Readiness
  -> final/publish-readiness.md + ratify/publish-readiness.json
```

## Publish-readiness checklist

After `final/video.mp4` exists, call the advisory readiness tool or helper to
write:

- `final/publish-readiness.md`
- `ratify/publish-readiness.json`

Initial status should be `not_reviewed` unless a human or reviewer has checked:

- source faithfulness,
- visual hierarchy,
- pacing,
- subtitle readability,
- thumbnail usefulness.

Technical render completion and publish readiness are separate states. A render
can be complete while publish readiness is still `not_reviewed`.

## Validation commands

```powershell
$env:UV_CACHE_DIR='E:\workspace\deepagents-video-maker\.uv-cache'
uv run python scripts/deepagents_video_maker.py --check
uv run pytest tests/deepagents_video_maker -q
pnpm harness:validate
```

If `pnpm` hits a Windows temp permission issue around `C:\Users\ADMINI~1`, rerun
with:

```powershell
$env:TEMP='C:\tmp'
$env:TMP='C:\tmp'
pnpm harness:validate
```

## Known limitations

- This demo does not prove live `websearch`; `websearch` still requires `TAVILY_API_KEY`.
- This demo does not make Build Scenes automatic; script approval remains required.
- Publish readiness starts as a manual/advisory artifact, not a hard workflow blocker.
- Final Remotion quality still depends on local Remotion/browser/ffmpeg availability.
