#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "faster-whisper>=1.0.0",
#   "anthropic>=0.40.0",
#   "Pillow>=10.0.0",
#   "yt-dlp>=2024.1.0",
# ]
# ///
"""
video_to_golden.py — 从满意的视频提取 golden script，集成到 better-harness 优化流程。

用法:
    uv run python scripts/video_to_golden.py <video.mp4|YouTube-URL> [options]

选项:
    --topic TEXT         视频话题（不填则从视频内容自动推断）
    --duration TEXT      时长规格，如 "1-3min"、"3-5min" [默认: 1-3min]
    --style TEXT         风格 professional/casual/storytelling [默认: professional]
    --aspect-ratio TEXT  画面比例 16:9、9:16 等 [默认: 16:9]
    --golden-dir PATH    golden 文件保存目录 [默认: tests/evals/fixtures]
    --harness-toml PATH  harness 配置路径 [默认: harness/video-maker-minimal.toml]
    --proxy TEXT         HTTP 代理（默认读 HTTP_PROXY 环境变量）

输出:
    tests/evals/fixtures/golden_script.md    — 从视频重建的脚本
    tests/evals/fixtures/golden_rubric.md    — 质量评分标准
    tests/evals/fixtures/golden_props.json   — 结构属性（供 eval 断言使用）
    tests/evals/test_script_llm_golden.py    — pytest eval 测试文件
    harness/video-maker-minimal.toml         — 自动追加 golden cases
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path


# ─────────────────────────────────────────────────────────────────────────────
# 0. 环境检查 & YouTube 下载
# ─────────────────────────────────────────────────────────────────────────────

def _is_url(s: str) -> bool:
    return s.startswith("http://") or s.startswith("https://")


def _check_ffmpeg() -> bool:
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def _check_whisper() -> bool:
    try:
        import faster_whisper  # noqa: F401
        return True
    except ImportError:
        return False


def _check_ytdlp() -> bool:
    try:
        subprocess.run(["yt-dlp", "--version"], capture_output=True, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def download_youtube_video(
    url: str,
    out_dir: Path,
    proxy: str | None = None,
    cookies: str | None = None,
    cookies_from_browser: str | None = None,
) -> Path:
    """用 yt-dlp 下载 YouTube 视频，返回下载后的 mp4 路径。"""
    out_dir.mkdir(parents=True, exist_ok=True)
    output_tmpl = str(out_dir / "%(title).80s [%(id)s].%(ext)s")
    cmd = [
        "yt-dlp",
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best",
        "--merge-output-format", "mp4",
        "-o", output_tmpl,
        "--no-playlist",
        "--progress",
        "--newline",
        url,
    ]
    if proxy:
        cmd += ["--proxy", proxy]
    if cookies:
        cmd += ["--cookies", cookies]
    if cookies_from_browser:
        cmd += ["--cookies-from-browser", cookies_from_browser]

    print(f"[INFO] yt-dlp 下载: {url}")
    result = subprocess.run(cmd, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        print(f"[ERROR] yt-dlp 下载失败（exit {result.returncode}）")
        sys.exit(1)

    # 找到下载好的 mp4 文件
    mp4_files = list(out_dir.glob("*.mp4"))
    if not mp4_files:
        print("[ERROR] yt-dlp 完成但未找到 .mp4 文件")
        sys.exit(1)
    # 取最新的
    return max(mp4_files, key=lambda p: p.stat().st_mtime)


def _load_dot_env() -> None:
    dot_env = Path(".env")
    if not dot_env.exists():
        return
    for line in dot_env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    if os.environ.get("ANTHROPIC_AUTH_TOKEN") and not os.environ.get("ANTHROPIC_API_KEY"):
        os.environ["ANTHROPIC_API_KEY"] = os.environ["ANTHROPIC_AUTH_TOKEN"]


# ─────────────────────────────────────────────────────────────────────────────
# 1. 在视频附近查找现有 script.md（优先级最高，避免重复提取）
# ─────────────────────────────────────────────────────────────────────────────

def find_existing_script(video_path: Path) -> Path | None:
    """向上遍历 4 层目录，寻找最近的 script.md。"""
    sibling = video_path.parent / "script.md"
    if sibling.exists():
        return sibling
    current = video_path.parent
    for _ in range(4):
        candidates = sorted(current.glob("**/script.md"))
        if candidates:
            return candidates[0]
        current = current.parent
    return None


# ─────────────────────────────────────────────────────────────────────────────
# 2. 音频提取 + 语音转录
# ─────────────────────────────────────────────────────────────────────────────

def extract_audio(video_path: Path, out_dir: Path) -> Path:
    """用 ffmpeg 提取单声道 16kHz WAV。"""
    audio_path = out_dir / "audio.wav"
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(video_path),
         "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
         str(audio_path)],
        capture_output=True, check=True,
    )
    return audio_path


def transcribe_audio(audio_path: Path) -> list[dict]:
    """用 faster-whisper 转录音频，返回带时间戳的 segment 列表。"""
    from faster_whisper import WhisperModel
    model = WhisperModel("base", device="cpu", compute_type="int8")
    segments, _info = model.transcribe(str(audio_path), beam_size=5)
    return [
        {"start": round(seg.start, 2), "end": round(seg.end, 2), "text": seg.text.strip()}
        for seg in segments
    ]


# ─────────────────────────────────────────────────────────────────────────────
# 3. 场景边界检测（ffmpeg scene filter）
# ─────────────────────────────────────────────────────────────────────────────

def detect_scene_timestamps(video_path: Path) -> list[float]:
    """返回场景切换时间戳列表（含 0.0 和总时长作为首尾）。"""
    # 获取总时长
    dur_result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "csv=print_section=0", str(video_path)],
        capture_output=True, text=True, check=True,
    )
    total = round(float(dur_result.stdout.strip()), 2)

    # 场景变化检测
    scene_result = subprocess.run(
        ["ffmpeg", "-i", str(video_path),
         "-vf", "select=gt(scene\\,0.25),showinfo",
         "-vsync", "vfr", "-f", "null", "-"],
        capture_output=True, text=True,
    )

    timestamps = [0.0]
    for line in scene_result.stderr.splitlines():
        m = re.search(r"pts_time:([\d.]+)", line)
        if m:
            timestamps.append(round(float(m.group(1)), 2))
    timestamps.append(total)
    return sorted(set(timestamps))


# ─────────────────────────────────────────────────────────────────────────────
# 4. 关键帧提取（base64 JPEG）
# ─────────────────────────────────────────────────────────────────────────────

def extract_keyframe_b64(video_path: Path, timestamp: float) -> str | None:
    """提取指定时间戳的视频帧，返回 base64 JPEG 字符串。失败返回 None。"""
    try:
        result = subprocess.run(
            ["ffmpeg", "-y", "-ss", str(timestamp), "-i", str(video_path),
             "-frames:v", "1", "-q:v", "4", "-f", "image2pipe", "-vcodec", "mjpeg", "pipe:1"],
            capture_output=True, check=True,
        )
        return base64.b64encode(result.stdout).decode()
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# 5. 用 Claude 视觉 API 从视频重建 script.md
# ─────────────────────────────────────────────────────────────────────────────

def reconstruct_script_from_video(
    transcript: list[dict],
    scene_timestamps: list[float],
    video_path: Path,
    topic: str,
    duration: str,
    style: str,
    aspect_ratio: str,
    client,
) -> str:
    """用 Claude 多模态 API，根据截图 + 转录文本重建 script.md。"""

    # 将 transcript segments 分配到各场景
    scenes = []
    for i in range(len(scene_timestamps) - 1):
        start, end = scene_timestamps[i], scene_timestamps[i + 1]
        dur = round(end - start, 1)
        narration = " ".join(
            s["text"] for s in transcript
            if s["start"] >= start - 0.5 and s["end"] <= end + 0.5
        ).strip()
        frame_ts = start + (end - start) / 3
        frame_b64 = extract_keyframe_b64(video_path, frame_ts)
        scenes.append({
            "idx": i + 1, "start": start, "end": end,
            "duration": dur, "narration": narration, "frame_b64": frame_b64,
        })

    # 构建多模态消息
    content: list[dict] = [{
        "type": "text",
        "text": (
            f"你是视频脚本分析专家。根据以下视频场景信息（截图 + 旁白），"
            f"重建符合 script.md 格式的完整脚本。\n\n"
            f"视频参数：话题={topic}，时长={duration}，风格={style}，比例={aspect_ratio}\n"
        ),
    }]

    for s in scenes:
        content.append({
            "type": "text",
            "text": f"\n### 场景 {s['idx']}（{s['duration']}s）\n旁白：{s['narration'] or '（无旁白）'}\n",
        })
        if s["frame_b64"]:
            content.append({
                "type": "image",
                "source": {"type": "base64", "media_type": "image/jpeg", "data": s["frame_b64"]},
            })

    content.append({
        "type": "text",
        "text": """
