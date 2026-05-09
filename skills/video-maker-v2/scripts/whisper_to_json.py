#!/usr/bin/env python3
"""Convert SRT captions into Remotion-friendly JSON segments."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

TIME_RE = re.compile(r"(\d\d):(\d\d):(\d\d),(\d\d\d)\s*-->\s*(\d\d):(\d\d):(\d\d),(\d\d\d)")


def to_seconds(h: str, m: str, s: str, ms: str) -> float:
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def parse_srt(text: str) -> list[dict]:
    blocks = re.split(r"\n\s*\n", text.strip(), flags=re.MULTILINE)
    segments: list[dict] = []
    for block in blocks:
        lines = [line.strip("\ufeff ") for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        time_idx = next((i for i, line in enumerate(lines) if "-->" in line), None)
        if time_idx is None:
            continue
        match = TIME_RE.search(lines[time_idx])
        if not match:
            continue
        start = to_seconds(*match.groups()[:4])
        end = to_seconds(*match.groups()[4:])
        caption = " ".join(lines[time_idx + 1 :]).strip()
        if not caption:
            continue
        segments.append({"start": start, "end": end, "text": caption})
    return segments


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--srt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fps", type=int, default=30)
    args = parser.parse_args()

    text = args.srt.read_text(encoding="utf-8-sig")
    segments = parse_srt(text)
    payload = {
        "version": 1,
        "source": str(args.srt),
        "fps": args.fps,
        "segments": [
            {
                **seg,
                "startFrame": round(seg["start"] * args.fps),
                "endFrame": round(seg["end"] * args.fps),
            }
            for seg in segments
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(args.output), "segments": len(segments)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
