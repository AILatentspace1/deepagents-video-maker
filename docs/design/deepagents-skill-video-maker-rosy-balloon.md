# DeepAgents-Native Video-Maker 抽离为独立项目

## Context

当前 `e:/workspace/orchestrator_skills` 仓库混杂了多套 video-maker 实现：
- `src/agent/` + `src/agent-ui/`：DAG scheduler + Fastify/Vite Web app
- `.claude/skills/video-maker/`：Claude Code 会话内的 Skill 编排（Producer-Crew + 业务知识 md；其下的 pipeline-cli / Remotion template 本次不迁，后续独立项目化）
- `src/deepagents_video_maker/`（**目标方案**）：DeepAgents-native Producer，已实现 research/script milestone，复用 `.claude/skills/video-maker/` 的业务知识 md 作 progressive disclosure
- `deepagent-video-maker-ui/`：Next.js + LangGraph Dev UI

用户的目标：只保留 **deepagents（Python sidecar）+ skill（业务知识 md）+ Web UI** 这一条链路，抽到一个独立 repo，让后续演进不再被旁路代码干扰。`pipeline-cli` 和 `remotion-template` 后续作为独立 project / 外部依赖处理，本次不迁入新仓库。

本次只做"剥离打包"，不补 assets/assembly milestone，也不重构现有代码。

---

## 用户已确认决策

1. **位置**：同级新目录 `e:/workspace/deepagents-video-maker`，独立 git repo
2. **范围**：3 大块全迁（Python 编排层 + Skill 业务知识 md + Next.js Web UI）；不迁 `pipeline-cli` / `remotion-template`
3. **完成度**：只迁现状，研究/脚本 milestone 跑通即可，assets/assembly 留待后续
4. **Skill 复用**：直接拷贝为副本，与原仓库独立演进
5. **迁移基准**：必须包含 2026-04-27 最新 pipeline fixes（`goal.yaml` fallback、YAML Windows path escaping、LangSmith smoke tracing、`vm_ratify_script` fallback、对应 tests）
6. **命令约定**：Python 命令统一使用 `uv run ...`；不使用裸 `pytest` / `python`
7. **旧 skill 附属目录**：`assets/`、`reflexion/` 与 `references/`、`scripts/`、`templates/` 一起 copy
8. **路径回归**：必须加 grep/测试，确保代码与配置不再引用 `.claude/skills/video-maker`
9. **渲染工具链边界**：`pipeline-cli` 与 `remotion-template` 不进入新仓库；后续单独建 repo 或以 package/dependency 方式接入

---

## Task 0: Freeze source snapshot（必须先做）

当前 `orchestrator_skills` worktree 包含本迁移必须带走的最新修复。执行迁移前先二选一：

1. **推荐**：提交当前 deepagents-video-maker 相关 fixes，再从该 commit 迁移。
2. **可接受**：明确从当前 dirty working tree 迁移，并在新仓库验证同等行为。

必须包含这些文件中的最新变更：

- `src/deepagents_video_maker/langchain_tools.py`
  - `vm_build_researcher_task` / `vm_ratify_research` / `vm_build_scriptwriter_task` / `vm_ratify_script` 支持无 `topic/source/...` 时从 `output_dir/goal.yaml` fallback。
- `src/deepagents_video_maker/state_store.py`
  - `load_goal_yaml()`
  - `_scalar()` 正确 escape Windows backslash，保证 PyYAML 可 parse。
- `scripts/smoke_skills_research_script.py`
  - 加载 `.env`
  - `LANGSMITH_*` / `LANGCHAIN_*` 覆盖当前进程环境
  - `@traceable(name="skills_research_script_smoke")`
- `tests/deepagents_video_maker/test_langchain_tools.py`
  - 覆盖 build/ratify tools 从 `goal.yaml` fallback。

迁移前在原仓库记录：

```powershell
git rev-parse HEAD
git status --short
uv run pytest tests/deepagents_video_maker -q
```

当前已知基准：`uv run pytest tests/deepagents_video_maker -q` 应为 `63 passed`（或更多，但不能有失败）。

## 新仓库目录结构

