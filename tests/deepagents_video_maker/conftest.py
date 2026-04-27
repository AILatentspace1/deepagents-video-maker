from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest


@pytest.fixture
def tmp_path() -> Path:
    """Workspace-local tmp_path replacement for locked Windows temp dirs."""

    root = Path("test-results") / "deepagents-video-maker-tmp"
    root.mkdir(parents=True, exist_ok=True)
    path = root / uuid4().hex
    path.mkdir(parents=True, exist_ok=False)
    return path