请重建完整 script.md，格式要求：
1. 顶部 ```style_spine 代码块（含 lut_style, aspect_ratio, style_template, visual_strategy, pacing, tone, glossary）
2. 每个场景：
   ## Scene N: {标题}
   type: narration|data_card|quote_card|title_card|transition
   narrative_role: hook|setup|development|climax|cta
   narration: |
     {旁白}
   scene_intent:
     story_beat: ...
     data_story: ...
     emotional_target: ...
     pacing: ...
   content_brief: |
     {视觉创意描述}
   duration_estimate: {秒数}
3. 末尾 ## Audio Design 段落

直接从 ```style_spine 开始输出，不要任何解释。
""",
    })

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        messages=[{"role": "user", "content": content}],
    )
    return response.content[0].text.strip()


# ─────────────────────────────────────────────────────────────────────────────
# 6. 从 golden script 提炼质量 rubric
# ─────────────────────────────────────────────────────────────────────────────

def extract_rubric(script_content: str, client) -> str:
    """用 Claude 从 golden script 提炼 6-8 条可操作的评分标准。"""
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": f"""分析以下高质量视频脚本，提炼 6-8 条评分标准（rubric），
用于自动评估新脚本是否达到同等质量。

每条标准必须：
- 描述可观察的具体行为（不是"要好"，而是精确条件）
- 说明为什么重要（1句）
- 给出 5分（优）/ 3分（及格）/ 1分（差）的判断依据

