#!/usr/bin/env python3
"""
Measure actual durations of generated scene WAV files and write audio-manifest.json.

Usage:
    python compute_scene_durations.py <output_dir> [--fps 30] [--buffer 30]

Arguments:
    output_dir   Root output directory (contains audio/ and artifacts/)
    --fps        Frames per second (default: 30)
    --buffer     Extra frames to add as comfort buffer (default: 30 = 1s at 30fps)

Output:
    <output_dir>/artifacts/audio/audio-manifest.json

The manifest contains measured duration_hint_s and duration_frames for every WAV found:
    duration_frames = ceil(duration_s * fps) + buffer
"""

import argparse
import json
import math
import os
import wave


def compute_durations(audio_dir: str, fps: int = 30, buffer: int = 30) -> dict:
    scenes = []
    wav_files = sorted(
        f for f in os.listdir(audio_dir)
        if f.startswith("scene_") and f.endswith(".wav")
    )
    for filename in wav_files:
        # Extract scene number from scene_NN.wav
        stem = filename[len("scene_"):-len(".wav")]
        try:
            scene_num = int(stem)
        except ValueError:
            continue
        path = os.path.join(audio_dir, filename)
        with wave.open(path) as wf:
            duration_s = wf.getnframes() / wf.getframerate()
        duration_frames = math.ceil(duration_s * fps) + buffer
        scenes.append({
            "scene": scene_num,
            "wav": path,
            "duration_hint_s": round(duration_s, 3),
            "duration_frames": duration_frames,
        })
    return {"fps": fps, "buffer_frames": buffer, "scenes": scenes}


def main():
    parser = argparse.ArgumentParser(description="Measure scene WAV durations and write audio-manifest.json")
    parser.add_argument("output_dir", help="Root output directory (contains audio/ subdir)")
    parser.add_argument("--fps", type=int, default=30, help="Frames per second (default: 30)")
    parser.add_argument("--buffer", type=int, default=30, help="Extra buffer frames appended after audio (default: 30)")
    args = parser.parse_args()

    audio_dir = os.path.join(args.output_dir, "audio")
    if not os.path.isdir(audio_dir):
        raise SystemExit(f"[ERROR] audio dir not found: {audio_dir}")

    manifest = compute_durations(audio_dir, fps=args.fps, buffer=args.buffer)

    out_dir = os.path.join(args.output_dir, "artifacts", "audio")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "audio-manifest.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    print(f"\n[OK] audio-manifest.json written to {out_path}")


if __name__ == "__main__":
    main()
