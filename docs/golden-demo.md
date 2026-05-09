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

## Approved-script downstream smoke

After the script checkpoint is proven, use the approved script fixture to test
Build Scenes, Render Package, and Publish Readiness plumbing without invoking an
LLM or a real Remotion browser render:

```powershell
$env:UV_CACHE_DIR='E:\workspace\deepagents-video-maker\.uv-cache'
uv run python scripts/run_golden_render_smoke.py
```

Expected result:

- `output/golden-render-smoke-video-ai-agent-intro/remotion-project/package.json`
- `output/golden-render-smoke-video-ai-agent-intro/remotion-project/src/index.ts`
- `output/golden-render-smoke-video-ai-agent-intro/final/video.mp4`
- `output/golden-render-smoke-video-ai-agent-intro/final/thumbnail.jpg`
- `output/golden-render-smoke-video-ai-agent-intro/final/publish-readiness.md`
- `output/golden-render-smoke-video-ai-agent-intro/ratify/render-package.json`
- `output/golden-render-smoke-video-ai-agent-intro/ratify/publish-readiness.json`

This smoke writes deterministic simulated renderer output. It validates the
approved-script downstream state, package, ratify, and publish-readiness path;
it does **not** claim final visual quality or replace a real Remotion render.

## Playable golden smoke

Use this tier when you need proof that the golden path produces a real,
probeable MP4 instead of the simulated fixture used by `golden:render`:

```powershell
$env:UV_CACHE_DIR='E:\workspace\deepagents-video-maker\.uv-cache'
pnpm golden:playable
```

Expected result:

- `output/golden-playable-smoke-video-ai-agent-intro/remotion-project/package.json`
- `output/golden-playable-smoke-video-ai-agent-intro/remotion-project/src/index.ts`
- `output/golden-playable-smoke-video-ai-agent-intro/final/video.mp4`
- `output/golden-playable-smoke-video-ai-agent-intro/final/thumbnail.jpg`
- `output/golden-playable-smoke-video-ai-agent-intro/ratify/render-package.json`
- `output/golden-playable-smoke-video-ai-agent-intro/final/publish-readiness.md`

The default playable smoke uses local `ffmpeg` to produce deterministic video
media, then validates the final MP4 with `ffprobe` through the native
Render Package ratifier. This is a product-demo proof that the output is
playable, not a visual-quality approval.

To exercise the generated minimal Remotion project and native Remotion render
command path instead, run:

```powershell
$env:UV_CACHE_DIR='E:\workspace\deepagents-video-maker\.uv-cache'
uv run python scripts/run_golden_playable_smoke.py --renderer remotion --install
```

If Remotion/Chromium/ffmpeg dependencies are unavailable, this command should
fail with a clear environment or render diagnostic rather than silently writing
a fake MP4.

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
pnpm golden:playable
pnpm harness:validate
pnpm ui:build
```

If the user-profile `pnpm` shim fails before running repo scripts with
`EPERM lstat C:\Users\Administrator` or `C:\Users\ADMINI~1`, run the same
commands through Corepack from the repo root:

```powershell
corepack pnpm golden:playable
corepack pnpm ui:build
```

`pnpm harness:validate` also requires the external `better-harness` CLI to be
installed in the active `uv` environment. A fresh `uv sync` does not install it
yet; follow [`harness/README.md`](../harness/README.md) first or expect
`Failed to spawn: better-harness`.

If `pnpm` hits a Windows temp permission issue around `C:\Users\ADMINI~1`, rerun
with:

```powershell
$env:TEMP='C:\tmp'
$env:TMP='C:\tmp'
corepack pnpm harness:validate
```

The UI production build intentionally runs through
[`E:\workspace\deepagents-video-maker\scripts\build-ui.mjs`](E:\workspace\deepagents-video-maker\scripts\build-ui.mjs).
The wrapper invokes the local Next binary with `NEXT_TELEMETRY_DISABLED=1`,
`CI=1`, and hidden Windows child processes. On this Windows workspace that
avoids intermittent `spawn EPERM` failures after TypeScript succeeds.

## Known limitations

- This demo does not prove live `websearch`; `websearch` still requires `TAVILY_API_KEY`.
- This demo does not make Build Scenes automatic; script approval remains required.
- Publish readiness starts as a manual/advisory artifact, not a hard workflow blocker.
- Final Remotion quality still depends on local Remotion/browser/ffmpeg availability.
- `run_golden_render_smoke.py` uses a simulated renderer-output fixture, not a playable production render.
- `run_golden_playable_smoke.py` proves playable media by default; use `--renderer remotion --install` when you specifically need to test the Remotion CLI path.
