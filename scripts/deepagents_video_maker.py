"""Run the project video-maker workflow with the DeepAgents SDK."""

from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path
from typing import Any, Iterable

from langchain_core.tools import tool


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEEPAGENTS_HOME = Path.home() / ".deepagents"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_env_files() -> None:
    """Load simple KEY=VALUE pairs from project and DeepAgents env files."""
    for env_path in [DEEPAGENTS_HOME / ".env", PROJECT_ROOT / ".env"]:
        if not env_path.exists():
            continue
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ[key] = value

    if os.environ.get("LANGSMITH_TRACING", "").lower() == "true":
        os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")


def resolve_model(model: Any) -> Any:
    """Resolve provider shortcuts, including DeepSeek OpenAI-compatible config."""
    if not isinstance(model, str):
        return model

    normalized = model.strip()
    deepseek_requested = normalized.startswith("deepseek:")
    deepseek_env_present = bool(os.environ.get("DEEPSEEK_API_KEY"))
    if not deepseek_requested and not (deepseek_env_present and normalized.startswith("deepseek-")):
        return normalized

    from langchain_openai import ChatOpenAI

    model_name = normalized.split(":", 1)[1] if deepseek_requested else normalized
    api_key = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("DeepSeek requires DEEPSEEK_API_KEY or OPENAI_API_KEY.")
    base_url = (
        os.environ.get("DEEPSEEK_BASE_URL")
        or os.environ.get("DEEPSEEK_API_BASE")
        or os.environ.get("OPENAI_BASE_URL")
        or "https://api.deepseek.com"
    )
    thinking_type = os.environ.get("DEEPSEEK_THINKING", "disabled").strip().lower()
    return ChatOpenAI(
        model=model_name,
        api_key=api_key,
        base_url=base_url,
        extra_body={"thinking": {"type": thinking_type}},
        max_retries=5,
        timeout=120,
    )


def _ensure_under_project(path: Path) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(PROJECT_ROOT)
    except ValueError as exc:
        raise ValueError(f"cwd must stay under project root: {PROJECT_ROOT}") from exc
    return resolved


def to_virtual_path(path: str) -> str:
    """Normalize common local/project paths to DeepAgents virtual paths."""
    if not isinstance(path, str):
        return path
    raw = path.strip()
    if raw.startswith("/workspace/"):
        return "/" + raw.removeprefix("/workspace/")
    candidate = Path(raw)
    if candidate.is_absolute():
        try:
            rel = candidate.resolve().relative_to(PROJECT_ROOT)
            return "/" + str(rel).replace("\\", "/")
        except Exception:
            return raw
    return raw


def patch_deepagents_path_validation() -> None:
    """Let DeepAgents file tools tolerate project-local Windows absolute paths."""
    try:
        import deepagents.middleware.filesystem as fs
    except Exception:
        return
    validator_name = "_validate_path" if hasattr(fs, "_validate_path") else "validate_path"
    original = getattr(fs, validator_name, None)
    if original is None:
        return
    if getattr(original, "_video_maker_patched", False):
        return

    def _patched(path: str) -> str:
        return original(to_virtual_path(path))

    _patched._video_maker_patched = True  # type: ignore[attr-defined]
    setattr(fs, validator_name, _patched)


@tool
def execute_pwsh(command: str, cwd: str = ".") -> str:
    """Execute a PowerShell 7 command under the project root and return output."""
    workdir = _ensure_under_project((PROJECT_ROOT / cwd).resolve())
    pwsh = Path(r"C:\Program Files\PowerShell\7\pwsh.exe")
    if not pwsh.exists():
        raise RuntimeError(f"PowerShell 7 not found: {pwsh}")
    completed = subprocess.run(
        [str(pwsh), "-NoLogo", "-NoProfile", "-Command", command],
        cwd=str(workdir),
        text=True,
        capture_output=True,
        timeout=900,
    )
    output = [
        f"cwd: {workdir}",
        f"exit_code: {completed.returncode}",
    ]
    if completed.stdout:
        output.append("stdout:\n" + completed.stdout[-12000:])
    if completed.stderr:
        output.append("stderr:\n" + completed.stderr[-12000:])
    return "\n".join(output)


@tool
def project_glob(pattern: str) -> str:
    """Find project files matching a glob pattern and return relative paths."""
    matches: Iterable[Path] = PROJECT_ROOT.glob(pattern)
    rels = sorted(
        str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")
        for path in matches
        if ".git" not in path.parts and "node_modules" not in path.parts
    )
    return "\n".join(rels[:500]) or "(no matches)"


def build_agent(model: Any, interrupt: bool = False, checkpointer: bool = False):
    patch_deepagents_path_validation()

    import sys
    sys.path.insert(0, str(PROJECT_ROOT / "src"))
    os.environ.setdefault("ORCHESTRATOR_SKILLS_ROOT", str(PROJECT_ROOT))

    from deepagents_video_maker.agent import create_video_maker_agent

    return create_video_maker_agent(
        resolve_model(model),
        project_root=PROJECT_ROOT,
        interrupt=interrupt,
        checkpointer=None,
    )


def check_files() -> None:
    init_path = PROJECT_ROOT / "src" / "deepagents_video_maker" / "__init__.py"
    skill_path = PROJECT_ROOT / "skills" / "video-maker" / "SKILL.md"
    missing = []
    if not init_path.exists():
        missing.append(str(init_path.relative_to(PROJECT_ROOT)))
    if not skill_path.exists():
        missing.append(str(skill_path.relative_to(PROJECT_ROOT)))
    if missing:
        raise SystemExit("Missing required files:\n" + "\n".join(missing))
    print("OK: deepagents-video-maker files are present.")
    print(f"Project root: {PROJECT_ROOT}")


def main() -> None:
    load_env_files()
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=os.environ.get("DEEPAGENTS_MODEL", "anthropic:claude-sonnet-4-5-20250929"))
    parser.add_argument("--thread-id", default="video-maker-local")
    parser.add_argument("--check", action="store_true", help="Validate files without invoking an LLM.")
    parser.add_argument("--interrupt", action="store_true", help="Pause before writes/edits/shell execution.")
    parser.add_argument("prompt", nargs="*", help="Video-maker request to run.")
    args = parser.parse_args()

    check_files()
    if args.check:
        return

    if not args.prompt:
        raise SystemExit("Provide a prompt, or use --check.")

    agent = build_agent(args.model, interrupt=args.interrupt, checkpointer=False)
    result = agent.invoke(
        {"messages": [{"role": "user", "content": " ".join(args.prompt)}]},
        config={"configurable": {"thread_id": args.thread_id}, "recursion_limit": 100},
    )
    messages = result.get("messages", [])
    if messages:
        print(messages[-1].content)
    else:
        print(result)


if __name__ == "__main__":
    main()
