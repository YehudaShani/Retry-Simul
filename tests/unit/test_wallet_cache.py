"""Unit tests for wallet_cache module."""
import pytest
from retry_simul.wallet_cache import (
    get_cached_static_wallets,
    has_cached_wallets,
    supports_wallet_cache_key_count,
)
from retry_simul.wallet_enumerations import enumerateStaticWallets


def test_supports_wallet_cache_key_count_range():
    assert supports_wallet_cache_key_count(1) is True
    assert supports_wallet_cache_key_count(8) is True
    assert supports_wallet_cache_key_count(0) is False
    assert supports_wallet_cache_key_count(9) is False


def test_has_cached_wallets_requires_json_file(tmp_path, monkeypatch):
    """has_cached_wallets is False without on-disk JSON; supports_* is still True for 3..4."""
    from retry_simul import wallet_cache as wc

    monkeypatch.setattr(wc, "_CACHE_DIR", tmp_path)
    assert supports_wallet_cache_key_count(3) is True
    assert has_cached_wallets(3) is False


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
