# deepagents-video-maker

DeepAgents-native `video-maker-v2` orchestrator. The old research-first `video-maker` skill is no longer supported. Current pipeline is **Source Intake → Script → user review checkpoint → Build Scenes → Render Package**; build/render continues only after explicit user approval.

## Quick Start

```bash
uv sync && pnpm install
uv run pytest tests/deepagents_video_maker -q
uv run python scripts/deepagents_video_maker.py --check
uv run python scripts/run_golden_demo_smoke.py
pnpm agent:dev
```

## Architecture

```text
src/deepagents_video_maker/   # Python orchestration layer (DeepAgents Producer)
skills/video-maker-v2/         # v2 business knowledge, contracts, scriptwriter/remotion instructions
.deepagents/skills/            # v2 subagent wrapper(s)
web-ui/                        # Next.js + LangGraph Dev UI
scripts/                       # CLI runner + smoke tests
tests/                         # pytest unit tests
```

## v2 Artifact Gates

See [`docs/golden-demo.md`](docs/golden-demo.md) for the canonical local demo
path and product-readiness checklist.

### Source Intake

| Artifact | Path | Required |
|----------|------|----------|
| Source manifest | `output/<session>/artifacts/source/source-manifest.md` | Yes |

Validation rules:
- File must exist.
- Must contain `# Source Manifest`.
- Must contain `## Items`.
- Must contain at least one `- path:` item.
- `source=websearch` requires at least one URL.

### Script checkpoint

| Artifact | Path | Required |
|----------|------|----------|
| Script contract | `output/<session>/artifacts/script/run-<n>/script-contract.json` | Yes |
| Script markdown | `output/<session>/artifacts/script/run-<n>/script.md` | Yes |

Validation rules:
- Both files must exist.
- Script must contain at least one `## Scene ...` block.
- Scene count must fit `script-contract.json.target_scene_count`.
- `narration`, `data_card`, and `quote_card` scenes must include `scene_intent:` and `content_brief:`.
- `layer_hint:` and `beats:` are forbidden in these scene blocks.

### Build / render checkpoint

| Artifact | Path | Required |
|----------|------|----------|
| Remotion package | `output/<session>/remotion-project/package.json` | Yes |
| Remotion entry | `output/<session>/remotion-project/src/index.ts` | Yes |
| Final video | `output/<session>/final/video.mp4` | Yes |
| Final thumbnail | `output/<session>/final/thumbnail.jpg` | Warning only |
| Publish readiness | `output/<session>/final/publish-readiness.md` | Advisory |

Validation rules:
- Build Scenes requires explicit script approval.
- Remotion project must contain `package.json` and `src/index.ts`.
- Render Package requires non-empty `final/video.mp4`.
- Native final ratify probes `final/video.mp4` duration with `ffprobe` and rejects videos outside the requested duration band.
- Missing thumbnail is reported as a warning, not a hard failure.
- Publish readiness is advisory and separates “render succeeded” from “ready to publish”.

Generated output lives under `output/` and is git-ignored.
