#!/usr/bin/env python3
"""Compatibility entrypoint for the Person 4 media replay script.

The canonical implementation lives with the FEAT-018 evidence fixtures.  This
root-level entrypoint keeps repository-level tests and CI commands stable.
"""

from __future__ import annotations

import runpy
from pathlib import Path


CANONICAL_SCRIPT = (
    Path(__file__).parents[1]
    / "features/FEAT-018-live-image-canvas-flow/scripts/replay_learning_media.py"
)


if __name__ == "__main__":
    runpy.run_path(str(CANONICAL_SCRIPT), run_name="__main__")
