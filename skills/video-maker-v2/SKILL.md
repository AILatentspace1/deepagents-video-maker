---
name: video-maker-v2
description: "Hatch-pet aligned end-to-end video workflow: Setup → Source Intake → Script → Build Remotion Project → Render & Package, with Generate Audio optional until a native audio milestone exists. Use when the user asks for video-maker-v2, 制作视频 v2, or a simpler composition-first video workflow that delegates Remotion implementation to $remotion-best-practices without video-pipeline-cli."
---

# /video-maker-v2 — Composition-first video workflow

You are the **Producer**. Create one finished short-form video package from a topic and source material.

Default native runnable flow:

```text
Setup → Source Intake → Script → user script review → Build Remotion Project → Render & Package
```

Generate Audio (optional) may run after script approval when the user explicitly wants voiceover/audio assets. Until a native audio milestone/tool layer exists, the native runnable path is Source Intake → Script → user script review → Build Remotion Project → Render & Package.

For exact schemas, artifact paths, commands, and ratify checks, load `references/workflow-contract.md`.

## Core model

This skill is parallel to v1 and must not call v1 tooling. It follows the `hatch-pet` pattern:

- Producer owns planning, source indexing, script contract, review checkpoint, boundaries, and validation.
- Scriptwriter owns only `artifacts/script/run-1/script.md`.
- Remotion Builder owns only the per-run `remotion-project/**` and `final/**`.
- Remotion visual implementation is delegated to `agents/remotion-builder.md`, which must compose `$remotion-best-practices`.
- Deterministic tools (`python`, `pnpm`, `ffmpeg`, `ffprobe`) validate, render, package, or probe already-generated artifacts; they do not replace creative Remotion implementation.

## Required inputs

Ask only these 5 parameters unless the user already supplied enough to infer them:

1. `topic`
2. `source`: `folder`, `websearch`, `notebooklm`, `local-file`, or `manual`
3. `duration`: `1-3min`, `3-5min`, or `5-10min`
4. `style`: `professional`, `casual`, or `storytelling`
5. `aspectRatio`: `16:9`, `9:16`, `3:4`, or `1:1`

If reasonable defaults are appropriate, propose them once and continue after user confirmation.

## References to load

Load only what is needed:

- `references/parameters.md` — infer dimensions, style, duration, scene count, audio/motion defaults.
- `references/workflow-contract.md` — exact artifact schemas, source manifest, script contract, render/package commands, ratify checks.
- `agents/scriptwriter.md` — dispatch script generation.
- `references/scriptwriter-output-contract.md` — detailed `script.md` scene schema; loaded by Scriptwriter.
- `references/audio-contract.md` — TTS generation, duration measurement, manifest schema, Remotion Builder consumption rules.
- `references/scene-layout-contract.md` — Remotion generation boundary, not a layout schema.
- `references/look-and-feel-boundary.md` — visual identity boundary.
- `agents/remotion-builder.md` — Remotion implementation instructions.

## Progress UI

Keep this visible checklist updated:

```text
[ ] 1. Setting up <Topic>.
[ ] 2. Loading sources for <Topic>.
[ ] 3. Writing <Topic>'s script.
[ ] 4. Generating audio for <Topic>.
[ ] 5. Building <Topic>'s scenes.
[ ] 6. Rendering <Topic>.
```

Use `[x]` for completed, `[*]` for current, and `[!]` for blocked.

## Workflow summary

### 1. Setup

Read `references/parameters.md`, infer defaults, create:

```text
output/<timestamp>-video-<slug>/goal.yaml
output/<timestamp>-video-<slug>/state.yaml
```

### 2. Source Intake

Create exactly one canonical source artifact:

```text
artifacts/source/source-manifest.md
```

Do not create `research.md` or `source-context.md` by default. Source Intake is indexing only; extraction and normalization happen inside Scriptwriter Pass 0.

### 3. Script

Create `artifacts/script/run-1/script-contract.json`, dispatch `agents/scriptwriter.md`, ratify `script.md`, then stop for user review:

