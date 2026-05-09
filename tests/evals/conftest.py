"""Pytest configuration for better-harness eval suites.

Adds two CLI options consumed by the harness runner:

    --model              Inner-agent model string forwarded to eval fixtures.
    --evals-report-file  Path for machine-readable JSON eval report.

The JSON report (when requested) has the shape::

    {
      "timestamp": <float>,
      "model": "<model-string>",
      "total": <int>,
      "passed": <int>,
      "failed": <int>,
      "results": [
        {"node": "<nodeid>", "passed": <bool>, "outcome": "<str>", "duration": <float>},
        ...
      ]
    }
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--model",
        default="claude-sonnet-4-6",
        help="Inner-agent model string forwarded to eval fixtures.",
    )
    parser.addoption(
        "--evals-report-file",
        default=None,
        help="Path to write machine-readable JSON eval report (for better-harness).",
    )


@pytest.fixture(scope="session")
def eval_model(request: pytest.FixtureRequest) -> str:
    """Exposes --model CLI option to individual eval tests."""
    return request.config.getoption("--model")  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Result collection for the JSON report
# ---------------------------------------------------------------------------
# NOTE: _RESULTS is a module-level list mutated by the hookimpl below.
# Parallel test execution (e.g. pytest-xdist) is not supported by this
# reporter; run evals serially (the default).
_RESULTS: list[dict[str, Any]] = []


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo) -> Any:  # type: ignore[misc]
    # The `Any` return type is required here because pytest's hookwrapper
    # protocol uses generator-based yield mechanics that mypy cannot express
    # without importing private pytest internals.  This is the canonical
    # pattern recommended in the pytest docs for hookwrappers.
    outcome = yield
    rep = outcome.get_result()
    if call.when == "call":
        _RESULTS.append(
            {
                "node": item.nodeid,
                "passed": rep.passed,
                "outcome": rep.outcome,
                "duration": rep.duration,
            }
        )


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:  # noqa: ARG001
    report_path: str | None = session.config.getoption("--evals-report-file", default=None)
    if not report_path:
        return
    report: dict[str, Any] = {
        "timestamp": time.time(),
        "model": session.config.getoption("--model", default="claude-sonnet-4-6"),
        "total": len(_RESULTS),
        "passed": sum(1 for r in _RESULTS if r["passed"]),
        "failed": sum(1 for r in _RESULTS if not r["passed"]),
        "results": _RESULTS,
    }
    Path(report_path).write_text(json.dumps(report, indent=2), encoding="utf-8")
