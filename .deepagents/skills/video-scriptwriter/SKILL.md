---
name: video-scriptwriter
description: Scriptwriter subagent wrapper for DeepAgents-native video-maker. Loads source-of-truth scriptwriter prompt and script milestone rules from the legacy video-maker skill tree.
---

# Video Scriptwriter Skill Wrapper

This is a thin DeepAgents skill wrapper for the scriptwriter custom subagent.

Source of truth lives in:

- /skills/video-maker/agents/scriptwriter.md
- /skills/video-maker/milestones/script.md
- /skills/video-maker/ratify/script-rules.md

Use those files for progressive disclosure of business rules. Keep Producer context controller-only; do not load the end-to-end ideo-maker producer skill.

Operational constraints:

1. Read 
esearch_file by virtual path.
2. Write script.md and manifest.json exactly to paths from task.description.
3. Ensure script.md scene count equals manifest.scenes length.
4. Return only the output contract summary.
