"""Shared fixtures for unit and integration tests."""
import sys
from pathlib import Path

# Ensure project root is on path when running tests
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import pytest
from consts import SAFE, LOST, LEAKED, STOLEN


@pytest.fixture
def key_count():
    return 3


@pytest.fixture
def uniform_probs():
    """Equal probabilities summing to 1."""
    return {SAFE: 0.25, LOST: 0.25, LEAKED: 0.25, STOLEN: 0.25}


@pytest.fixture
def safe_heavy_probs():
    """SAFE-heavy scenario."""
    return {SAFE: 0.5, LOST: 0.2, LEAKED: 0.2, STOLEN: 0.1}
