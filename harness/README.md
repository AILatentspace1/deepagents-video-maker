# Better-Harness Integration (Minimal)

This directory contains the configuration for autonomous harness optimization using better-harness from the DeepAgents project.

## Quick Start

The minimal integration optimizes only the **Scriptwriter prompt** surface.

### Prerequisites

`pnpm harness:validate` and `pnpm harness:run` call `uv run better-harness ...`.
A fresh `uv sync` for this repository does **not** install `better-harness`; install
the external CLI into the active `uv` environment first:

```bash
# Install better-harness from deepagents repo
cd /tmp
git clone https://github.com/langchain-ai/deepagents.git
cd deepagents/examples/better-harness
uv sync
uv pip install -e .
```

On Windows/Codex worktrees, if the user-profile `pnpm` shim fails before repo
scripts run with `EPERM lstat C:\Users\Administrator` or
`C:\Users\ADMINI~1`, use Corepack so the repo `packageManager` pin is honored:

```powershell
corepack pnpm harness:validate
corepack pnpm harness:run
```

### Run Optimization

```bash
# Validate config
uv run better-harness validate harness/video-maker-minimal.toml

# Run baseline (1 iteration to test)
uv run better-harness run harness/video-maker-minimal.toml --output-dir runs/baseline --max-iterations 1

# Run full optimization loop (cross-platform via Node.js)
pnpm harness:run

# Or manually with an explicit output directory
uv run better-harness run harness/video-maker-minimal.toml --output-dir runs/my-run --max-iterations 5

# POSIX shell (bash/zsh/sh)
uv run better-harness run harness/video-maker-minimal.toml --output-dir runs/$(date +%Y%m%d-%H%M%S) --max-iterations 5

# PowerShell (Windows)
uv run better-harness run harness/video-maker-minimal.toml --output-dir "runs/$(Get-Date -Format 'yyyyMMdd-HHmmss')" --max-iterations 5
```

## Configuration

See `video-maker-minimal.toml` for the minimal surface configuration.

## Future Expansion

Once the minimal setup works, additional surfaces can be added:
- Producer prompt (SKILL.md)
- Researcher prompt
- LangChain tools
- Agent factory
- Milestone rules
- Ratify rules

## References

- [Better-Harness README](https://github.com/langchain-ai/deepagents/tree/main/examples/better-harness)
- [Blog: Improving Deep Agents with Harness Engineering](https://blog.langchain.com/improving-deep-agents-with-harness-engineering/)
