---
name: video-researcher
description: Research subagent wrapper for DeepAgents-native video-maker. Loads source-of-truth researcher prompt and research milestone rules from the legacy video-maker skill tree.
---

# Video Researcher Skill Wrapper

This is a thin DeepAgents skill wrapper for the 
esearcher custom subagent.

Source of truth lives in:

- /skills/video-maker/agents/researcher.md
- /skills/video-maker/milestones/research.md
- /skills/video-maker/ratify/research-rules.md

Use those files for progressive disclosure of business rules. Keep Producer context controller-only; do not load the end-to-end ideo-maker producer skill.

Operational constraints:

1. Read input artifacts by virtual path.
2. Write 
esearch.md exactly to the output_path from task.description.
3. Return only the output contract summary.
