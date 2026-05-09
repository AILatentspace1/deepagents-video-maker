#!/usr/bin/env python3
"""
QA-1: Verify that Root.tsx scene durationInFrames constants meet the minimums
from audio-manifest.json.

Usage:
    python check_scene_durations.py <audio_manifest_json> <Root.tsx>

Exit code:
    0  all scenes PASS
    1  one or more scenes FAIL (durationInFrames < required duration_frames)

Output example:
    [PASS] scene_01  required=347f  actual=347f
    [FAIL] scene_02  required=690f  actual=300f  <-- too short by 390f
    ...
    [RESULT] 1/2 scenes FAILED
"""

import json
import re
import sys


def load_manifest(path: str) -> dict[int, int]:
    """Returns {scene_number: required_duration_frames}."""
    with open(path, encoding="utf-8") as f:
        manifest = json.load(f)
    return {s["scene"]: s["duration_frames"] for s in manifest["scenes"]}


def extract_root_durations(tsx_path: str) -> dict[int, int]:
    """
    Extract scene durationInFrames values from Root.tsx.

    Matches patterns like:
      durationInFrames={347}
      durationInFrames: 347
      const S01 = 347
      durationInFrames={S01}  (resolves named constants)

    Returns {scene_number: frames} where scene_number is inferred from
    nearby Scene identifiers (Scene01, S01, scene_01, etc.).
    """
    with open(tsx_path, encoding="utf-8") as f:
        source = f.read()

    results: dict[int, int] = {}

    # 1. Collect named constants: const S01 = 347 / const SCENE_01 = 347
    named: dict[str, int] = {}
    for m in re.finditer(
        r"\bconst\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(\d+)\b", source
    ):
        named[m.group(1)] = int(m.group(2))

    # 2. Find <Sequence ... durationInFrames={...}> blocks; associate with nearby Scene id
    # Strategy: scan for <Series.Sequence or <Sequence blocks that contain durationInFrames
    # and are adjacent to a Scene component reference (Scene01, Scene02, …)
    block_pattern = re.compile(
        r"<(?:Series\.Sequence|Sequence)\b([^>]*?)>", re.DOTALL
    )
    for block_match in block_pattern.finditer(source):
        attrs = block_match.group(1)

        # Extract durationInFrames value
        dur_match = re.search(r"durationInFrames[=:]\{?(\w+)\}?", attrs)
        if not dur_match:
            continue
        raw = dur_match.group(1)
        if raw.isdigit():
            frames = int(raw)
        elif raw in named:
            frames = named[raw]
        else:
            continue

        # Look ahead up to 300 chars for a Scene component reference
        pos = block_match.end()
        window = source[pos: pos + 300]
        scene_num_match = re.search(
            r"<Scene(\d+)|Scene(\d+)|scene_(\d+)", window, re.IGNORECASE
        )
        if scene_num_match:
            n = int(next(g for g in scene_num_match.groups() if g is not None))
            results[n] = frames

    # 3. Fallback: parse ordered list of durationInFrames values and assign scene 1..N
    if not results:
        all_vals = []
        for m in re.finditer(r"durationInFrames[=:]\{?(\w+)\}?", source):
            raw = m.group(1)
            if raw.isdigit():
                all_vals.append(int(raw))
            elif raw in named:
                all_vals.append(named[raw])
        for i, v in enumerate(all_vals, start=1):
            results[i] = v

    return results


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <audio-manifest.json> <Root.tsx>")
        sys.exit(2)

    manifest_path, tsx_path = sys.argv[1], sys.argv[2]
    required = load_manifest(manifest_path)
    actual = extract_root_durations(tsx_path)

    failures = 0
    for scene_num in sorted(required):
        req = required[scene_num]
        act = actual.get(scene_num)
        if act is None:
            print(f"[WARN] scene_{scene_num:02d}  required={req}f  actual=NOT FOUND (skipped)")
            continue
        if act >= req:
            print(f"[PASS] scene_{scene_num:02d}  required={req}f  actual={act}f")
        else:
            short = req - act
            print(f"[FAIL] scene_{scene_num:02d}  required={req}f  actual={act}f  <-- too short by {short}f")
            failures += 1

    total = len(required)
    passed = total - failures
    print(f"\n[RESULT] {passed}/{total} scenes PASSED")
    if failures:
        print("[ACTION] Fix the FAIL scenes in Root.tsx, then re-run this check before rendering.")
        sys.exit(1)


if __name__ == "__main__":
    main()
