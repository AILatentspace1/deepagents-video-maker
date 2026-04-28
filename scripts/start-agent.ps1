#!/usr/bin/env pwsh
# Start the LangGraph dev server (backend agent)
Set-Location $PSScriptRoot\..\web-ui
uv run langgraph dev