```
deepagents-video-maker/
├── pyproject.toml
├── package.json                # root scripts（主要代理 web-ui + Python 命令）
├── pnpm-workspace.yaml         # 仅包含 web-ui；预留未来外部包接入
├── .gitignore
├── .env.example
├── README.md
├── AGENTS.md                   # 精简版（~30 行），描述 Quick Start + 架构骨架
├── CLAUDE.md                   # 精简版，给 Claude Code 用
├── src/
│   └── deepagents_video_maker/ # Python 包，import path 不变
│       ├── __init__.py
│       ├── agent.py            # 主工厂 create_video_maker_agent
│       ├── prompts/            # producer.md + subagents/*.md
│       └── …                   # models, flows, tools, ratify, state_store…
├── tests/
│   └── deepagents_video_maker/ # test_*.py + conftest.py（以迁移基准为准）
├── scripts/
│   ├── deepagents_video_maker.py        # 改写成 thin runner（见下）
│   └── smoke_skills_research_script.py  # deterministic typed-tool smoke + LangSmith trace
├── .deepagents/
│   └── skills/
│       ├── video-researcher/SKILL.md       # progressive disclosure wrapper
│       └── video-scriptwriter/SKILL.md
├── skills/
│   └── video-maker/            # 原 .claude/skills/video-maker/ 业务知识（去掉 .claude/ 前缀）
│       ├── SKILL.md
│       ├── milestones/         # _pipeline.yaml + research.md + script.md (+ assets.md/assembly.md 留作未来)
│       ├── agents/             # researcher.md, scriptwriter.md, evaluator.md, reviewer.md, scene-batch-generator.md
│       └── ratify/             # research-rules.md, script-rules.md (+ 未来 assets/assembly)
└── web-ui/                     # workspace pkg "deepagent-video-maker-ui"
    ├── package.json
    ├── langgraph.json          # graphs.video-maker = ./agent/agent.py:agent
    ├── agent/agent.py          # LangGraph 胶水
    └── src/                    # Next.js app
```

**为什么这样分**：
- `.deepagents/skills/` 保留点前缀，因为 `agent.py:_SUBAGENT_SKILL_DIRS` 里硬编码这条相对路径，迁移后无需改代码
- `skills/video-maker/` 去掉 `.claude/` 前缀，新仓库不再是 Claude Code 项目根，不需要那层命名空间
- 本次只保留一个 pnpm workspace package：`web-ui/`。原仓库 `.claude/skills/video-maker/` 下的 `video-pipeline-cli/` 与 `remotion-template/` 不拷入新仓库；未来单独项目化后再通过 package/dependency/API 接入。

---

## 文件迁移清单

约定：`copy` = 字节级拷贝；`rewrite` = 拷贝后修补；`skip` = 不迁。

### Python 编排层
| 源 | 目标 | 操作 |
|---|---|---|
| `src/deepagents_video_maker/**`（含 `prompts/`） | `src/deepagents_video_maker/**` | rewrite（仅 `prompts/producer.md` 第 9 行 `.claude/skills/video-maker/` → `skills/video-maker/`） |
| `tests/deepagents_video_maker/**` | `tests/deepagents_video_maker/**` | rewrite（`test_skill_files.py` 见 §路径调整） |
| `.deepagents/skills/video-researcher/SKILL.md` | `.deepagents/skills/video-researcher/SKILL.md` | rewrite（`/.claude/skills/video-maker/` → `/skills/video-maker/`） |
| `.deepagents/skills/video-scriptwriter/SKILL.md` | `.deepagents/skills/video-scriptwriter/SKILL.md` | rewrite（同上） |
| `scripts/deepagents_video_maker.py` | `scripts/deepagents_video_maker.py` | rewrite（去掉 path-coupled 死路径，见 §scripts 处理） |
| `scripts/smoke_skills_research_script.py` | `scripts/smoke_skills_research_script.py` | copy（必须包含 LangSmith traceable 最新版本） |
| `scripts/_smoke_verbose.py`、`_smoke_verbose2.py`、`_check_run.py`、`_thread_state.py`、`smoke_native.py`、`smoke_final.py` | — | skip（实验残留） |
| `pyproject.toml` | `pyproject.toml` | rewrite（rename project + 补 `langchain-openai`） |
| `.env.example` | `.env.example` | rewrite（只保留新仓库需要的 LangSmith/model/provider/native env，见 §`.env.example`） |