输出格式（Markdown）：
## 脚本质量评分标准（Golden Rubric）

### 1. [维度名]
**描述**：...
**重要性**：...
**5分**：... | **3分**：... | **1分**：...

（共 6-8 条）

Golden Script（前 4000 字）：
---
{script_content[:4000]}
---
"""}],
    )
    return response.content[0].text.strip()


# ─────────────────────────────────────────────────────────────────────────────
# 7. 解析 golden script 的结构属性（用于 deterministic 断言）
# ─────────────────────────────────────────────────────────────────────────────

def analyze_structure(script_content: str) -> dict:
    scene_blocks = re.findall(
        r"(?ms)^## Scene\b.*?(?=^## Scene\b|^## Audio\b|\Z)", script_content
    )
    scene_count = len(scene_blocks)

    types = re.findall(r"(?m)^type:\s*(\S+)", script_content)
    type_counts: dict[str, int] = {}
    for t in types:
        type_counts[t] = type_counts.get(t, 0) + 1

    durations = [int(d) for d in re.findall(r"duration_estimate:\s*(\d+)", script_content)]
    total_dur = sum(durations)

    roles = re.findall(r"narrative_role:\s*(\w+)", script_content)
    role_set = set(roles)

    data_cards = type_counts.get("data_card", 0)
    ratio = round(data_cards / scene_count, 2) if scene_count else 0

    return {
        "scene_count": scene_count,
        "scene_count_min": max(1, scene_count - 4),
        "scene_count_max": scene_count + 4,
        "total_duration": total_dur,
        "duration_min": max(10, int(total_dur * 0.6)),
        "duration_max": int(total_dur * 1.5),
        "max_single_scene": max(durations) if durations else 20,
        "data_card_count": data_cards,
        "data_card_ratio": ratio,
        "data_card_ratio_min": max(0.0, round(ratio - 0.10, 2)),
        "has_hook": "hook" in role_set,
        "has_climax": "climax" in role_set,
        "has_cta": "cta" in role_set,
        "has_style_spine": bool(re.search(r"```style_spine", script_content)),
        "has_audio_design": bool(re.search(r"## Audio Design", script_content)),
        "has_glossary": bool(re.search(r"glossary:\s*\[", script_content)),
        "type_counts": type_counts,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 8. 生成 eval 测试文件
# ─────────────────────────────────────────────────────────────────────────────

def generate_eval_test_file(props: dict, topic: str, duration: str, style: str, aspect_ratio: str) -> str:
    """生成 tests/evals/test_script_llm_golden.py 内容。"""
    p = props  # shorthand

    # 用占位符替换避免 f-string 嵌套问题
    lines = [
        '"""Golden reference eval cases — auto-generated by scripts/video_to_golden.py.',
        '',
        f'Source topic  : {topic}',
        f'Source duration: {duration}',
        f'Source style  : {style}',
        '',
        'Train  → test_llm_scriptwriter_matches_golden_structure',
        'Holdout → test_llm_scriptwriter_golden_quality_judge',
        '"""',
        '',
        'from __future__ import annotations',
        '',
        'import json',
        'import re',
        'import pytest',
        'from pathlib import Path',
        '',
        'from deepagents_video_maker.models import MilestoneStatus, VideoMakerGoal',
        'from deepagents_video_maker.params import derive_video_params',
        'from deepagents_video_maker.script_flow import start_script_milestone',
        'from deepagents_video_maker.session import init_video_session',
        '',
        'from .conftest import invoke_scriptwriter',
        '',
        'GOLDEN_RUBRIC_PATH = Path(__file__).parent / "fixtures" / "golden_rubric.md"',
        '',
        '',
        '# ---------------------------------------------------------------------------',
        '# Research fixture — same domain as the golden video',
        '# ---------------------------------------------------------------------------',
        '',
        '@pytest.fixture',
        'def golden_research():',
        f'    """Representative research for topic: {topic}."""',
        '    return """# Research Report: ' + topic + r"""

## 1. Executive Summary
This research report covers the same domain as the golden reference video.
Use it to evaluate whether the scriptwriter can produce comparable quality.

## 2. Data Points
- Key metric 1: 75% adoption rate among target segment
- Key metric 2: $2.5B market size, growing at 40% YoY
- Key metric 3: 3x productivity improvement in controlled studies
- Key metric 4: 89% user satisfaction score

## 3. Visual Strategy
visual_strategy: image_light
Recommend images for: hook scene (dramatic visual), climax scene (data visualization)

## 4. Key Findings
Primary finding drives the hook. Secondary findings build development chapters.
The climax presents the most surprising or impactful insight.

## 5. Technical Details
Supporting technical context for development sections.
Include relevant mechanisms and evidence.

## 6. Style Spine
lut_style: tech_cool
tone: professional, confident
style_template: tech-noir

## 7. Narrative Flow
Hook (surprising fact) → Setup (why it matters) → Development (how it works)
→ Climax (biggest insight/data) → CTA (what to do next)

## 8. Additional Data
- Supporting metric A: 85% precision in benchmark tests
- Supporting metric B: 40% cost reduction vs baseline
- Supporting metric C: 12-month payback period

## 9. Quotes
"A compelling, quotable insight about this topic." - Domain Expert, Institution
""",
        '',
        '',
        '@pytest.fixture',
        f'def setup_golden_session(tmp_path, golden_research):',
        '    goal = VideoMakerGoal(',
        f'        topic="{topic}",',
        '        source="local-file",',
        '        local_file="research.md",',
        '    )',
        f'    goal.duration = "{duration}"',
        f'    goal.style = "{style}"',
        f'    goal.aspect_ratio = "{aspect_ratio}"',
        '    goal = derive_video_params(goal)',
        '    state = init_video_session(goal, tmp_path, timestamp="golden-eval01")',
        '    rm = state.milestone("research")',
        '    rm.status = MilestoneStatus.COMPLETED',
        '    rm.current_run = 1',
        '    rd = Path(state.output_dir) / "artifacts" / "research" / "run-1"',
        '    rd.mkdir(parents=True, exist_ok=True)',
        '    (rd / "research.md").write_text(golden_research, encoding="utf-8")',
        '    return {"goal": goal, "state": state}',
        '',
        '',
        '# ---------------------------------------------------------------------------',
        '# Train case — structure: matches golden structural properties',
        '# ---------------------------------------------------------------------------',
        '',
        'def test_llm_scriptwriter_matches_golden_structure(setup_golden_session, llm_client, model):',
        '    """Script structure must match golden reference properties.',
        '',
        '    Criteria extracted from golden script analysis:',
        f'    - Scene count    : {p["scene_count_min"]}-{p["scene_count_max"]} (golden had {p["scene_count"]})',
        f'    - Total duration : {p["duration_min"]}-{p["duration_max"]}s (golden was {p["total_duration"]}s)',
        f'    - data_card ratio: >={p["data_card_ratio_min"]:.0%} (golden had {p["data_card_ratio"]:.0%})',
        '    - Narrative arc  : hook → climax → cta',
        '    - style_spine + glossary present',
        '    - Audio Design section present',
        '    """',
        '    goal = setup_golden_session["goal"]',
        '    state = setup_golden_session["state"]',
        '    run = start_script_milestone(state)',
        '    run_dir = Path(run.run_dir)',
        '    rd = Path(state.output_dir) / "artifacts" / "research" / "run-1"',
        '    research = (rd / "research.md").read_text(encoding="utf-8")',
        '    ok, err = invoke_scriptwriter(llm_client, goal, research, run_dir)',
        '    assert ok, f"invoke_scriptwriter failed: {err}"',
        '    script = (run_dir / "script.md").read_text(encoding="utf-8")',
        '',
        '    # --- Scene count ---',
        r'    blocks = re.findall(r"(?ms)^## Scene\b.*?(?=^## Scene\b|^## Audio\b|\Z)", script)',
        '    scene_count = len(blocks)',
        f'    assert {p["scene_count_min"]} <= scene_count <= {p["scene_count_max"]}, (',
        f'        f"Scene count {{scene_count}} outside golden range [{p["scene_count_min"]}, {p["scene_count_max"]}]. '
        f'Golden had {p["scene_count"]}."',
        '    )',
        '',
        '    # --- Total duration ---',
        r'    durs = [int(d) for d in re.findall(r"duration_estimate:\s*(\d+)", script)]',
        '    total_dur = sum(durs)',
        f'    assert {p["duration_min"]} <= total_dur <= {p["duration_max"]}, (',
        f'        f"Total duration {{total_dur}}s outside golden range [{p["duration_min"]}, {p["duration_max"]}]s."',
        '    )',
        '',
        '    # --- data_card ratio ---',
        r'    scene_types = re.findall(r"(?m)^type:\s*(\S+)", script)',
        '    data_cards = sum(1 for t in scene_types if t == "data_card")',
        '    if scene_count > 0:',
        '        ratio = data_cards / scene_count',
        f'        assert ratio >= {p["data_card_ratio_min"]:.2f}, (',
        f'            f"data_card ratio {{ratio:.0%}} below golden minimum {p["data_card_ratio_min"]:.0%}. '
        f'Golden had {p["data_card_count"]} data_cards."',
        '        )',
        '',
        '    # --- Narrative arc ---',
        r'    roles = set(re.findall(r"narrative_role:\s*(\w+)", script))',
        '    assert "hook" in roles, f"Missing hook scene. Roles: {sorted(roles)}"',
        '    assert "climax" in roles, f"Missing climax scene. Roles: {sorted(roles)}"',
        '    assert "cta" in roles, f"Missing cta scene. Roles: {sorted(roles)}"',
        '',
        '    # --- style_spine + glossary ---',
        r'    assert re.search(r"```style_spine", script), "Missing ```style_spine block"',
        r'    assert re.search(r"glossary:\s*\[", script), "style_spine missing glossary"',
        '',
        '    # --- Audio Design ---',
        '    assert "## Audio Design" in script, "Missing ## Audio Design section"',
        '',
        '',
        '# ---------------------------------------------------------------------------',
        '# Holdout case - scene_quality: LLM judge >= 4/5 on golden rubric',
        '# ---------------------------------------------------------------------------',
        '',
        'def test_llm_scriptwriter_golden_quality_judge(setup_golden_session, llm_client, model):',
        '    """LLM judge must score the script >= 4/5 on the golden rubric.',
        '',
        '    The judge uses the rubric extracted from the golden reference video — it does NOT',
        '    see the golden script itself, preventing superficial similarity bias.',
        '    The rubric captures qualitative principles (hook quality, narrative flow, etc.)',
        '    that cannot be measured by structural assertions alone.',
        '    """',
        '    if not GOLDEN_RUBRIC_PATH.exists():',
        '        pytest.skip(f"Golden rubric not found at {GOLDEN_RUBRIC_PATH}")',
        '',
        '    goal = setup_golden_session["goal"]',
        '    state = setup_golden_session["state"]',
        '    run = start_script_milestone(state)',
        '    run_dir = Path(run.run_dir)',
        '    rd = Path(state.output_dir) / "artifacts" / "research" / "run-1"',
        '    research = (rd / "research.md").read_text(encoding="utf-8")',
        '    ok, err = invoke_scriptwriter(llm_client, goal, research, run_dir)',
        '    assert ok, f"invoke_scriptwriter failed: {err}"',
        '    script = (run_dir / "script.md").read_text(encoding="utf-8")',
        '    rubric = GOLDEN_RUBRIC_PATH.read_text(encoding="utf-8")',
        '',
        '    from langchain_core.messages import HumanMessage, SystemMessage',
        '',
        '    judge_sys = (',
        '        "你是视频脚本评审专家。根据以下评分标准对脚本打 1-5 分（整数）。\\n\\n"',
        '        + rubric',
        '        + "\\n\\n只输出 JSON，格式：{\\"score\\": <1-5>, \\"reasoning\\": \\"<一句话>\\"}\\n不要其他内容。"',
        '    )',
        '    response = llm_client.invoke([',
        '        SystemMessage(content=judge_sys),',
        '        HumanMessage(content=f"请评审以下脚本：\\n\\n{script[:3000]}"),',
        '    ])',
        '',
        '    raw = response.content if isinstance(response.content, str) else str(response.content)',
        '    m = re.search(r\'"score"\\s*:\\s*([1-5])\', raw)',
        '    assert m, f"Judge returned unparseable response: {raw[:300]}"',
        '    score = int(m.group(1))',
        '',
        '    reason_m = re.search(r\'"reasoning"\\s*:\\s*"([^"]+)"\', raw)',
        '    reasoning = reason_m.group(1) if reason_m else ""',
        '',
        '    assert score >= 4, (',
        '        f"LLM judge scored {score}/5 (need >=4). Reasoning: {reasoning}\\n\\n"',
        '        f"Script preview: {script[:400]}"',
        '    )',
    ]
    return "\n".join(lines) + "\n"


