# Remotion Generation Boundaries

This file intentionally does **not** define a scene layout schema.

`video-maker-v2` should behave like a composition skill:

- Producer owns topic setup, source manifest, script contract, script review, and final validation.
- Remotion Builder owns visual design and Remotion implementation.
- `$remotion-best-practices` is the normal generation path for Remotion code quality.
- Local scripts are deterministic helpers only; they may validate, package, copy, transcode, or probe existing artifacts.

## Boundary, not schema

Producer must pass a concise generation brief to Remotion Builder:

```text
topic: ...
duration: ...
aspectRatio: ...
style: ...
look_and_feel:
  lut_style: ...
  template: ...
  tone: ...
  pacing: ...
  visual_strategy: ...
  palette_direction: ...
  typography_direction: ...
  motion_direction: ...
  recurring_motifs: [...]
  avoid: [...]
script_file: ...
source_manifest_file: ...
output_project_dir: ...
final_video: ...
thumbnail: ...
hard_constraints:
  - no video-pipeline-cli
  - no v1 remotion-template mutation
  - write only inside output_project_dir and final
  - preserve script facts and narration
```

Producer should not require:

- `scene-layouts.json`
- `asset-manifest.json`
- fixed `layout.type` values
- absolute region coordinates
- a predeclared scene schema
- a deterministic smoke-builder fallback as the normal path

Producer should require a look-and-feel boundary. This is not a layout schema; it is the run's visual identity contract.

## Allowed creative implementation

Remotion Builder can choose its own:

- component architecture
- composition id
- props shape
- text and motion hierarchy
- SVG/Canvas/CSS primitives
- local generated assets under the per-run project
- audio strategy (BGM/SFX)

Remotion Builder **must** implement:

- subtitle / caption overlay on every scene that has narration (see `agents/remotion-builder.md` § Mandatory: Subtitles / Captions)

Remotion Builder must keep those choices inside the look-and-feel brief. It should implement a coherent theme/style layer or equivalent design system in the per-run project.

The output must be inspectable and verifiable, but not template-locked.

## Validation expectations

At minimum:

```bash
pnpm install
pnpm exec tsc --noEmit
pnpm exec remotion render src/index.ts <CompositionId> --output=out/video.mp4
ffprobe -v error -show_entries format=duration -of csv=p=0 out/video.mp4
```

Create or extract a thumbnail when practical:

```bash
pnpm exec remotion still src/index.ts <CompositionId> --output=out/thumbnail.jpg
```

If a thumbnail composition is not implemented, extracting one frame with `ffmpeg` is acceptable.