### Skill 业务知识（活跃部分）
| 源 | 目标 | 操作 |
|---|---|---|
| `.claude/skills/video-maker/SKILL.md` | `skills/video-maker/SKILL.md` | rewrite（grep `.claude/skills` 字面量并替换为 `skills/`） |
| `.claude/skills/video-maker/milestones/{_pipeline.yaml, research.md, script.md, assets.md, assembly.md}` | `skills/video-maker/milestones/…` | rewrite（同样 grep + 替换） |
| `.claude/skills/video-maker/agents/{researcher, scriptwriter, evaluator, reviewer, scene-batch-generator}.md` | `skills/video-maker/agents/…` | rewrite |
| `.claude/skills/video-maker/agents/{editor, scene-patch-generator}.md` | — | skip（已废弃） |
| `.claude/skills/video-maker/ratify/{research-rules, script-rules, assets-rules, assembly-rules}.md` | `skills/video-maker/ratify/…` | copy |
| `.claude/skills/video-maker/{assets, reflexion, references, scripts, templates}/**`（如有） | `skills/video-maker/…` | copy |
| `.claude/skills/video-maker/{video-pipeline-cli, remotion-template}/**` | — | skip（后续独立 project，不进入本 repo） |

### 渲染工具链（本次不迁）
| 源 | 目标 | 操作 |
|---|---|---|
| `.claude/skills/video-maker/video-pipeline-cli/**` | — | skip（未来独立 repo） |
| `.claude/skills/video-maker/remotion-template/**` | — | skip（未来独立 repo） |

### Next.js Web UI
| 源 | 目标 | 操作 |
|---|---|---|
| `deepagent-video-maker-ui/{package.json, next.config.ts, src/, public/, tailwind.config.*, postcss.config.*, tsconfig.json, eslint.config.*, agent/agent.py, langgraph.json}` | `web-ui/…` | rewrite（`agent/agent.py` 见 §路径调整；`package.json` 改 packageManager 为 pnpm） |
| `deepagent-video-maker-ui/{node_modules, .next, .turbo, out, yarn.lock}` | — | skip |

### 顶层文档
| 源 | 目标 | 操作 |
|---|---|---|
| 现有 `AGENTS.md`、`CLAUDE.md`、`README.md` | — | skip；写新版（顶层 < 80 行，描述新仓库定位） |
| `docs/plans/2026-04-25-deepagents-*.md`、`2026-04-26-deepagents-skills-research-script.md`、`research.md` | `docs/design/` | copy（保留设计源头供未来对照） |

### 不迁的范围（确认）
`src/agent/`、`src/agent-ui/`、`specs/`、`tasks/`、`output/`、`logs/`、`playwright*`、所有 `.claude/{agents,commands,hooks,plugins,settings*}` 配置、`.gstack/`、`.baoyu-skills/`、`.superpowers/`、`videomaker-playground.html`、`debug_sign_in.png`、`SPEC_RESEARCH_REPORT_*.md`、`TODOS.md`、`output.mp3`。

---

## 路径与代码调整

### 1. `tests/deepagents_video_maker/test_skill_files.py`
- 第 24 行 `if ".claude/skills" in line:` 改为 `if "skills/video-maker" in line:`
- 第 25 行的断言信息一并更新（`/.claude/skills` 字面量 → `/skills/video-maker`）
- 追加断言：wrapper 中任何业务知识引用必须使用 `/skills/video-maker/...`
- 追加断言：代码与配置中不得出现 `.claude/skills/video-maker`（`docs/design/` 历史文档豁免）

### 2. `src/deepagents_video_maker/prompts/producer.md`
- 第 9 行 `不读取 .claude/skills/video-maker/ 业务 prompt` → `不读取 skills/video-maker/ 业务 prompt`

