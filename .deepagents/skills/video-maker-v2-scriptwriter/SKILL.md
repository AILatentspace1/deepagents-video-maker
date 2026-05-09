---
name: video-maker-v2-scriptwriter
description: Scriptwriter subagent wrapper for DeepAgents-native video-maker-v2. Loads source-of-truth scriptwriter prompt and v2 script/source contracts.
---

# Video Maker v2 Scriptwriter Wrapper

Source of truth lives in:

- /skills/video-maker-v2/agents/scriptwriter.md
- /skills/video-maker-v2/references/workflow-contract.md
- /skills/video-maker-v2/references/scriptwriter-output-contract.md
- /skills/video-maker-v2/ratify/script-rules.md

Operational constraints:

1. Read source_manifest_file first by virtual path.
2. Read contract_file and satisfy its scene-count/duration constraints.
3. Write only script.md to the script_path from task.description.
4. Do not create research.md, source-context.md, or manifest.json.
5. Return only the output contract summary.
