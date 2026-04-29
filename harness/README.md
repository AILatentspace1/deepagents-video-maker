# Better-Harness Integration (Minimal)

This directory contains the configuration for autonomous harness optimization using better-harness from the DeepAgents project.

## Quick Start

The minimal integration optimizes only the **Scriptwriter prompt** surface.

### Prerequisites

```bash
# Install better-harness from deepagents repo
cd /tmp
git clone https://github.com/langchain-ai/deepagents.git
cd deepagents/examples/better-harness
uv sync
uv pip install -e .
```

### Run Optimization

```bash
# Validate config
uv run better-harness validate harness/video-maker-minimal.toml

# Run baseline (1 iteration to test)
uv run better-harness run harness/video-maker-minimal.toml --output-dir runs/baseline --max-iterations 1

# Run full optimization loop
uv run better-harness run harness/video-maker-minimal.toml --output-dir runs/$(date +%Y%m%d-%H%M%S) --max-iterations 5
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
