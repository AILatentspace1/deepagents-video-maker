# Look-and-feel Boundary

This file defines the visual identity boundary for `video-maker-v2`.

The boundary follows the same pattern as `hatch-pet`: the skill should delegate creative generation to a specialist, but it must still provide an authoritative visual spec and explicit anti-patterns. Remotion Builder is free to design within the spec; it is not free to ignore the spec.

## Producer responsibilities

Before dispatching Remotion Builder, Producer must derive a concise look-and-feel brief from:

- `goal.yaml`: `topic`, `style`, `aspectRatio`, `lut_style`, `template`, `visual_strategy`, `transition_style`, `progress_bar_style`.
- `script.md`: top `style_spine` block, scene roles, `content_brief`, and `visual_assets`.
- `source-manifest.md`: source identity and any source-provided visual cues.
- user feedback, if provided.

The brief should be short and concrete:

```text
look_and_feel:
  style_spine: tech_cool / news_neutral / warm_human / ...
  template: tech-noir / news-clean / warm-story / ...
  tone: professional / casual / storytelling
  pacing: slow / moderate / punchy / dramatic
  aspect_ratio: 16:9 / 9:16 / 3:4 / 1:1
  palette_direction: concise descriptive palette, no exact schema required
  typography_direction: e.g. editorial, technical dashboard, warm documentary
  motion_direction: e.g. subtle UI reveals, kinetic captions, cinematic fades
  recurring_motifs: 2-4 visual motifs that should repeat across scenes
  avoid: 4-8 anti-patterns
```

## Remotion Builder responsibilities

Remotion Builder must create a coherent visual system inside the per-run project. It may implement this as `src/theme.ts`, CSS variables, component tokens, or another equivalent layer.

It may choose:

- component architecture
- scene composition
- props shape
- SVG / Canvas / CSS primitives
- typography hierarchy
- motion details
- internal asset organization

It must preserve:

- `aspectRatio`, width, height, and fps from `goal.yaml`
- script facts, narrative roles, and scene intent
- the selected `lut_style` and `template` direction
- consistent palette, typography, spacing, and motion language across scenes
- source-grounded visuals when sources or script provide visual cues

## House-style defaults by template

Use these as guidance, not a rigid schema.

### `tech-noir`

- Best for AI, agents, software, developer tools, cloud, automation.
- Prefer dark technical surfaces, luminous UI lines, diagrammatic flows, cards, status chips, progress indicators, and clean futuristic dashboards.
- Motion should feel precise: staggered reveals, line tracing, subtle spring entrances, progress sweeps.
- Avoid generic stock-photo futurism, random robots unrelated to the script, neon overload, unreadable tiny code, and gratuitous 3D sci-fi.

### `news-clean`

- Best for finance, policy, current affairs, market explainers.
- Prefer editorial grids, lower-third style labels, chart frames, neutral data cards, and high information clarity.
- Motion should be restrained: wipes, fades, slide-ins, and chart reveals.
- Avoid meme visuals, overdramatic cinematic effects, and unsourced numerical graphics.

### `warm-story`

- Best for people, education, productivity, career, reflective topics.
- Prefer warmer backgrounds, human-centered metaphors, soft cards, story chapters, and gentle transitions.
- Motion should feel calm and guided.
- Avoid sterile enterprise dashboards unless the script specifically needs them.

### `minimal-mono`

- Best for abstract or technical topics where clarity is more important than decoration.
- Prefer monochrome layouts with one accent, simple diagrams, whitespace, and strong typography.
- Avoid excessive imagery, busy backgrounds, and decorative particles.

### `pastel-pop`

- Best for lifestyle, creative, design, travel, food, and light product explainers.
- Prefer soft shapes, playful cards, clean iconography, and friendly transitions.
- Avoid hard cyberpunk aesthetics unless requested.

### `cinema-drama`

- Best for history, geopolitics, crisis, biographies, and documentary topics.
- Prefer cinematic contrast, title cards, maps/timelines when grounded, slower reveals, and a stronger story arc.
- Avoid fake archival footage, fabricated maps, or dramatic claims not in the script.

## Global anti-patterns

Do not use:

- unrelated hero art, random stock-photo scenes, or images that imply facts not in the script
- hardcoded visual facts, charts, maps, numbers, rankings, or logos not present in the script/source
- a different aspect ratio or visual orientation than `goal.yaml`
- one-off scene styles that break the overall identity
- tiny unreadable text blocks, dense code walls, or cluttered dashboards
- placeholder-looking grey boxes, generic gradients with no visual concept, or bare text-only slides unless intentional
- v1 layout schema, `video-pipeline-cli`, or deterministic layout smoke-builder as a replacement for composition

## Practical rule

Use freedom for implementation, not for identity:

```text
Free: how to build scenes in Remotion.
Bounded: what the video should feel like, what facts it can imply, and what visual language it should repeat.
```
