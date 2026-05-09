#!/usr/bin/env python3
"""Generate one scene WAV using Qwen3-TTS with automatic backend selection.

Backend priority:
  1. DashScope API  — ``qwen3-tts-instruct-flash-realtime`` (best quality, cloud)
                      Requires: DASHSCOPE_API_KEY env var
                      Install:  pip install dashscope
  2. Local model    — ``Qwen3-TTS-12Hz-1.7B-CustomVoice`` via qwen-tts package
                      Requires: GPU + pip install qwen-tts
  3. edge-tts       — free offline fallback (lower quality)
                      Requires: pip install edge-tts

CLI interface is drop-in compatible with tts_scene.py for video-maker-v2 skill.

Usage examples:
    # Chinese narration (auto-selects best backend)
    python qwen3_tts_scene.py --scene 1 --text "今天我们来介绍AI大模型的发展" --output audio/scene_01.wav

    # English narration with custom voice instruction
    python qwen3_tts_scene.py --scene 2 --text "The world is changing fast." \\
        --output audio/scene_02.wav --language en --voice Aiden \\
        --instruct "Professional documentary narration, calm and authoritative."

    # Force DashScope backend
    python qwen3_tts_scene.py --scene 3 --text-file scene3.txt \\
        --output audio/scene_03.wav --backend dashscope

    # Force local model
    python qwen3_tts_scene.py --scene 4 --text "本地模型测试" \\
        --output audio/scene_04.wav --backend local --local-model Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice
"""
from __future__ import annotations

import argparse
import json
import os
import struct
import subprocess
import sys
import threading
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Language helpers
# ---------------------------------------------------------------------------

# Short code → DashScope/qwen-tts full language name
_LANG_MAP: dict[str, str] = {
    "zh": "Chinese",
    "zh-cn": "Chinese",
    "chinese": "Chinese",
    "en": "English",
    "en-us": "English",
    "english": "English",
    "ja": "Japanese",
    "japanese": "Japanese",
    "ko": "Korean",
    "korean": "Korean",
    "de": "German",
    "german": "German",
    "fr": "French",
    "french": "French",
    "ru": "Russian",
    "russian": "Russian",
    "pt": "Portuguese",
    "portuguese": "Portuguese",
    "es": "Spanish",
    "spanish": "Spanish",
    "it": "Italian",
    "italian": "Italian",
    "auto": "Auto",
}

# Default voices per language for DashScope instruct model
# Chosen for professional narration quality
_DEFAULT_VOICE_BY_LANG: dict[str, str] = {
    "Chinese": "Neil",        # 阿闻 — 专业新闻主持人，字正腔圆
    "English": "Aiden",       # 精通厨艺的美语大男孩，自然流畅
    "Japanese": "Ono Anna",   # 活泼日语女声
    "Korean": "Sohee",        # 温柔韩语女声
    "German": "Lenn",         # 理性德国青年
    "French": "Emilien",      # 浪漫法国大哥哥
    "Russian": "Alek",        # 战斗民族，沉稳
    "Portuguese": "Radio Gol",# 葡萄牙/巴西活力男声
    "Spanish": "Bodega",      # 热情西班牙大叔
    "Italian": "Dolce",       # 慵懒意大利大叔
}

# Default voices per language for local qwen-tts CustomVoice model
_LOCAL_DEFAULT_VOICE_BY_LANG: dict[str, str] = {
    "Chinese": "Eric",        # 成都男声，活力略带沙哑（四川腔）
    "English": "Ryan",        # 动感英语男声
    "Japanese": "Ono_Anna",   # 活泼日语女声
    "Korean": "Sohee",        # 温柔韩语女声
}

# Default video narration instruction (instructed model)
_DEFAULT_INSTRUCT_ZH = "吐字清晰精准，字正腔圆，专业播音风格，语速适中，沉稳有力。"
_DEFAULT_INSTRUCT_EN = "Professional documentary narration. Clear diction, calm and authoritative tone, moderate pace."


def _normalize_language(lang: str) -> str:
    return _LANG_MAP.get(lang.lower(), "Chinese")


# ---------------------------------------------------------------------------
# PCM → WAV helper (no external deps)
# ---------------------------------------------------------------------------