### 3. `.deepagents/skills/video-{researcher,scriptwriter}/SKILL.md`
- 文件内三处 `/.claude/skills/video-maker/` 字面量 → `/skills/video-maker/`

### 4. `scripts/deepagents_video_maker.py`（path-coupling 修复）
当前脚本引用两条**不存在的路径**：
- `SKILL_PATH = .deepagents/skills/video-maker/SKILL.md`（不存在）
- `AGENTS_DIR = .deepagents/agents`（不存在）

并且 `check_files()` 还写死了 `.claude/skills/video-maker/SKILL.md` 与 `milestones/_pipeline.yaml`。

**改写策略**（最小修补，不重构）：
- 删除 `SKILL_PATH`、`AGENTS_DIR`、`SUBAGENT_NAMES`、`load_system_prompt()`、`load_subagents()`、`check_files()` 这一套早期实现
- `build_agent()` 内部改为调用 `from deepagents_video_maker.agent import create_video_maker_agent` + `create_video_maker_agent(resolve_model(model), project_root=PROJECT_ROOT, interrupt=interrupt, checkpointer=None)`
- 默认不要使用 `checkpointer=True` 或 `MemorySaver()`；已实测 root graph 使用 `checkpointer=True` 会报 `RuntimeError: checkpointer=True cannot be used for root graphs.`
- 保留：`load_env_files`, `resolve_model`, `to_virtual_path`, `patch_deepagents_path_validation`, `execute_pwsh`, `project_glob`, `main()` CLI 入口
- `--check` flag 改为简单读 `src/deepagents_video_maker/__init__.py` 是否能 import + `skills/video-maker/SKILL.md` 是否存在
- `main()` 中真实 invoke 使用：
  ```python
  agent = build_agent(args.model, interrupt=args.interrupt, checkpointer=False)
  result = agent.invoke(
      {"messages": [{"role": "user", "content": " ".join(args.prompt)}]},
      config={"configurable": {"thread_id": args.thread_id}, "recursion_limit": 100},
  )
  ```

### 5. `web-ui/agent/agent.py`
- 第 18 行 `PROJECT_ROOT = Path(__file__).resolve().parents[2]` → `parents[2]` 在新布局下指向 repo 根（`web-ui/agent/agent.py` 上两级），仍然正确
- 第 25 行 `from scripts.deepagents_video_maker import build_agent, load_env_files, resolve_model` 在新布局下仍可解析，因为 `parents[2]` 是 repo 根，`sys.path` 已加 root + `src/`
- 第 33 行 `DEEPAGENTS_VIDEO_MAKER_NATIVE` 默认改为 `"true"`（`os.environ.get(..., "true")`），让新仓库默认走 native 工厂；legacy `build_agent` 分支保留作为 fallback 调试用

### 6. `web-ui/package.json`
- `packageManager: "yarn@1.22.22"` → `"pnpm@9.x"`（统一全仓库 pnpm，遵循全局 CLAUDE.md 约定）
- `agent:dev` 不再依赖隔离 `uvx` 默认环境；改成 root workspace 脚本统一用 `uv run` 启动 LangGraph dev server，避免新仓库 Python 包和 deps 不在 `uvx` 环境中。
- 如果保留 `uvx` fallback，必须显式加 `--with-editable .. --with langchain-anthropic --with langchain-openai --with PyYAML`。

### 7. `langchain_tools.py` 的 env var
- 当前用 `ORCHESTRATOR_SKILLS_ROOT`，在 `agent.py:65` 与 `web-ui/agent/agent.py:31` 都设置过。**保留原名**避免触发 14 个测试；新仓库注释里说明这是历史命名，未来可重命名

### 8. `tests/deepagents_video_maker/conftest.py`
- fixture 用 `Path("test-results") / "deepagents-video-maker-tmp"`，相对 CWD 工作，无需改

### 9. `.env.example`
不要字节级 copy 混合仓库的 `.env.example`。写新仓库最小版本：