```text
Script is ready for review: <script.md>
Options:
- Continue to Build Scenes
- Provide feedback and rewrite script
- I edited script.md manually; rerun Layer 1
- Stop
```

Do not build Remotion scenes until the user approves or explicitly skips review.

### 4. Generate Audio (optional)

Read `references/audio-contract.md` and follow **Sections 1 and 2** (TTS generation + duration measurement) only when the user explicitly requests audio generation or voiceover artifacts. The current native DeepAgents tool chain does not expose an audio milestone, so do not treat missing audio artifacts as a blocker for the default runnable path.

### 5. Build Remotion Project

Read `references/scene-layout-contract.md` and `references/look-and-feel-boundary.md`, then dispatch Remotion Builder with file paths and concise boundaries:

```text
goal.yaml
script.md
source-manifest.md
audio_manifest=<output_dir>/artifacts/audio/audio-manifest.json   # present if audio was generated
output_project_dir=<output_dir>/remotion-project
final_video=<output_dir>/final/video.mp4
thumbnail=<output_dir>/final/thumbnail.jpg
boundaries=no video-pipeline-cli; no v1 template mutation; write only output_project_dir/final; preserve script facts; subtitles required on all narration scenes
look_and_feel=lut_style; template; visual_strategy; tone; pacing; palette; typography; motion; recurring motifs; anti-patterns
```

Remotion Builder may choose component architecture, props shape, SVG/CSS primitives, motion language, and visual rhythm **inside** the look-and-feel boundary.

### 6. Render and Package

Validate the per-run Remotion project:

```text
pnpm install
pnpm exec tsc --noEmit
pnpm exec remotion render src/index.ts <CompositionId> --output=out/video.mp4 --gl=angle
pnpm exec remotion still src/index.ts <CompositionId> --output=out/thumbnail.jpg --gl=angle
ffprobe final/video.mp4
```

Package final files:

```text
final/video.mp4
final/thumbnail.jpg
```

## Hard boundaries

Do not:

- call `.Codex/skills/video-maker/video-pipeline-cli`
- call v1 `pnpm exec tsx src/index.ts <command>`
- copy v1 `video-pipeline-cli` into v2
- modify v1 `remotion-template` or global skill files
- use GAN Evaluator, Layer 2 Reviewer, `agents/evaluator.md`, `agents/reviewer.md`, or `reflexion/*.json`
- require `scene-layouts.json`, `asset-manifest.json`, fixed `layout.type`, or absolute region coordinates as the normal path
- use `scripts/remotion-layout-builder.mjs` as the normal generation path
- allow generic visuals that violate the run's look-and-feel boundary
- invent facts, metrics, quotes, logos, maps, charts, or source implications not in the script/source

## Write permissions

- Producer: `goal.yaml`, `state.yaml`, `artifacts/source/source-manifest.md`, `artifacts/script/run-1/script-contract.json`, `<output_dir>/audio/*.wav`, `<output_dir>/artifacts/audio/audio-manifest.json`, state updates, final packaging.
- Scriptwriter: only `artifacts/script/run-1/script.md`.
- Remotion Builder: only `remotion-project/**` and `final/**`.

Producer passes file paths, not large artifact contents, wherever possible.

## Acceptance criteria

A run is complete only when:

- `goal.yaml`, `state.yaml`, `source-manifest.md`, and `script.md` exist.
- Source Intake, Script, Remotion project, and Assembly Layer 1 checks pass.
- The user approved the script checkpoint or explicitly skipped review.
- `remotion-project/package.json`, `remotion-project/src/index.ts`, and `remotion-project/out/video.mp4` exist.
- `pnpm exec tsc --noEmit` passes, or failures are documented and accepted by the user.
- The Remotion project contains a coherent theme/style layer or equivalent visual system matching the look-and-feel brief.
- `final/video.mp4` exists, is non-empty, and duration is inside the target band or accepted by the user.
- `final/thumbnail.jpg` exists or a thumbnail warning is reported.
- v1 `video-pipeline-cli` was not invoked and v1 `remotion-template` was not modified.
