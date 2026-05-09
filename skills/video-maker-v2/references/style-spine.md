# Style Spine

Use this table when Producer writes `goal.yaml`, `manifest.json`, or `video-config.json`.

| lut_style | primaryColor | accentColor | surface | semantic use |
| --- | --- | --- | --- | --- |
| `tech_cool` | `#0f172a` | `#38bdf8` | `#020617` | AI, software, developer tooling, automation |
| `warm_human` | `#7c2d12` | `#f97316` | `#fff7ed` | people, teams, productivity, education |
| `docu_natural` | `#1f2937` | `#84cc16` | `#f7fee7` | everyday explainers, calm factual stories |
| `news_neutral` | `#111827` | `#2563eb` | `#f8fafc` | market, policy, public events, business |
| `pastel_dream` | `#4c1d95` | `#e879f9` | `#fdf4ff` | lifestyle, creative, soft visual topics |
| `cinematic_drama` | `#1c1917` | `#dc2626` | `#0c0a09` | history, crisis, documentary, high stakes |
| `none` | `#111827` | `#64748b` | `#ffffff` | minimal fallback |

Scriptwriter must include a `style_spine` code block near the top of `script.md`:

```style_spine
lut_style: tech_cool
aspect_ratio: 3:4
style_template: tech-noir
visual_strategy: image_light
pacing: moderate
tone: technical, confident
glossary: [AI Agent, LLM, Remotion, TTS, Whisper]
```

Scene generator subagents must use `theme.colors.*`, `theme.spacing.*`, `theme.radius.*`, and `theme.motion.*` from the reused Remotion template. The hex values above are for Producer-owned config only, not for hardcoding in generated scene components.
