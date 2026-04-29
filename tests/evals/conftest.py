"""Shared fixtures for eval tests."""

import pytest
from pathlib import Path


def pytest_addoption(parser):
    """Add command-line options for evals."""
    parser.addoption(
        "--model",
        action="store",
        default="claude-sonnet-4-6",
        help="Model to use for agent tests",
    )
    parser.addoption(
        "--evals-report-file",
        action="store",
        default=None,
        help="Path to write eval summary JSON",
    )


@pytest.fixture
def model(request):
    """Get model from command line."""
    return request.config.getoption("--model")


@pytest.fixture
def evals_report_file(request):
    """Get eval report path from command line."""
    return request.config.getoption("--evals-report-file")


@pytest.fixture
def sample_research_content():
    """Sample research report for scriptwriter tests."""
    return """# Research Report: AI Agent Evolution

## 1. Executive Summary
AI Agents are transforming how we work. From simple chatbots to autonomous systems, the technology has advanced rapidly in 2024-2025.

## 2. Data Points
- Global AI Agent investment: $150B in 2024
- Market leaders: Google (35%), Microsoft (25%), Amazon (10%), Others (30%)
- Growth rate: 300% year-over-year

## 3. Visual Strategy
visual_strategy: image_light
Recommend images for: hook scene, climax scene

## 4. Key Findings
AI Agents now handle complex multi-step tasks. They can plan, use tools, and learn from feedback.

## 5. Technical Architecture
Modern agents use LLM + planning + tool execution loops.

## 6. Style Spine
lut_style: tech_cool
tone: professional, confident

## 7. Narrative Flow
Hook → Evolution → Impact → Future → CTA

## 8. Additional Data
- Average task completion rate: 85%
- User satisfaction: 92%

## 9. Quotes
"AI Agents are not just responding anymore, they're acting." - Dr. Sarah Chen, MIT AI Lab
"""
