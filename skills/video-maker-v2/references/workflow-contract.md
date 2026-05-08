# video-maker-v2 Workflow Contract

Detailed workflow contract for `SKILL.md`. Load when executing the full pipeline or when exact artifact/schema/ratify details are needed.

## Output structure

```text
output/<timestamp>-video-<slug>/
├── goal.yaml
├── state.yaml
├── artifacts/
│   ├── source/source-manifest.md
│   └── script/run-1/
│       ├── script-contract.json
│       └── script.md
├── remotion-project/
│   ├── package.json
│   ├── src/index.ts
│   └── out/video.mp4
└── final/
    ├── video.mp4
    └── thumbnail.jpg
```

## Setup

Collect exactly 5 user parameters:

1. `topic`
2. `source`: `folder`, `websearch`, `notebooklm`, `local-file`, or `manual`
3. `duration`: `1-3min`, `3-5min`, or `5-10min`
4. `style`: `professional`, `casual`, or `storytelling`
5. `aspectRatio`: `16:9`, `9:16`, `3:4`, or `1:1`

Read `references/parameters.md` and infer:

```text
lut_style, source_manifest_policy, quality_threshold, eval_mode,
visual_strategy, composition_mode, template, bgm_file, sfx_enabled,
transition_style, width, height, target_scene_count,
target_duration_seconds, fps, progress_bar_style
```

Create `goal.yaml`:

```yaml
topic: "<topic>"
source: "<source>"
source_folder: "<optional>"
notebook_url: "<optional>"
local_file: "<optional>"
duration: "<duration>"
style: "<style>"
aspectRatio: "<aspectRatio>"
lut_style: "<inferred>"
source_manifest_policy: "manifest-only"
quality_threshold: 0
eval_mode: "none"
visual_strategy: "<inferred>"
composition_mode: "none"
template: "<inferred>"
bgm_file: "auto"
sfx_enabled: true
transition_style: "fade"
fps: 30
width: <inferred>
height: <inferred>
target_scene_count:
  min: <inferred>
  max: <inferred>
target_duration_seconds:
  min: <inferred>
  max: <inferred>
progress_bar_style: "minimal"
```

Create `state.yaml`:

```yaml
workflow: video-maker-v2
workflow_status: in_progress
created_at: "<iso timestamp>"
output_dir: "<output directory>"
milestones:
  - id: source_intake
    status: pending
    retry_count: 0
    max_retries: 2
    current_run: ~
    started_at: ~
    completed_at: ~
    blocking_reason: ~
  - id: script
    status: pending
    retry_count: 0
    max_retries: 2
    current_run: ~
    started_at: ~
    completed_at: ~
    blocking_reason: ~
  - id: build_scenes
    status: pending
    retry_count: 0
    max_retries: 2
    current_run: ~
    started_at: ~
    completed_at: ~
    blocking_reason: ~
  - id: render_package
    status: pending
    retry_count: 0
    max_retries: 2
    current_run: ~
    started_at: ~
    completed_at: ~
    blocking_reason: ~
todos:
  - content: "Source Intake milestone"
    status: "pending"
```

## Source Intake

Create exactly one canonical source artifact:

```text
{output_dir}/artifacts/source/source-manifest.md
```

Do not create `research.md` or `source-context.md` by default.

Manifest format:

```md
# Source Manifest

source_type: folder | manual | websearch | notebooklm | local-file
topic: <topic>
created_at: <iso timestamp>
root: <folder path or empty>

## Reading Policy
- Scriptwriter must read this manifest first.
- Scriptwriter chooses relevant files to read; Producer must not load the whole folder into context.
- Single file >20KB: read selectively and quote only relevant passages in reasoning/output.
- CSV/JSON: inspect header/schema and representative rows before deciding whether to read more.
- Binary/image/audio/video: record path and intended use; do not transcribe/analyze unless explicitly needed.
- If a needed claim/data/quote is not present in listed sources, mark it as unavailable; do not invent it.

## Items

### 1. <relative path or URL>
- type: markdown | text | csv | json | url | manual | binary | image | audio | video | other
- path: <absolute or repo-relative path, or URL>
- size_bytes: <number or unknown>
- readable: yes | no | partial
- note: <one-line note only; no deep summary required>
```

Source modes:

- `folder`: scan provided folder recursively for usable files.
- `manual`: write the user brief as one manifest item.
- `websearch`: browse only because user selected it; record URLs and snippets as manifest items.
- `notebooklm`: record notebook URL and user-provided exported notes/files.
- `local-file`: record the single file path as one manifest item.

Source ratify:

```bash
test -f "$output_dir/artifacts/source/source-manifest.md"
grep -q '^# Source Manifest' "$output_dir/artifacts/source/source-manifest.md"
grep -q '^## Items' "$output_dir/artifacts/source/source-manifest.md"
grep -q '^- path:' "$output_dir/artifacts/source/source-manifest.md"
# source=websearch: grep -E 'https?://' source-manifest.md
# source=folder/local-file: verify listed local paths exist where practical
```

If ratify fails, repair the manifest only. Do not dispatch a researcher.

## Script

Create `script-contract.json` before dispatching Scriptwriter:

```json
{
  "version": 2,
  "topic": "...",
  "duration": "1-3min",
  "target_scene_count": { "min": 10, "max": 16 },
  "target_duration_seconds": { "min": 60, "max": 180 },
  "narrative_structure": {
    "opening_type": "hook",
    "closing_type": "cta",
    "required_roles": ["hook", "setup", "development", "climax", "cta"]
  },
  "constraints": {
    "max_consecutive_same_type": 3,
    "min_visual_break_scenes": 1,
    "audio_scene_types": ["narration", "data_card", "quote_card", "diagram_walkthrough"]
  }
}
```

Dispatch `agents/scriptwriter.md` with:

```text
{topic}, {duration}, {style}, {aspectRatio}, {lut_style},
{source_manifest_file}={output_dir}/artifacts/source/source-manifest.md,
{project_root}=<skill root or repo root that contains references/>,
{output_dir}={output_dir}/artifacts/script/run-1,
{bgm_file}, {sfx_enabled}, {template_bgm_track},
{contract_file}={output_dir}/artifacts/script/run-1/script-contract.json,
{feedback_section}=empty or previous repair feedback
```

Script ratify:

```bash
test -f "$output_dir/artifacts/script/run-1/script.md"
grep -c '^## Scene' "$output_dir/artifacts/script/run-1/script.md"
# compare scene count to contract
# parse scene type sequence and reject 3+ consecutive same type
# check narration/data_card/quote_card required fields
# reject layer_hint/beats
# data_card must include source-grounded data_semantic/items
# narration must not include data_semantic
```

After Layer 1 passes, stop for user review:

```text
Script is ready for review: {output_dir}/artifacts/script/run-1/script.md
Options:
- Continue to Build Scenes
- Provide feedback and rewrite script
- I edited script.md manually; rerun Layer 1
- Stop
```

## Build Remotion Project

Read:

- `references/scene-layout-contract.md`
- `references/look-and-feel-boundary.md`
- `agents/remotion-builder.md`

Dispatch Remotion Builder with:

```text
{goal_file}={output_dir}/goal.yaml
{script_file}={output_dir}/artifacts/script/run-1/script.md
{source_manifest_file}={output_dir}/artifacts/source/source-manifest.md
{output_project_dir}={output_dir}/remotion-project
{final_video}={output_dir}/final/video.mp4
{thumbnail}={output_dir}/final/thumbnail.jpg
{boundaries}=topic, duration, aspectRatio, style, target duration band, no video-pipeline-cli, no v1 template mutation, write only output_project_dir/final, preserve script facts
{look_and_feel}=lut_style, template, visual_strategy, tone, pacing, typography direction, palette direction, motion direction, recurring motifs, visual anti-patterns
```

Validate:

```bash
test -d "$output_dir/remotion-project"
test -f "$output_dir/remotion-project/package.json"
test -f "$output_dir/remotion-project/src/index.ts"
cd "$output_dir/remotion-project"
pnpm install
pnpm exec tsc --noEmit
pnpm exec remotion render src/index.ts <CompositionId> --output=out/video.mp4
```

If compile or render fails, repair only inside `remotion-project/`.

## Generate Audio

Audio generation is optional in the current native runnable path. Run it only when
the user explicitly requests voiceover/audio assets. Until a native `audio`
milestone/tool layer exists, missing audio artifacts must not block the default
Source Intake → Script → user review → Build Remotion Project → Render and
Package path.

## Render and Package

```bash
mkdir -p "$output_dir/final"
cp "$output_dir/remotion-project/out/video.mp4" "$output_dir/final/video.mp4"
# Prefer Remotion still if available:
# pnpm exec remotion still src/index.ts <CompositionId> --output=out/thumbnail.jpg
# Otherwise extract a frame:
ffmpeg -y -ss 00:00:02 -i "$output_dir/final/video.mp4" -frames:v 1 "$output_dir/final/thumbnail.jpg"
ffprobe -v error -show_entries format=duration -of csv=p=0 "$output_dir/final/video.mp4"
```

Assembly ratify:

```bash
test -s "$output_dir/final/video.mp4"
ffprobe -v error -show_entries format=duration -of csv=p=0 "$output_dir/final/video.mp4"
test -f "$output_dir/final/thumbnail.jpg" || echo "thumbnail warning"
```

Native ratify must reject a final video whose probed duration is outside the
target duration band unless the user explicitly accepts the mismatch. On pass,
update `render_package` to `completed`, set `workflow_status: completed`, and
report final paths. Command-level render evidence is written to
`ratify/render-command.json`; milestone ratify summaries are written under
`ratify/`.

## Publish Readiness

After `final/video.mp4` exists, Producer may write an advisory product-readiness
review:

```text
final/publish-readiness.md
ratify/publish-readiness.json
```

This is not the same as technical render completion. `render_package` can be
completed while publish readiness remains `not_reviewed`.

Checklist dimensions:

- source faithfulness
- visual hierarchy
- pacing
- subtitle readability
- thumbnail usefulness

Allowed decisions:

- `publish_ready`
- `needs_revision`
- `not_reviewed`

## Repair workflow

Repair smallest scope first:

1. TypeScript failure: repair only `remotion-project/`.
2. Render failure: inspect Remotion error and repair only referenced project/assets.
3. Packaging failure: repair copy/ffmpeg/ffprobe/thumbnail commands only.
4. Full Remotion design failure: one targeted Remotion Builder retry with explicit error feedback; after two rounds ask user.

Never rewrite source manifest or accepted script because render failed.