def _pcm_to_wav(pcm_bytes: bytes, sample_rate: int, channels: int, bits: int) -> bytes:
    """Wrap raw PCM data in a RIFF/WAV container."""
    data_len = len(pcm_bytes)
    byte_rate = sample_rate * channels * bits // 8
    block_align = channels * bits // 8
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        36 + data_len,
        b"WAVE",
        b"fmt ",
        16,           # PCM chunk size
        1,            # AudioFormat = PCM
        channels,
        sample_rate,
        byte_rate,
        block_align,
        bits,
        b"data",
        data_len,
    )
    return header + pcm_bytes


# ---------------------------------------------------------------------------
# Backend 1: DashScope API (qwen3-tts-instruct-flash-realtime)
# ---------------------------------------------------------------------------

DASHSCOPE_MODEL = "qwen3-tts-instruct-flash-realtime"
DASHSCOPE_WSS_URL = "wss://dashscope.aliyuncs.com/api-ws/v1/realtime"
DASHSCOPE_SAMPLE_RATE = 24000
DASHSCOPE_CHANNELS = 1
DASHSCOPE_BITS = 16


def _dashscope_generate(
    text: str,
    output: Path,
    voice: str,
    instruct: str,
    timeout: int,
) -> bool:
    """Generate WAV via DashScope qwen3-tts-instruct-flash-realtime.

    Returns True on success, False on any failure.
    """
    try:
        import dashscope
        from dashscope.audio.qwen_tts_realtime import (
            AudioFormat,
            QwenTtsRealtime,
            QwenTtsRealtimeCallback,
        )
    except ImportError:
        print("[WARN] dashscope not installed. Run: pip install dashscope", file=sys.stderr)
        return False

    api_key = os.environ.get("DASHSCOPE_API_KEY", "").strip()
    if not api_key:
        print("[WARN] DASHSCOPE_API_KEY not set — skipping DashScope backend.", file=sys.stderr)
        return False

    dashscope.api_key = api_key

    pcm_chunks: list[bytes] = []
    done_event = threading.Event()
    error_holder: list[str] = []

    class _Callback(QwenTtsRealtimeCallback):
        def on_open(self) -> None:
            pass

        def on_close(self, code, msg) -> None:  # noqa: ANN001
            done_event.set()

        def on_event(self, response: dict) -> None:  # noqa: ANN001
            try:
                import base64
                evt_type = response.get("type", "")
                if evt_type == "response.audio.delta":
                    pcm_chunks.append(base64.b64decode(response["delta"]))
                elif evt_type == "session.finished":
                    done_event.set()
                elif evt_type == "error":
                    error_holder.append(str(response))
                    done_event.set()
            except Exception as exc:  # noqa: BLE001
                error_holder.append(str(exc))
                done_event.set()

    callback = _Callback()
    try:
        client = QwenTtsRealtime(
            model=DASHSCOPE_MODEL,
            callback=callback,
            url=DASHSCOPE_WSS_URL,
        )
        client.connect()
        session_opts = {
            "voice": voice,
            "response_format": AudioFormat.PCM_24000HZ_MONO_16BIT,
            "mode": "server_commit",
        }
        if instruct:
            session_opts["instructions"] = instruct
            session_opts["optimize_instructions"] = True
        client.update_session(**session_opts)

        # Send text in reasonable chunks to avoid WebSocket frame limits
        chunk_size = 200
        for i in range(0, len(text), chunk_size):
            client.append_text(text[i : i + chunk_size])

        client.finish()
        if not done_event.wait(timeout=timeout):
            error_holder.append("DashScope TTS timed out")

    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] DashScope connection error: {exc}", file=sys.stderr)
        return False

    if error_holder:
        print(f"[ERROR] DashScope TTS error: {error_holder[0]}", file=sys.stderr)
        return False

    if not pcm_chunks:
        print("[ERROR] DashScope returned no audio data.", file=sys.stderr)
        return False

    raw_pcm = b"".join(pcm_chunks)
    wav_bytes = _pcm_to_wav(raw_pcm, DASHSCOPE_SAMPLE_RATE, DASHSCOPE_CHANNELS, DASHSCOPE_BITS)
    output.write_bytes(wav_bytes)
    return True


