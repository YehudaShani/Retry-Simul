"""Helper package for running repo scripts.

This module ensures `src/` is on `sys.path` so scripts can import `helpers`
when executed via `python -m scripts.<name>` from the repo root.
"""

from __future__ import annotations

import sys
from pathlib import Path

for _src in Path(__file__).resolve().parents:
    if (_src / "helpers").is_dir() and (_src / "scripts").is_dir():
        if str(_src) not in sys.path:
            sys.path.insert(0, str(_src))
        break

