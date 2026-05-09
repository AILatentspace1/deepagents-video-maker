#!/usr/bin/env pwsh
# Run the better-harness optimization loop for scriptwriter prompt.
# Usage: .\scripts\run-harness.ps1 [-MaxIterations 5] [-Config harness/video-maker-minimal.toml]

param(
    [int]$MaxIterations = 5,
    [string]$Config = "harness/video-maker-minimal.toml"
)

Set-Location $PSScriptRoot\..

# Load .env so Anthropic proxy vars (ANTHROPIC_AUTH_TOKEN, ANTHROPIC_BASE_URL) are available
# to both the eval subprocess and the optimizer agent.
$dotEnvPath = Join-Path $PSScriptRoot ".." ".env"
if (Test-Path $dotEnvPath) {
    Get-Content $dotEnvPath | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith('#') -and $line.Contains('=')) {
            $parts = $line.Split('=', 2)
            $key = $parts[0].Trim()
            $val = $parts[1].Trim().Trim('"').Trim("'")
            [System.Environment]::SetEnvironmentVariable($key, $val, 'Process')
        }
    }
    # Anthropic SDK reads ANTHROPIC_API_KEY; .env uses ANTHROPIC_AUTH_TOKEN — map it
    if ($env:ANTHROPIC_AUTH_TOKEN -and -not $env:ANTHROPIC_API_KEY) {
        $env:ANTHROPIC_API_KEY = $env:ANTHROPIC_AUTH_TOKEN
    }
    Write-Host "Loaded .env (ANTHROPIC_BASE_URL=$env:ANTHROPIC_BASE_URL)"
}

$env:PYTHONUTF8 = "1"
$timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$outputDir = "runs/$timestamp"

Write-Host "Starting harness: config=$Config  max-iterations=$MaxIterations  output=$outputDir"
uv run better-harness run $Config --output-dir $outputDir --max-iterations $MaxIterations