# ---------------------------------------------------------------------------
# Backend 2: Local qwen-tts package (Qwen3-TTS-12Hz-1.7B-CustomVoice)
# ---------------------------------------------------------------------------

def _local_generate(
    text: str,
    output: Path,
    language: str,
    voice: str,
    instruct: str,
    model_id: str,
    device: str,
) -> bool:
    """Generate WAV using the local qwen-tts package.

    Returns True on success, False on any failure.
    """
    try:
        import torch  # noqa: F401
        from qwen_tts import Qwen3TTSModel
    except ImportError:
        print("[WARN] qwen-tts not installed. Run: pip install qwen-tts", file=sys.stderr)
        return False

    try:
        import torch
        import soundfile as sf
    except ImportError as exc:
        print(f"[WARN] Missing dependency for local backend: {exc}", file=sys.stderr)
        return False

    # Resolve 'auto' device: prefer CUDA, fall back to CPU
    if device == "auto":
        device = "cuda:0" if torch.cuda.is_available() else "cpu"
        print(f"[INFO] Auto device selected: {device}", file=sys.stderr)

    try:
        dtype = torch.bfloat16
        # Try flash_attention_2; fall back to sdpa on older GPUs / CPU
        try:
            model = Qwen3TTSModel.from_pretrained(
                model_id,
                device_map=device,
                dtype=dtype,
                attn_implementation="flash_attention_2",
            )
        except Exception:  # noqa: BLE001
            model = Qwen3TTSModel.from_pretrained(
                model_id,
                device_map=device,
                dtype=dtype,
            )

        wavs, sr = model.generate_custom_voice(
            text=text,
            language=language if language != "Auto" else "Auto",
            speaker=voice,
            instruct=instruct if instruct else "",
        )
        sf.write(str(output), wavs[0], sr)
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] Local qwen-tts failed: {exc}", file=sys.stderr)
        return False


# ---------------------------------------------------------------------------
# Backend 3: edge-tts fallback
# ---------------------------------------------------------------------------

# Map language → edge-tts voice for professional narration
_EDGE_VOICE_MAP: dict[str, str] = {
    "Chinese": "zh-CN-YunyangNeural",
    "English": "en-US-GuyNeural",
    "Japanese": "ja-JP-KeitaNeural",
    "Korean": "ko-KR-InJoonNeural",
    "German": "de-DE-ConradNeural",
    "French": "fr-FR-HenriNeural",
    "Russian": "ru-RU-DmitryNeural",
    "Portuguese": "pt-BR-AntonioNeural",
    "Spanish": "es-ES-AlvaroNeural",
    "Italian": "it-IT-DiegoNeural",
}


