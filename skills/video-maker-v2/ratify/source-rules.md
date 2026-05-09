# Source Intake Ratify Rules (Layer 1)

Producer validates `{output_dir}/artifacts/source/source-manifest.md`.

## Rules

1. `source-manifest.md` exists and is non-empty.
2. It starts with `# Source Manifest`.
3. It includes `source_type:` and `topic:` metadata.
4. It includes `## Items`.
5. It includes at least one `- path:` item.
6. For `source=websearch`, at least one item contains `http://` or `https://`.
7. For `source=folder` or `source=local-file`, listed local paths should exist where practical.

## Pass condition

All required checks pass → Source Intake complete.
Any failure → repair only `source-manifest.md`; do not generate `research.md` and do not dispatch a researcher.
