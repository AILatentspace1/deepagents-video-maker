# video-maker-v2 Manifest and Remotion Config Schema

Producer writes `manifest.json` and `artifacts/assembly/video-config.json` directly. Do not call v1 `video-pipeline-cli manifest`, `import-json`, or `composition`.

## manifest.json

```json
{
  "version": 2,
  "topic": "AI Agent 趋势 2025",
  "created_at": "2026-05-04T10:00:00+08:00",
  "goal": {
    "duration": "1-3min",
    "style": "professional",
    "aspectRatio": "3:4",
    "lut_style": "tech_cool",
    "fps": 30,
    "width": 1080,
    "height": 1440
  },
  "style_spine": {
    "lut_style": "tech_cool",
    "template": "tech-noir",
    "visual_strategy": "image_light",
    "glossary": ["AI Agent", "LLM", "Remotion"]
  },
  "scenes": [
    {
      "scene": 1,
      "type": "narration",
      "title": "Hook",
      "narrative_role": "hook",
      "durationInFrames": 180,
      "narration": "...",
      "audioFile": "audio/scene-01.wav",
      "captionsFile": "captions/scene-01.srt",
      "visualAssets": [
        { "role": "background", "type": "image", "file": "images/scene-01.png" }
      ],
      "generatedComponent": "./generated/Scene01"
    }
  ],
  "audio_design": {
    "bgm": { "file": "bgm/bgm-trimmed.wav", "baseVolume": 0.35 },
    "sfxCues": []
  },
  "thumbnail": {
    "title": "AI Agent 趋势 2025",
    "subtitle": "What changes next"
  }
}
```

## artifacts/assembly/video-config.json

This file must satisfy `remotion-template/src/types.ts` `VideoConfigSchema`.

```json
{
  "aspectRatio": "3:4",
  "fps": 30,
  "primaryColor": "#0f172a",
  "accentColor": "#38bdf8",
  "lutStyle": "tech_cool",
  "progressBarStyle": "minimal",
  "bgm": {
    "file": "bgm/bgm-trimmed.wav",
    "baseVolume": 0.35,
    "duckingRatio": 0.35,
    "fadeInSeconds": 2,
    "fadeOutSeconds": 3
  },
  "sfxCues": [],
  "scenes": [
    {
      "scene": 1,
      "type": "narration",
      "title": "Hook",
      "durationInFrames": 180,
      "audioFile": "audio/scene-01.wav",
      "captionsFile": "captions/scene-01.srt",
      "visualAssets": [],
      "generatedComponent": "./generated/Scene01"
    },
    {
      "scene": 2,
      "type": "title_card",
      "title": "Chapter 1",
      "durationInFrames": 90,
      "chapterTitle": "Chapter 1"
    }
  ],
  "thumbnail": {
    "title": "AI Agent 趋势 2025",
    "subtitle": "A concise explainer"
  }
}
```

## Scene conversion rules

- `narration`, `data_card`, `quote_card`: include `generatedComponent: "./generated/SceneNN"` after subagent writes `SceneNN.tsx`.
- `title_card`: set `chapterTitle` and omit `generatedComponent`.
- `transition`: omit audio and generated component; use existing shell support.
- `diagram_walkthrough`: use existing diagram fields when an Excalidraw file is present; otherwise convert to `narration` before codegen.
- `durationInFrames`: prefer `ffprobe(audio) * fps + pre/post roll`; fallback from scriptwriter timing.
- `audioFile`, `captionsFile`, `visualAssets.file` are paths relative to `remotion-template/public/`; never prefix `public/`.

## Generated registry

`remotion-template/src/generated/index.ts` must map each generated scene:

```ts
import React from 'react';

const registry: Record<string, React.LazyExoticComponent<React.ComponentType>> = {
  './generated/Scene01': React.lazy(() => import('./Scene01')),
};

export function getGeneratedScene(path: string): React.LazyExoticComponent<React.ComponentType> | null {
  return registry[path] ?? null;
}
```
