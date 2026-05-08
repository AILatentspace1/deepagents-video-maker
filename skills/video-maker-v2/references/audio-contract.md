# Audio Contract

Covers TTS generation, duration measurement, manifest schema, and how Remotion Builder must consume the manifest.

---

## 1. TTS Generation

Generate one WAV per scene that has a `narration` field:

```bash
python .claude/skills/video-maker-v2/scripts/qwen3_tts_scene.py \
  --scene <N> \
  --text "<narration text>" \
  --output <output_dir>/audio/scene_<NN>.wav \
  --language <zh|en|...> \
  --backend auto
```

Output path convention: `<output_dir>/audio/scene_<zero-padded-N>.wav`

- Run all scenes **sequentially** (GPU memory).
- If a scene has no `narration`, skip it.
- On failure, retry with `--backend edge` as fallback; if that also fails, skip with a warning.

---

## 2. Measure Durations and Write Manifest

After all scenes are processed:

```bash
python .claude/skills/video-maker-v2/scripts/compute_scene_durations.py <output_dir>
```

The script scans `<output_dir>/audio/scene_*.wav`, measures actual durations via the Python `wave` module, computes `duration_frames = ceil(duration_s * fps) + 30` (30 frames = 1 s comfort buffer), and writes:

```text
<output_dir>/artifacts/audio/audio-manifest.json
```

**The manifest must contain measured, non-null `duration_hint_s` and `duration_frames` for every generated WAV.**
Do NOT leave values as `null` — Remotion Builder relies on `duration_frames` to set correct `durationInFrames` per scene.

### Manifest schema

```json
{
  "fps": 30,
  "buffer_frames": 30,
  "scenes": [
    {
      "scene": 1,
      "wav": "<output_dir>/audio/scene_01.wav",
      "duration_hint_s": 10.56,
      "duration_frames": 347
    }
  ]
}
```

`duration_frames = ceil(duration_hint_s * fps) + buffer_frames`

---

## 3. Remotion Builder: Consuming the Manifest

**This is the highest-priority hard rule — never violate it.**

Every scene with narration audio must have `durationInFrames >= duration_frames` from the manifest.
Scenes that end before their audio finishes will be silently truncated by Remotion — there is no warning.

### When audio-manifest.json is present

```typescript
// audio-manifest.json already contains pre-computed duration_frames
// { scene: 1, duration_hint_s: 10.56, duration_frames: 347 }
// Use duration_frames directly — do NOT set durationInFrames lower than this value
const sceneFrames = audioManifest.scenes[i].duration_frames;
```

### When audio-manifest.json is absent (no TTS generated)

Estimate from character count with a safety margin:

```typescript
// Chinese ~4 chars/sec, English ~12 chars/sec; multiply by 1.5 safety factor + 30f buffer
const charsPerSec = language === 'zh' ? 4 : 12;
const estimatedSec = narration.length / charsPerSec * 1.5;
const sceneFrames = Math.ceil(estimatedSec * fps) + 30;
```

### Video-embed scenes (scenes that contain an embedded video)

```
durationInFrames = introDurationFrames + videoDurationFrames
introDurationFrames = duration_frames  (from this scene's audio entry in the manifest)
videoDurationFrames = Math.ceil(originalDurationSec / playbackRate * fps)
```

### Verification before rendering

After writing `Root.tsx`, verify all scene frame counts with Python:

```python
import json, math
with open('artifacts/audio/audio-manifest.json') as f:
    manifest = json.load(f)
fps = manifest['fps']
for s in manifest['scenes']:
    required = s['duration_frames']
    print(f"scene_{s['scene']:02d}: audio={s['duration_hint_s']}s  required>={required}f")
# Compare against your Root.tsx scene constants.
# If any constant is less than required, fix it before rendering.
```
