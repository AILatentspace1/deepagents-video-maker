"""Real DeepAgents invoke smoke test using ZhipuAI Anthropic-compatible backend.

Uses glm-5-turbo via ZhipuAI's Anthropic-compatible endpoint.
Credentials are loaded from E:/workspace/orchestrator_skills/.env.
"""
from __future__ import annotations
import os, sys, time, traceback
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ORCHESTRATOR_SKILLS_ENV = Path(r"E:\workspace\orchestrator_skills\.env")

sys.path.insert(0, str(PROJECT_ROOT / "src"))
os.environ.setdefault("ORCHESTRATOR_SKILLS_ROOT", str(PROJECT_ROOT))
os.environ["LANGSMITH_TRACING"] = "false"

# Load credentials from orchestrator_skills/.env
for line in ORCHESTRATOR_SKILLS_ENV.read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, v = line.split("=", 1)
    if k in ("ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL", "ANTHROPIC_MODEL",
             "ANTHROPIC_DEFAULT_SONNET_MODEL", "ANTHROPIC_DEFAULT_HAIKU_MODEL",
             "LANGSMITH_API_KEY", "LANGSMITH_ENDPOINT", "LANGSMITH_PROJECT"):
        os.environ[k] = v

# Load TAVILY_API_KEY from project .env
for line in (PROJECT_ROOT / ".env").read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if line.startswith("TAVILY_API_KEY="):
        os.environ["TAVILY_API_KEY"] = line.split("=", 1)[1]
        print(f"[INFO] TAVILY_API_KEY loaded")
        break

# Enable LangSmith tracing
os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_CALLBACKS_BACKGROUND"] = "false"
os.environ.setdefault("LANGSMITH_PROJECT", "deepagents-video-maker-smoke")
print(f"[INFO] LangSmith tracing enabled, project={os.environ['LANGSMITH_PROJECT']}")

from langchain_anthropic import ChatAnthropic  # noqa: E402
from deepagents_video_maker.agent import create_video_maker_agent  # noqa: E402

model = ChatAnthropic(
    model=os.environ.get("ANTHROPIC_MODEL", "glm-5-turbo"),
    api_key=os.environ["ANTHROPIC_AUTH_TOKEN"],
    base_url=os.environ.get("ANTHROPIC_BASE_URL", "https://open.bigmodel.cn/api/anthropic"),
    timeout=120,
    max_retries=2,
)
agent = create_video_maker_agent(model, project_root=PROJECT_ROOT)
print("[OK] agent built:", type(agent).__name__)

prompt = "Create a 30-second video about AI technology trends 2025. Use websearch to gather up-to-date information."
print(f"[INFO] prompt: {prompt}")
print("[INFO] invoking agent (real LLM)...")

start = time.time()
try:
    result = agent.invoke(
        {"messages": [{"role": "user", "content": prompt}]},
        config={"configurable": {"thread_id": "smoke-real-001"}, "recursion_limit": 150},
    )
    elapsed = time.time() - start
    messages = result.get("messages", [])
    print(f"[OK] invoke done in {elapsed:.1f}s, messages={len(messages)}")
    if messages:
        last = messages[-1]
        content = last.content if hasattr(last, "content") else str(last)
        print(f"[OK] last msg type={getattr(last, 'type', type(last).__name__)}")
        print("[OK] response preview:")
        print(str(content)[:800])
except Exception as e:
    elapsed = time.time() - start
    print(f"[ERROR] after {elapsed:.1f}s: {type(e).__name__}: {e}")
    traceback.print_exc()
    sys.exit(1)
