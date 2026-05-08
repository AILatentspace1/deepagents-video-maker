---
name: video-maker-v2-remotion-builder
description: Remotion Builder subagent wrapper for DeepAgents-native video-maker-v2. Loads the Remotion builder prompt and workflow/render contracts.
---

# Video Maker v2 Remotion Builder Wrapper

Source of truth lives in:

- /skills/video-maker-v2/agents/remotion-builder.md
- /skills/video-maker-v2/references/workflow-contract.md
- /skills/video-maker-v2/references/audio-contract.md
- /skills/video-maker-v2/references/scene-layout-contract.md
- /skills/video-maker-v2/references/look-and-feel-boundary.md

Operational constraints:

1. Read `goal_file`, `script_file`, and `source_manifest_file` by virtual path.
2. Write only `output_project_dir/**` and, when explicitly packaging, `final/**`.
3. Do not call v1 `video-pipeline-cli` or mutate v1 templates.
4. Do not invent facts outside `script.md` / `source-manifest.md`.
5. Return only project path, composition id, validation results, and blockers.
