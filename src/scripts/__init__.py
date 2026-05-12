"""Helper package for running repo scripts.

This module ensures `src/` is on `sys.path` so scripts can import `helpers`
when executed via `python -m scripts.<name>` from the repo root.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

