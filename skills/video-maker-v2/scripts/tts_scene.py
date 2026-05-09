#!/usr/bin/env python3
"""Generate one scene WAV using the local Voicebox API, with optional Edge TTS fallback.

This helper is intentionally small and deterministic. It does not parse script.md or make
creative decisions; Producer passes the exact scene text and output path.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

DEFAULT_HOST = os.environ.get("VOICEBOX_HOST", "http://127.0.0.1:17493")
DEFAULT_PROFILE = "8fd74fc1-1d47-41fb-a929-9d1357244ef1"


def post_json(url: str, payload: dict, timeout: int) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # local service
        return json.loads(resp.read().decode("utf-8"))


def download(url: str, timeout: int) -> bytes:
    with urllib.request.urlopen(url, timeout=timeout) as resp:  # local service
        return resp.read()


def run(cmd: list[str], timeout: int) -> None:
    subprocess.run(cmd, check=True, timeout=timeout)


def edge_tts_fallback(text_file: Path, output: Path) -> bool:
    tmp_mp3 = output.with_suffix(".edge.mp3")
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
    cmd = [
        "edge-tts",
        "--voice",
        "zh-CN-YunyangNeural",
        "--rate",
        "+5%",
        "--file",
        str(text_file),
        "--write-media",
        str(tmp_mp3),
    ]
    if proxy:
        cmd.extend(["--proxy", proxy])
    try:
        run(cmd, timeout=180)
        run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(tmp_mp3),
                "-ar",
                "24000",
                "-ac",
                "1",
                "-c:a",
                "pcm_s16le",
                str(output),
            ],
            timeout=120,
        )
        return output.exists() and output.stat().st_size > 1024
    except Exception as exc:  # noqa: BLE001
        print(f"edge-tts fallback failed: {exc}", file=sys.stderr)
        return False
    finally:
        try:
            tmp_mp3.unlink(missing_ok=True)
        except Exception:
            pass


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene", type=int, required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text")
    group.add_argument("--text-file", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--profile", default=DEFAULT_PROFILE)
    parser.add_argument("--language", default="zh")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--model-size", default="1.7B")
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--no-fallback", action="store_true")
    args = parser.parse_args()

    text = args.text if args.text is not None else args.text_file.read_text(encoding="utf-8")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    text_file = args.output.with_name("text.txt")
    text_file.write_text(text, encoding="utf-8")

    payload = {
        "text": text,
        "profile_id": args.profile,
        "language": args.language,
        "model_size": args.model_size,
    }
    started = time.time()
    try:
        meta = post_json(f"{args.host.rstrip('/')}/generate", payload, args.timeout)
        wav = download(f"{args.host.rstrip('/')}/audio/{meta['id']}", args.timeout)
        args.output.write_bytes(wav)
    except Exception as exc:  # noqa: BLE001
        print(f"voicebox failed for scene {args.scene}: {exc}", file=sys.stderr)
        if args.no_fallback or not edge_tts_fallback(text_file, args.output):
            return 1

    if not args.output.exists() or args.output.stat().st_size <= 1024:
        print(f"TTS output missing or too small: {args.output}", file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "scene": args.scene,
                "output": str(args.output),
                "bytes": args.output.stat().st_size,
                "elapsed_seconds": round(time.time() - started, 2),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