def _edge_tts_fallback(text_file: Path, output: Path, language: str) -> bool:
    """Generate WAV via edge-tts (fallback). Returns True on success."""
    tmp_mp3 = output.with_suffix(".edge_tmp.mp3")
    voice = _EDGE_VOICE_MAP.get(language, "zh-CN-YunyangNeural")
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
    cmd = [
        "edge-tts",
        "--voice", voice,
        "--rate", "+5%",
        "--file", str(text_file),
        "--write-media", str(tmp_mp3),
    ]
    if proxy:
        cmd.extend(["--proxy", proxy])
    try:
        subprocess.run(cmd, check=True, timeout=180)
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", str(tmp_mp3),
                "-ar", "24000",
                "-ac", "1",
                "-c:a", "pcm_s16le",
                str(output),
            ],
            check=True,
            timeout=120,
        )
        return output.exists() and output.stat().st_size > 1024
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] edge-tts fallback failed: {exc}", file=sys.stderr)
        return False
    finally:
        try:
            tmp_mp3.unlink(missing_ok=True)
        except Exception:  # noqa: BLE001
            pass


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:  # noqa: C901
    parser = argparse.ArgumentParser(
        description="Generate scene audio using Qwen3-TTS (DashScope → local → edge-tts fallback).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--scene", type=int, required=True, help="Scene number (for logging).")

    text_group = parser.add_mutually_exclusive_group(required=True)
    text_group.add_argument("--text", help="Narration text (inline).")
    text_group.add_argument("--text-file", type=Path, help="Path to a UTF-8 text file.")

    parser.add_argument("--output", type=Path, required=True, help="Output WAV file path.")
    parser.add_argument(
        "--language", default="zh",
        help="Language code: zh/en/ja/ko/de/fr/ru/pt/es/it/auto (default: zh).",
    )
    parser.add_argument(
        "--voice", default="",
        help="Voice/speaker name. Defaults to a recommended voice for the language.",
    )
    parser.add_argument(
        "--instruct", default="",
        help=(
            "Natural-language instruction to guide voice style "
            "(e.g. '专业播音风格，语速适中'). DashScope instruct model only."
        ),
    )
    parser.add_argument(
        "--backend", choices=["auto", "dashscope", "local", "edge"], default="auto",
        help="Force a specific backend (default: auto).",
    )
    parser.add_argument(
        "--local-model",
        default="Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
        help="HuggingFace model ID or local path for the local backend.",
    )
    parser.add_argument(
        "--device", default="auto",
        help="Torch device for local backend (default: auto — uses cuda:0 if available, else cpu).",
    )
    parser.add_argument("--timeout", type=int, default=300, help="Timeout in seconds.")
    parser.add_argument(
        "--no-fallback", action="store_true",
        help="Disable edge-tts fallback; fail hard if primary backends fail.",
    )
    args = parser.parse_args()

    # Resolve text
    if args.text is not None:
        text = args.text
    else:
        text = args.text_file.read_text(encoding="utf-8").strip()

    if not text:
        print("[ERROR] Text is empty.", file=sys.stderr)
        return 1

    language = _normalize_language(args.language)
    args.output.parent.mkdir(parents=True, exist_ok=True)

    # Persist raw text alongside audio for debugging
    text_cache = args.output.with_suffix(".txt")
    text_cache.write_text(text, encoding="utf-8")

    # Resolve voice
    voice_ds = args.voice or _DEFAULT_VOICE_BY_LANG.get(language, "Neil")
    voice_local = args.voice or _LOCAL_DEFAULT_VOICE_BY_LANG.get(language, "Dylan")

    # Resolve instruction
    instruct = args.instruct
    if not instruct:
        instruct = _DEFAULT_INSTRUCT_ZH if language == "Chinese" else _DEFAULT_INSTRUCT_EN

    started = time.time()
    success = False

    backend = args.backend
    print(
        f"[INFO] Scene {args.scene} | lang={language} | backend={backend} | chars={len(text)}",
        file=sys.stderr,
    )

    if backend in ("auto", "dashscope"):
        print(f"[INFO] Trying DashScope API (model={DASHSCOPE_MODEL}, voice={voice_ds}) ...", file=sys.stderr)
        success = _dashscope_generate(
            text=text,
            output=args.output,
            voice=voice_ds,
            instruct=instruct,
            timeout=args.timeout,
        )
        if success:
            print(f"[OK] DashScope → {args.output}", file=sys.stderr)

    if not success and backend in ("auto", "local"):
        print(
            f"[INFO] Trying local model ({args.local_model}, voice={voice_local}) ...",
            file=sys.stderr,
        )
        success = _local_generate(
            text=text,
            output=args.output,
            language=language,
            voice=voice_local,
            instruct=instruct,
            model_id=args.local_model,
            device=args.device,
        )
        if success:
            print(f"[OK] Local model → {args.output}", file=sys.stderr)

    if not success and backend in ("auto", "edge"):
        if args.no_fallback:
            print("[ERROR] All primary backends failed and --no-fallback is set.", file=sys.stderr)
            return 1
        print("[INFO] Trying edge-tts fallback ...", file=sys.stderr)
        success = _edge_tts_fallback(
            text_file=text_cache,
            output=args.output,
            language=language,
        )
        if success:
            print(f"[OK] edge-tts → {args.output}", file=sys.stderr)

    if not success:
        print(f"[ERROR] All backends failed for scene {args.scene}.", file=sys.stderr)
        return 1

    if not args.output.exists() or args.output.stat().st_size <= 1024:
        print(f"[ERROR] Output missing or too small: {args.output}", file=sys.stderr)
        return 1

    elapsed = round(time.time() - started, 2)
    result = {
        "scene": args.scene,
        "output": str(args.output),
        "bytes": args.output.stat().st_size,
        "elapsed_seconds": elapsed,
        "language": language,
    }
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
