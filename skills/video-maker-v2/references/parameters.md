# video-maker-v2 Parameter Inference

v2 asks only 5 required user parameters. Everything below is deterministic unless the user manually edits `goal.yaml`.

## Duration

| duration | target_seconds | target_scene_count | source_manifest_policy |
| --- | ---: | --- | --- |
| `1-3min` | 120 | min 10, max 16 | `manifest-only` |
| `3-5min` | 240 | min 18, max 27 | `manifest-only` |
| `5-10min` | 420 | min 28, max 43 | `manifest-only` |

`target_duration_seconds.min/max` equals the user band in seconds.

## Aspect ratio

| aspectRatio | width | height |
| --- | ---: | ---: |
| `16:9` | 1920 | 1080 |
| `9:16` | 1080 | 1920 |
| `3:4` | 1080 | 1440 |
| `1:1` | 1080 | 1080 |

`fps` is always `30`.

## Source intake policy

`source_manifest_policy` is always `manifest-only`.

Producer does not normalize source materials into `source-context.md` and does not generate `research.md`.
Scriptwriter reads `source-manifest.md`, then chooses relevant source files/URLs to inspect in Pass 0.

## Style spine inference

`lut_style` priority:

1. AI / agent / LLM / software / cloud / developer → `tech_cool`
2. finance / policy / news / market → `news_neutral`
3. people / productivity / education / career → `warm_human`
4. history / geopolitics / documentary / crisis → `cinematic_drama`
5. travel / lifestyle / art / design → `pastel_dream`
6. fallback by style:
   - `professional` → `news_neutral`
   - `casual` → `docu_natural`
   - `storytelling` → `warm_human`

`template` mapping:

| lut_style | template |
| --- | --- |
| `tech_cool` | `tech-noir` |
| `warm_human` | `warm-story` |
| `docu_natural` | `minimal-mono` |
| `news_neutral` | `news-clean` |
| `pastel_dream` | `pastel-pop` |
| `cinematic_drama` | `cinema-drama` |
| `none` | `minimal-mono` |

## Visual strategy

- `image_heavy`: travel, product, design, fashion, food, location-rich stories.
- `image_light`: AI, software, business, education, explainers. Default.
- `image_none`: abstract concepts, privacy-sensitive topics, or when the user explicitly says no images.

Scriptwriter uses this to decide whether each scene needs `visual_assets`.

## Audio and motion defaults

- `quality_threshold`: `0` (no Layer 2 reviewer)
- `eval_mode`: `none`
- `composition_mode`: `none`
- `transition_style`: `fade`
- `progress_bar_style`: `minimal`
- `sfx_enabled`: `true`
- `bgm_file`: `auto`

BGM auto mapping:

| style / topic | track |
| --- | --- |
| AI / tech / professional | `upbeat-tech` |
| storytelling | `storytelling-piano` if available, else `upbeat-tech` |
| casual / upbeat | `upbeat-tech` |
| documentary / dramatic | `dramatic-cinematic` if available, else `upbeat-tech` |
| fallback | `upbeat-tech` |
