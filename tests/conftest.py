"""Shared pytest fixtures for specced."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """An empty target repo directory."""
    return tmp_path