```dotenv
# LangSmith tracing
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_PROJECT=deepagents-video-maker
LANGCHAIN_CALLBACKS_BACKGROUND=false

# Model provider
DEEPAGENTS_MODEL=anthropic:claude-sonnet-4-5-20250929
ANTHROPIC_API_KEY=

# Optional DeepSeek OpenAI-compatible route
DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_THINKING=disabled

# Web UI / LangGraph
DEEPAGENTS_VIDEO_MAKER_NATIVE=true
ORCHESTRATOR_SKILLS_ROOT=
```

---

## 配置文件草案

### `pyproject.toml`
```toml
[project]
name = "deepagents-video-maker"
version = "0.1.0"
description = "DeepAgents-native video-maker orchestrator"
requires-python = ">=3.11"
dependencies = [
  "deepagents>=0.5.3",
  "langchain>=0.3.0",
  "langchain-core>=0.3.0",
  "langchain-anthropic>=0.3.0",
  "langchain-openai>=0.3.0",   # 新增：DeepSeek OpenAI-兼容路径
  "PyYAML>=6.0",
]

[dependency-groups]
dev = ["pytest>=8.0.0"]

[tool.pytest.ini_options]
testpaths = ["tests/deepagents_video_maker"]
pythonpath = ["src"]
addopts = "-q -p no:cacheprovider"
```

### `package.json`（root）
```json
{
  "name": "deepagents-video-maker",
  "private": true,
  "packageManager": "pnpm@9",
  "scripts": {
    "ui:dev": "pnpm --filter deepagent-video-maker-ui dev",
    "agent:dev": "uv run langgraph dev --config web-ui/langgraph.json",
    "test:py": "uv run pytest tests/deepagents_video_maker"
  }
}
```

### `pnpm-workspace.yaml`
```yaml
packages:
  - web-ui
```

### `.gitignore`（关键项）
```
.venv/
__pycache__/
*.egg-info/
node_modules/
.next/
.turbo/
out/
dist/
output/
test-results/
.tmp/
.env
.env.local
.DS_Store
```

### `README.md`（骨架）
- 一句话定位：**DeepAgents-native video-maker orchestrator，当前可运行链路为 research → script；assets/assembly 后续通过独立渲染工具链接入**
- Quick Start：`uv sync` → `pnpm install` → `pnpm test:py` → `pnpm agent:dev`
- 链接到 `docs/design/` 设计文档

---

## 验证 Checklist

新仓库 cherry-pick 完成后逐项确认：

1. `uv sync` 依赖解析成功
2. `pnpm install` 在 root 成功，`pnpm -r ls` 列出 1 个 workspace 包：`deepagent-video-maker-ui`
3. `uv run pytest tests/deepagents_video_maker -q` 全绿（当前源仓库基准为 `63 passed`）
4. `uv run python scripts/deepagents_video_maker.py --check` 输出 OK，无 SystemExit
5. `uv run python scripts/smoke_skills_research_script.py` 跑通（deterministic typed-tool smoke，并写 LangSmith trace `skills_research_script_smoke`）
6. `uv run langgraph dev --config web-ui/langgraph.json` 启动 LangGraph dev server（langgraph.json 解析 `./agent/agent.py:agent` 成功，default `DEEPAGENTS_VIDEO_MAKER_NATIVE=true` 走 native 工厂）
7. 全仓 grep `\.claude/skills` 在代码与配置中零匹配（仅可能在 `docs/design/` 历史文档里出现）
8. 全仓确认不存在迁入的渲染工具链目录：
    ```powershell
    Test-Path pipeline-cli
    Test-Path remotion-template
    Test-Path skills/video-maker/video-pipeline-cli
    Test-Path skills/video-maker/remotion-template
    ```
    Expected: 全部为 `False`。
9. 跑一次真实 DeepAgents invoke（非 deterministic smoke）：
    ```powershell
    uv run python scripts/deepagents_video_maker.py --thread-id migration-real-smoke "请生成介绍 video-maker skill 的视频。source=local-file local_file=/docs/design/ARCHITECTURE-VIDEO-MAKER.md duration=1-3min style=professional"
    ```
    Expected: research + script milestones completed；LangSmith project 中出现 `video-maker-producer` success trace。

---

## 关键文件清单（实施时直接对照）

