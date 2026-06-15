"""Resource-path resolution shared by scaffold and detect (avoids an import cycle)."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path


def templates_dir() -> Path:
    """Path to the bundled templates directory (works for editable + wheel)."""
    return Path(str(files("specced"))) / "templates"
