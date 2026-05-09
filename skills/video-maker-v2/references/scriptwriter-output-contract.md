# Scriptwriter Output Contract

This reference holds the detailed script format for `agents/scriptwriter.md`. Keep the agent prompt short; put schema and examples here.

## Source policy

- Read `source-manifest.md` first.
- Use manifest notes and listed paths/URLs as source context.
- For local files >20KB, inspect selectively.
- For CSV/JSON, inspect headers/schema and representative rows first.
- For binary/image/audio/video, record intended use only unless analysis is explicitly needed.
- Mark unsupported or missing claims as unavailable; do not invent.

## Style spine

`script.md` must start with:

````md
```style_spine
lut_style: tech_cool
aspect_ratio: 16:9
style_template: tech-noir
visual_strategy: image_light
pacing: moderate
tone: technical, confident
glossary: [AI Agent, LLM, Remotion, TTS, Whisper]
```
````

`glossary` is required. Include 8-12 maximum proper nouns, brands, acronyms, or technical terms that ASR may misrecognize.

## Scene types

| type | use | audio | duration |
| --- | --- | --- | --- |
| `narration` | main story beat with visual primitives or optional image prompt | yes | 5-15s |
| `data_card` | source-grounded metric or comparison | yes | 3-8s |
| `quote_card` | source-grounded quote | yes | 3-6s |
| `title_card` | chapter divider | no | 2-4s |
| `transition` | visual pacing break | no | 1-2s |
| `diagram_walkthrough` | staged process/architecture explanation | yes | 8-20s |

For `1-3min`, target 10-16 scenes and 2-3 chapters.

## Required fields

### narration

```md
## Scene N: <title>
type: narration
narrative_role: hook | setup | development | climax | cta
narration: |
  <2-3 sentences>
visual_assets:
  - { role: "background", type: "image", effect: "zoom-in", prompt: "<English image prompt>" }
scene_intent:
  story_beat: hook | setup | reveal | contrast | climax | cta
  data_story: comparison | trend | part_to_whole | ranking | single_impact | none
  emotional_target: surprise | trust | urgency | reflection | inspiration
  pacing: slow | moderate | punchy | dramatic
content_brief: |
  <visual implementation direction, no hardcoded color unless source/user requires it>
duration_estimate: 8
```

`visual_assets` is optional. Use it only for hook, climax, emotional/reflection scenes, or source-specified imagery when `visual_strategy=image_light`.

### data_card

```md
## Scene N: <title>
type: data_card
narrative_role: development | climax
narration: |
  <data explanation>
scene_intent:
  story_beat: reveal | contrast | climax
  data_story: comparison | trend | part_to_whole | ranking | single_impact
  emotional_target: surprise | trust | urgency
  pacing: moderate | punchy | dramatic
content_brief: |
  <chart/counter/card direction>
data_semantic:
  claim: "<source-grounded conclusion>"
  anchor_number: <source-grounded number>
  comparison_axis: "<axis>"
  items:
    - { label: "<label>", value: <number>, unit: "<unit>" }
duration_estimate: 5
```

Use `data_card` only when source material provides concrete values.

### quote_card

```md
## Scene N: <title>
type: quote_card
narrative_role: climax | cta
narration: |
  <quote setup or reading>
quote: "<source quote>"
attribution: "<source/person>"
scene_intent:
  story_beat: climax | cta | reveal
  data_story: none
  emotional_target: inspiration | reflection | trust
  pacing: slow | dramatic
content_brief: |
  <quote visual treatment>
duration_estimate: 4
```

Use `quote_card` only when the source provides a quote.

### title_card

```md
## Scene N: <chapter title>
type: title_card
title: "<chapter title>"
chapter_title: "<short label, <=6 Chinese chars if Chinese>"
duration_estimate: 3
```

Every chapter starts with `title_card`. Hook and CTA do not need title cards.

### diagram_walkthrough

```md
## Scene N: <diagram step title>
type: diagram_walkthrough
excalidraw_file: artifacts/diagrams/<name>.excalidraw
visible_groups: [0, 1]
highlight_group: 1
diagram_variant: step-reveal
narrative_role: development
narration: |
  <explain the step's meaning, not the shapes>
transition_to_next: fade
duration_estimate: 12
```

## Forbidden fields

For content scenes, do not output:

- `layer_hint`
- `beats`
- v1 template layout hints
- invented `data_semantic`

`narration` must not contain `data_semantic`.

## Audio Design

End the script with:

```md
## Audio Design

bgm_track: upbeat-tech
bgm_reasoning: "<why this matches topic/style>"

sfx_cues:
  - scene: 1
    event: intro_stinger
    sfx: intro-stinger
    anchor: before_audio
    offsetMs: 300
```

BGM defaults:

- professional + AI/tech: `upbeat-tech`
- professional + other: `calm-corporate`
- storytelling: `storytelling-piano`
- casual/news/fast: `energetic-pop`
- casual/other: `upbeat-tech`
- documentary/dramatic: `dramatic-cinematic`
- fallback: `upbeat-tech`

SFX defaults when enabled:

- scene 1 hook: `intro-stinger`
- title_card: `title-whoosh`
- data_card with counter: `counter-pop`
- data_card with comparison/chart: `bar-impact`
- quote_card: `quote-chime`
- transition: `transition-swoosh`
- final cta: `outro-jingle`

## Layer 1 checks

- `script.md` exists.
- Scene count is inside contract range.
- Required narrative roles exist.
- No more than 3 consecutive scenes of the same type.
- `narration`, `data_card`, `quote_card` have required fields.
- `data_card` has source-grounded `data_semantic`.
- `narration` has no `data_semantic`.
- No `layer_hint` or `beats`.
- `## Audio Design` exists.