# ─────────────────────────────────────────────────────────────────────────────
# 9. 更新 harness TOML
# ─────────────────────────────────────────────────────────────────────────────

def update_harness_toml(toml_path: Path) -> None:
    content = toml_path.read_text(encoding="utf-8")
    if "test_script_llm_golden" in content:
        print("[INFO] Golden cases already present in TOML, skipping.")
        return

    addition = """
# Golden reference cases — auto-generated by scripts/video_to_golden.py
[[cases]]
case_id = "tests/evals/test_script_llm_golden.py::test_llm_scriptwriter_matches_golden_structure"
split = "train"
stratum = "structure"

[[cases]]
case_id = "tests/evals/test_script_llm_golden.py::test_llm_scriptwriter_golden_quality_judge"
split = "holdout"
stratum = "scene_quality"
"""
    toml_path.write_text(content + addition, encoding="utf-8")
    print(f"[OK] Updated {toml_path} with golden cases")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="从满意的视频提取 golden script，集成到 better-harness"
    )
    parser.add_argument(
        "video",
        help="本地视频文件路径（.mp4）或 YouTube URL（https://...）",
    )
    parser.add_argument("--topic", default=None, help="视频话题（不填则自动推断）")
    parser.add_argument("--duration", default="1-3min")
    parser.add_argument("--style", default="professional")
    parser.add_argument("--aspect-ratio", default="16:9", dest="aspect_ratio")
    parser.add_argument("--golden-dir", type=Path, default=Path("tests/evals/fixtures"),
                        dest="golden_dir")
    parser.add_argument("--yt-dir", type=Path, default=Path("yt_videos"),
                        dest="yt_dir",
                        help="YouTube 视频下载目录 [默认: yt_videos]")
    parser.add_argument("--harness-toml", type=Path,
                        default=Path("harness/video-maker-minimal.toml"),
                        dest="harness_toml")
    parser.add_argument("--proxy", default=None,
                        help="HTTP 代理（默认读 HTTP_PROXY 环境变量，如 http://127.0.0.1:7897）")
    parser.add_argument("--cookies", default=None,
                        help="yt-dlp cookies 文件路径（Netscape 格式，用于 YouTube 认证）")
    parser.add_argument("--cookies-from-browser", default=None, dest="cookies_from_browser",
                        help="从浏览器读取 cookies（如 chrome、edge、firefox）")
    args = parser.parse_args()

    _load_dot_env()

    # ── 确定代理 ────────────────────────────────────────────────────────────
    proxy = args.proxy or os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")

    # ── 解析输入：URL or 本地文件 ───────────────────────────────────────────
    if _is_url(args.video):
        if not _check_ytdlp():
            print("[ERROR] 未找到 yt-dlp，请先安装: pip install yt-dlp 或 uv add yt-dlp")
            sys.exit(1)
        print(f"[INFO] 检测到 YouTube URL，开始下载...")
        dl_dir = args.yt_dir
        video_path = download_youtube_video(
            args.video, dl_dir, proxy,
            cookies=args.cookies,
            cookies_from_browser=args.cookies_from_browser,
        )
        print(f"[OK]  下载完成: {video_path}")
    else:
        video_path = Path(args.video).resolve()
        if not video_path.exists():
            print(f"[ERROR] 视频文件不存在: {video_path}")
            sys.exit(1)

    import anthropic
    client = anthropic.Anthropic(
        api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
        base_url=os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com"),
    )

    args.golden_dir.mkdir(parents=True, exist_ok=True)

    # ── Step 1: 查找现有 script.md ──────────────────────────────────────────
    print(f"\n[INFO] Step 1: 查找 {video_path.name} 附近的 script.md...")
    existing = find_existing_script(video_path)

    if existing:
        print(f"[OK]  找到现有脚本: {existing}")
        golden_script = existing.read_text(encoding="utf-8")
        topic = args.topic or "Video Topic"
    else:
        print("[INFO] 未找到现有脚本，从视频提取...")

        if not _check_ffmpeg():
            print("[ERROR] 未找到 ffmpeg，请先安装: https://ffmpeg.org/download.html")
            sys.exit(1)
        if not _check_whisper():
            print("[ERROR] faster-whisper 未安装。请运行: uv add faster-whisper")
            sys.exit(1)

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            print("[INFO] Step 1a: 提取音频...")
            audio_path = extract_audio(video_path, tmp_path)

            print("[INFO] Step 1b: Whisper 转录（base 模型）...")
            transcript = transcribe_audio(audio_path)
            print(f"       → {len(transcript)} 个语音段")

            print("[INFO] Step 1c: 检测场景切换...")
            scene_ts = detect_scene_timestamps(video_path)
            print(f"       → {len(scene_ts)-1} 个场景")

            # 自动推断话题
            topic = args.topic
            if not topic:
                sample = " ".join(s["text"] for s in transcript[:8])
                resp = client.messages.create(
                    model="claude-haiku-4-5-20251001", max_tokens=50,
                    messages=[{"role": "user", "content": f"用5字以内概括视频主题，只输出主题词：\n{sample}"}],
                )
                topic = resp.content[0].text.strip()
                print(f"       → 推断话题: {topic}")

            print("[INFO] Step 1d: Claude 视觉 API 重建 script.md...")
            golden_script = reconstruct_script_from_video(
                transcript, scene_ts, video_path,
                topic, args.duration, args.style, args.aspect_ratio, client,
            )

    # ── Step 2: 保存 golden script ──────────────────────────────────────────
    golden_script_path = args.golden_dir / "golden_script.md"
    golden_script_path.write_text(golden_script, encoding="utf-8")
    print(f"\n[OK]  Step 2: golden_script.md → {golden_script_path}")

    # ── Step 3: 提炼 rubric ──────────────────────────────────────────────────
    print("\n[INFO] Step 3: 提炼质量评分标准（rubric）...")
    rubric = extract_rubric(golden_script, client)
    rubric_path = args.golden_dir / "golden_rubric.md"
    rubric_path.write_text(rubric, encoding="utf-8")
    print(f"[OK]  golden_rubric.md → {rubric_path}")

    # ── Step 4: 解析结构属性 ─────────────────────────────────────────────────
    print("\n[INFO] Step 4: 解析 golden 结构属性...")
    props = analyze_structure(golden_script)
    props_path = args.golden_dir / "golden_props.json"
    props_path.write_text(json.dumps(props, indent=2, ensure_ascii=False), encoding="utf-8")
    print(
        f"[OK]  golden_props.json → {props_path}\n"
        f"      场景数={props['scene_count']}, 总时长={props['total_duration']}s, "
        f"data_card比例={props['data_card_ratio']:.0%}"
    )

    # ── Step 5: 生成 eval 测试文件 ───────────────────────────────────────────
    print("\n[INFO] Step 5: 生成 eval 测试文件...")
    test_content = generate_eval_test_file(
        props, topic, args.duration, args.style, args.aspect_ratio
    )
    test_path = Path("tests/evals/test_script_llm_golden.py")
    test_path.write_text(test_content, encoding="utf-8")
    print(f"[OK]  test_script_llm_golden.py → {test_path}")

    # ── Step 6: 更新 harness TOML ────────────────────────────────────────────
    print("\n[INFO] Step 6: 更新 harness TOML...")
    if args.harness_toml.exists():
        update_harness_toml(args.harness_toml)
    else:
        print(f"[INFO] TOML 不存在于 {args.harness_toml}，跳过。")

    # ── 完成 ─────────────────────────────────────────────────────────────────
    print(f"""
╔══════════════════════════════════════════════════════════╗
║  [OK] 全部完成！                                          ║
╠══════════════════════════════════════════════════════════╣
║  生成文件：                                               ║
║    {str(golden_script_path):<52} ║
║    {str(rubric_path):<52} ║
║    {str(props_path):<52} ║
║    {str(test_path):<52} ║
╠══════════════════════════════════════════════════════════╣
║  后续步骤：                                               ║
║  1. 检查 tests/evals/fixtures/golden_rubric.md           ║
║     确认 rubric 准确反映你的质量标准                       ║
║  2. 可选：编辑 test_script_llm_golden.py 中的             ║
║     golden_research fixture 使其更贴合真实话题            ║
║  3. 运行: pnpm harness:run                               ║
╚══════════════════════════════════════════════════════════╝
""")


if __name__ == "__main__":
    main()
