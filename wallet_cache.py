"""Cache for pre-computed static wallets to avoid re-enumeration on optimal search."""
import json
from pathlib import Path

from wallet_enumerations import enumerateStaticWallets

_CACHE_DIR = Path(__file__).resolve().parent / "wallet_cache"
_CACHED_KEY_COUNTS = range(1, 9)


def _cache_path(key_count: int) -> Path:
    return _CACHE_DIR / f"wallets_{key_count}.json"


def has_cached_wallets(key_count: int) -> bool:
    """Return True if a pre-computed wallet cache exists for this key_count (no enumeration)."""
    return key_count in _CACHED_KEY_COUNTS and _cache_path(key_count).exists()


def get_cached_static_wallets(
    key_count: int, deduplicate_by_architecture: bool = True
) -> list[list[int]]:
    """Return static wallets, loading from cache when possible.

    Uses cache only for key_count in 1..8 and deduplicate_by_architecture=True.
    Otherwise falls back to enumerateStaticWallets.
    """
    use_cache = (
        key_count in _CACHED_KEY_COUNTS and deduplicate_by_architecture
    )
    path = _cache_path(key_count)

    if use_cache and path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    wallets = enumerateStaticWallets(
        key_count, deduplicate_by_architecture=deduplicate_by_architecture
    )
    if use_cache:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(wallets, f)
    return wallets


def build_cache(key_counts: range | None = None) -> None:
    """Pre-populate the wallet cache for the given key counts."""
    if key_counts is None:
        key_counts = _CACHED_KEY_COUNTS
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    for k in key_counts:
        if k not in _CACHED_KEY_COUNTS:
            continue
        path = _cache_path(k)
        if path.exists():
            print(f"Cache exists for key_count={k}, skipping")
            continue
        print(f"Building cache for key_count={k}...")
        wallets = enumerateStaticWallets(k, deduplicate_by_architecture=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(wallets, f)
        print(f"Saved {len(wallets)} wallets to {path}")


if __name__ == "__main__":
    build_cache(key_counts=[5,6])
