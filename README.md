# deepagents-video-maker

DeepAgents-native video-maker orchestrator. Current runnable pipeline: **research → script**. Assets/assembly milestone will be integrated via a standalone rendering toolchain in a future plan.

## Quick Start

```bash
# Python env
uv sync  # requires `uv` installed (see below)

# Node packages
pnpm install

# Run tests
pnpm test:py

# Start LangGraph dev server
pnpm agent:dev
```

### Prerequisites

- `uv` (Python package manager)
  - If `uv` is not installed, `python -m pip install uv` is sufficient for dev.
- `pnpm` (Node package manager)
  - If `pnpm` is not installed, `corepack enable` will provide it.

## Architecture

```
src/deepagents_video_maker/   # Python orchestration layer (DeepAgents Producer)
skills/video-maker/           # Business knowledge md (milestones, agents, ratify)
.deepagents/skills/           # Subagent skill wrappers (researcher, scriptwriter)
web-ui/                       # Next.js + LangGraph Dev UI
scripts/                      # CLI runner + smoke tests
tests/                        # pytest unit tests
```

## Design Docs

See `docs/design/` for architecture and plan documents.

## Artifact Gates

The pipeline enforces artifact validation (ratify) gates before advancing each milestone.

### Research artifact

| Artifact | Path | Required |
|----------|------|----------|
| Research report | `output/<session>/artifacts/research/run-<n>/research.md` | Yes |

Validation rules (`ratify_research`):
- File must exist.
- Content must be **> 800 characters**.
- Must contain **≥ 3 level-2 headings** (`## …`).
- Must contain **≥ 1 URL** — unless `source` is `local-file` / `local_file`.

### Script artifacts

Both files must be present for the script gate to pass.

| Artifact | Path | Required |
|----------|------|----------|
| Script markdown | `output/<session>/artifacts/script/run-<n>/script.md` | Yes |
| Scene manifest | `output/<session>/artifacts/script/run-<n>/manifest.json` | Yes |

Validation rules (`ratify_script`):
- Both files must exist.
- Script must contain **≥ 1 `## Scene …` block**.
- `manifest.json` must be a valid JSON object with a non-empty `"scenes"` array.
- Every scene object must include `id`, `narration`, and `duration` (positive number).
- Scene `id` values must be unique across the manifest.
- Scene count in the manifest must match the scene count in the script.
- Scenes with `type: narration`, `type: data_card`, or `type: quote_card` in the **script markdown** must include `scene_intent:` and `content_brief:` fields, and must **not** include `layer_hint:` or `beats:`.

### Output directories

All generated output lives under `output/` (git-ignored). No generated files are committed to the repository.

