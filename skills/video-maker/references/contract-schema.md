# Contract Schema Reference

Contracts define "what done looks like" before work begins. They are generated at milestone start, reviewed by the Evaluator, and used as the verification baseline after work completes.

## Script Contract (`script-contract.json`)

```json
{
  "version": 1,
  "milestone": "script",
  "target_scene_count": { "min": 4, "max": 8 },
  "target_duration_frames": { "min": 600, "max": 1800 },
  "narrative_structure": {
    "opening_type": "hook|question|statistic|story",
    "closing_type": "cta|summary|callback|open_question"
  },
  "audience": "general|technical|beginner|expert",
  "key_topics": ["topic1", "topic2", "topic3"],
  "constraints": {
    "max_consecutive_same_type": 3,
    "min_visual_break_scenes": 1
  }
}
```

### Field Definitions

| Field | Type | Description |
|-------|------|-------------|
| `target_scene_count` | `{min, max}` | Acceptable scene count range. Producer derives from research depth. |
| `target_duration_frames` | `{min, max}` | Total video length at 30fps. 600=20s, 1800=60s. |
| `narrative_structure.opening_type` | enum | How the video opens. `hook`: bold claim. `question`: audience question. `statistic`: data point. `story`: anecdote. |
| `narrative_structure.closing_type` | enum | How the video ends. `cta`: call to action. `summary`: key takeaways. `callback`: reference opening. `open_question`: provoke thought. |
| `audience` | enum | Target audience level. Affects content depth and jargon. |
| `key_topics` | `string[]` | Must-cover information points from research.md. Evaluator checks coverage. |
| `constraints` | object | Hard rules the script must follow. |

### Validation Rules

- `version` must be `1`
- `target_scene_count.min` >= 2, `max` <= 15
- `target_duration_frames.min` >= 300 (10s), `max` <= 5400 (3min)
- `key_topics` must have >= 2 items
- `opening_type` and `closing_type` must be from enum values above

---

## Assets Contract (`assets-contract.json`) — Phase 1

```json
{
  "version": 1,
  "milestone": "assets",
  "total_scenes": 12,
  "scenes": [
    {
      "scene_id": "scene_01",
      "type": "narration",
      "required_files": ["audio.wav", "captions.srt", "image_prompt.txt"],
      "composition_hint": "ken-burns",
      "estimated_audio_duration_ms": 8500,
      "has_data_card": false
    },
    {
      "scene_id": "scene_05",
      "type": "data_card",
      "required_files": ["audio.wav", "captions.srt"],
      "composition_hint": "solid",
      "estimated_audio_duration_ms": 6000,
      "has_data_card": true,
      "data_card_fields": ["title", "stats"]
    }
  ],
  "constraints": {
    "valid_composition_hints": ["ken-burns", "parallax", "solid", "broll", "gradient-flow", "particle"],
    "min_audio_size_kb": 10,
    "caption_format": "srt"
  },
  "parallel_agents": ["visual-director", "sound-engineer"]
}
```

### Field Definitions

| Field | Type | Description |
|-------|------|-------------|
| `total_scenes` | number | Must equal `scenes.length`. |
| `scenes[].scene_id` | string | Scene identifier (e.g., "scene_01"). Matches directory name. |
| `scenes[].type` | enum | Scene type from script.md: `narration`, `data_card`, `quote_card`, `intro`, `outro`. |
| `scenes[].required_files` | `string[]` | Required output files per scene (type-dependent). |
| `scenes[].composition_hint` | enum | Visual composition style. Must match valid values. |
| `scenes[].estimated_audio_duration_ms` | number | Expected TTS audio length. Derived from narrative word count. |
| `scenes[].has_data_card` | boolean | Whether scene contains data visualization. |
| `scenes[].data_card_fields` | `string[]` | (optional) Expected data_card fields if `has_data_card=true`. |
| `constraints` | object | Hard validation rules for file checks. |
| `parallel_agents` | `string[]` | Which agents execute in parallel. |

### Derivation Rules

| Field | Rule |
|-------|------|
| `total_scenes` | Count of `## Scene` in script.md (excluding skipped) |
| `type` | From scene's `type:` field in script.md |
| `required_files` | narration/quote_card → `["audio.wav", "captions.srt", "image_prompt.txt"]`; data_card → `["audio.wav", "captions.srt"]`; intro/outro → `["audio.wav", "captions.srt"]` |
| `composition_hint` | From scene's `composition_hint:` field, or default by type (narration→ken-burns, data_card→solid, quote_card→solid) |
| `estimated_audio_duration_ms` | Narrative word count × 150ms (中文) or × 80ms (英文) |

### Valid `composition_hint` Values

`ken-burns`, `parallax`, `solid`, `broll`, `gradient-flow`, `particle`

### Validation Rules

- `version` must be `1`
- `total_scenes` must equal `scenes.length`
- All `composition_hint` values must be in valid list
- `estimated_audio_duration_ms` must be in range 2000-30000
- `required_files` must match type-based rules above

---

## Assembly Contract (`assembly-contract.json`) — Phase 2

```json
{
  "version": 1,
  "milestone": "assembly",
  "scenes": [
    {
      "scene": 1,
      "type": "narration",
      "estimated_duration_frames": 150,
      "primary_layers": ["background:ken-burns", "subtitles:word-highlight"],
      "transition": "fade"
    }
  ],
  "total_estimated_duration_frames": 900,
  "bgm": { "track": "ambient-pulse", "ducking": true },
  "transition_strategy": "diverse (>=3 types, fade <=50%)",
  "visual_strategy": ">=3 unique background variants"
}
```

### Valid `transition` Values

`fade`, `slide-left`, `slide-right`, `slide-up`, `slide-down`, `wipe`, `flip`, `clock-wipe`

---

## Contract Review Output (`contract-review.json`)

Output by Evaluator after reviewing a contract.

```json
{
  "version": 1,
  "milestone": "script",
  "items": [
    {
      "field": "target_scene_count",
      "status": "approved",
      "reason": "6 scenes matches research depth"
    },
    {
      "field": "key_topics",
      "status": "rejected",
      "reason": "Missing 'performance benchmarks' which research.md covers extensively",
      "suggestion": "Add 'performance benchmarks' to key_topics"
    }
  ],
  "overall": "approved|rejected",
  "summary": "Brief one-line summary of review result"
}
```

### Review Rules

- `overall: "approved"` only if all items have `status: "approved"`
- Each rejected item must have a `suggestion` with actionable fix
- Evaluator reviews max 2 rounds; if still rejected after 2 rounds, escalate to user