需要修改路径或代码的文件：
- `e:/workspace/orchestrator_skills/scripts/deepagents_video_maker.py`（删 SKILL_PATH/AGENTS_DIR，build_agent 改调 create_video_maker_agent）
- `e:/workspace/orchestrator_skills/src/deepagents_video_maker/prompts/producer.md`（line 9 字面量替换）
- `e:/workspace/orchestrator_skills/.deepagents/skills/video-researcher/SKILL.md`（3 处字面量替换）
- `e:/workspace/orchestrator_skills/.deepagents/skills/video-scriptwriter/SKILL.md`（同上）
- `e:/workspace/orchestrator_skills/tests/deepagents_video_maker/test_skill_files.py`（line 24-25 路径子串）
- `e:/workspace/orchestrator_skills/deepagent-video-maker-ui/agent/agent.py`（NATIVE 默认 true）
- `e:/workspace/orchestrator_skills/deepagent-video-maker-ui/package.json`（packageManager → pnpm）
- `e:/workspace/orchestrator_skills/.claude/skills/video-maker/{SKILL.md, milestones/*.md, agents/*.md}`（grep `.claude/skills` 字面量做批量替换）
- `e:/workspace/orchestrator_skills/src/deepagents_video_maker/langchain_tools.py`（必须包含最新 `goal.yaml` fallback）
- `e:/workspace/orchestrator_skills/src/deepagents_video_maker/state_store.py`（必须包含 `load_goal_yaml` 和 Windows path escaping）
- `e:/workspace/orchestrator_skills/scripts/smoke_skills_research_script.py`（必须包含 LangSmith traceable）

需要新建的文件：
- `e:/workspace/deepagents-video-maker/{pyproject.toml, package.json, pnpm-workspace.yaml, .gitignore, .env.example, README.md, AGENTS.md, CLAUDE.md}`

---

## 风险与开放问题

1. **`langchain-openai` 是必需依赖**：DeepSeek 路径在 `scripts/deepagents_video_maker.py:resolve_model` 用 `from langchain_openai import ChatOpenAI`。必须加进 dependencies，否则 `.env` 里 `DEEPAGENTS_MODEL=deepseek:*` 时会启动失败。

2. **新仓库是不是要再写一份"会被 Claude Code 看到"的 `.claude/skills/video-maker/`**：当前方案是只放到 `skills/video-maker/`，作为 deepagents subagent skill 的目标。如果你也想在新仓库里继续用 Claude Code 会话直接跑老 Skill 编排（即不通过 deepagents 入口），就要再做一份 `.claude/skills/video-maker/` 软拷或符号链接。**默认假设：不需要**——deepagents 入口是新仓库唯一的执行路径。

3. **`docs/design/` 要带过去**：copy 设计源头，至少包含 `2026-04-25-deepagents-native-video-maker-implementation.md`、`2026-04-26-deepagents-skills-research-script.md`、`research.md`；其他重型历史文档可按需补充。

4. **`web-ui/package.json` 切到 pnpm 后，lockfile 重生成**：原 yarn.lock 不带过去，`pnpm install` 时会重新解析 Web UI 依赖，可能出现 minor 版本漂移（特别是 React/Next/Tailwind 的 transitive deps）。建议迁移后立即跑 `pnpm --filter deepagent-video-maker-ui dev` 验证渲染正常。

5. **后续 milestone（assets/assembly）的预留**：`skills/video-maker/{milestones,ratify}` 已经包含 assets/assembly 的 md（业务侧已就绪），但 Python 这边 `langchain_tools.py` 还没有 `vm_start_assets`、`vm_ratify_assets`、`vm_start_assembly` 等 typed tools；并且渲染执行依赖未来独立的 `pipeline-cli` / `remotion-template` 项目。后续 milestone 是另一个独立 plan，本次不动。

6. **渲染工具链外部化接口未定义**：本计划只确保 research/script pipeline 可运行；未来接入 assets/assembly 时，需要新 plan 明确 `pipeline-cli` 和 `remotion-template` 以 npm package、git submodule、local path dependency、CLI binary 还是 service API 形式接入。
