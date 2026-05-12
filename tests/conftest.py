"""Shared fixtures for unit and integration tests."""
import pytest
from helpers.consts import SAFE, LOST, LEAKED, STOLEN


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
