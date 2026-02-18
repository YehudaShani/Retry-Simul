"""Unit tests for wallet_cache module."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pytest
from wallet_cache import get_cached_static_wallets
from wallet_enumerations import enumerateStaticWallets


class TestGetCachedStaticWallets:
    def test_matches_enumerate_for_cached_key_count(self):
        """Cached result matches enumerateStaticWallets for key_count in 1..8."""
        key_count = 5
        enumerated = enumerateStaticWallets(
            key_count, deduplicate_by_architecture=True
        )
        cached = get_cached_static_wallets(
            key_count, deduplicate_by_architecture=True
        )
        assert cached == enumerated
        assert isinstance(cached, list)
        assert all(isinstance(w, list) for w in cached)
        assert all(isinstance(m, int) for w in cached for m in w)


    def test_fallback_for_deduplicate_false(self):
        """When deduplicate_by_architecture=False, result matches enumeration."""
        key_count = 3
        enumerated = enumerateStaticWallets(
            key_count, deduplicate_by_architecture=False
        )
        cached = get_cached_static_wallets(
            key_count, deduplicate_by_architecture=False
        )
        assert cached == enumerated
