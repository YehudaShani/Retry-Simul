"""Cache for pre-computed static wallets to avoid re-enumeration on optimal search."""

import json
import itertools
import math
import sys
from pathlib import Path
from typing import Iterable

if __package__ in (None, ""):
    # Allow running this file directly (e.g. `python src/retry_simul/wallet_cache.py`).
    # In that case, ensure `src/` is on sys.path so `retry_simul.*` absolute imports resolve.
    _SRC = Path(__file__).resolve().parents[1]
    if str(_SRC) not in sys.path:
        sys.path.insert(0, str(_SRC))
    from retry_simul.wallet_enumerations import enumerateStaticWallets
else:
    from .wallet_enumerations import enumerateStaticWallets

_CACHE_DIR = Path(__file__).resolve().parent / "data" / "wallet_cache"
_CACHED_KEY_COUNTS = range(1, 9)

_PERMUTATION_TABLES: dict[int, list[list[int]]] = {}

# Canonical-only generation cache (per n, per process).
_CANONICAL_WALLETS: dict[int, list[list[int]]] = {}


def _permutation_tables(key_count: int) -> list[list[int]]:
    """Return cached permutation lookup tables for this key_count.

    tables[p][mask] = permuted_mask under permutation p, where mask in [0..2^n-1].
    """
    if key_count <= 0:
        raise ValueError("key_count must be positive")
    if key_count in _PERMUTATION_TABLES:
        return _PERMUTATION_TABLES[key_count]

    masks = list(range(1 << key_count))
    indices = tuple(range(key_count))  # 0-based positions
    tables: list[list[int]] = []
    for perm in itertools.permutations(indices):
        table = [0] * len(masks)
        for mask in masks:
            out = 0
            mm = mask
            bit = 0
            while mm:
                if mm & 1:
                    out |= 1 << perm[bit]
                mm >>= 1
                bit += 1
            table[mask] = out
        tables.append(table)

    _PERMUTATION_TABLES[key_count] = tables
    return tables


def _canonicalize_wallet_fast(wallet: list[int], tables: list[list[int]]) -> tuple[int, ...]:
    """Canonicalize wallet up to key renaming using table lookups."""
    if not wallet:
        return tuple()
    best: tuple[int, ...] | None = None
    for table in tables:
        transformed = tuple(sorted(table[m] for m in wallet))
        if best is None or transformed < best:
            best = transformed
    return best or tuple()


def _deduplicate_wallets_by_architecture_fast(
    wallets: list[list[int]], key_count: int
) -> list[list[int]]:
    tables = _permutation_tables(key_count)
    seen: set[tuple[int, ...]] = set()
    unique: list[list[int]] = []
    for w in wallets:
        canon = _canonicalize_wallet_fast(w, tables)
        if canon not in seen:
            seen.add(canon)
            unique.append(w)
    return unique


def _is_covered(key_combination: int, wallet: list[int]) -> bool:
    """Is any wallet term covered by key_combination? (Same as wallet_enumerations.isCovered.)"""
    for wallet_combination in wallet:
        if (wallet_combination & key_combination) == wallet_combination:
            return True
    return False


def _enumerate_static_wallets_canonical(key_count: int) -> list[list[int]]:
    """Generate only canonical architecture representatives for key_count<=6.

    This uses canonical-prefix pruning: after adding a term, only recurse if the
    partial wallet equals its own canonical form under key renaming.
    """
    if key_count <= 0:
        raise ValueError("key_count must be positive")
    if key_count > 6:
        raise ValueError("Canonical-only generator is supported for key_count<=6")
    if key_count in _CANONICAL_WALLETS:
        return _CANONICAL_WALLETS[key_count]

    tables = _permutation_tables(key_count)
    max_mask = (1 << key_count) - 1

    out: list[list[int]] = []

    def rec(base_wallet: list[int], prev_combi: int) -> None:
        for curr_combi in range(prev_combi + 1, max_mask + 1):
            if _is_covered(curr_combi, base_wallet):
                continue
            curr_wallet = base_wallet + [curr_combi]

            # Canonical-prefix prune.
            w_norm = tuple(sorted(curr_wallet))
            canon = _canonicalize_wallet_fast(curr_wallet, tables)
            if w_norm != canon:
                continue

            out.append(list(w_norm))
            rec(curr_wallet, curr_combi)

    rec([], 0)
    _CANONICAL_WALLETS[key_count] = out
    return out


def _cache_path(key_count: int) -> Path:
    return _CACHE_DIR / f"wallets_{key_count}.json"


def has_cached_wallets(key_count: int) -> bool:
    """Return True if a pre-computed JSON wallet list exists on disk (no enumeration to load)."""
    return key_count in _CACHED_KEY_COUNTS and _cache_path(key_count).exists()


def supports_wallet_cache_key_count(key_count: int) -> bool:
    """Return True if ``get_cached_static_wallets`` uses the cache layer for this key_count (1..8).

    Missing JSON still enumerates on first use; callers that only need optimal static wallets
    should use this instead of :func:`has_cached_wallets`, which requires the file to exist.
    """
    return key_count in _CACHED_KEY_COUNTS


def get_cached_static_wallets(
    key_count: int, deduplicate_by_architecture: bool = True
) -> list[list[int]]:
    """Return static wallets, loading from cache when possible.

    Uses cache only for key_count in 1..8 and deduplicate_by_architecture=True.
    Otherwise falls back to enumerateStaticWallets.
    """
    use_cache = key_count in _CACHED_KEY_COUNTS and deduplicate_by_architecture
    path = _cache_path(key_count)

    if use_cache and path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    if deduplicate_by_architecture and key_count <= 6:
        # Canonical-only generation avoids enumerating all labeled wallets.
        wallets = _enumerate_static_wallets_canonical(key_count)
    else:
        # Fallback: enumerate labeled wallets then deduplicate (fast canonical signature).
        wallets = enumerateStaticWallets(key_count, deduplicate_by_architecture=False)
        if deduplicate_by_architecture:
            wallets = _deduplicate_wallets_by_architecture_fast(wallets, key_count)
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
            print(f"Cache exists for key_count={k}, skipping", flush=True)
            continue
        print(f"Building cache for key_count={k}...", flush=True)
        if k <= 6:
            wallets = _enumerate_static_wallets_canonical(k)
        else:
            wallets = enumerateStaticWallets(k, deduplicate_by_architecture=False)
            wallets = _deduplicate_wallets_by_architecture_fast(wallets, k)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(wallets, f)
        print(f"Saved {len(wallets)} wallets to {path}", flush=True)


def _parse_key_counts(raw: str) -> list[int]:
    # Accept "6" or "1,2,3" or "1-4".
    raw = raw.strip()
    if "-" in raw and "," not in raw:
        lo_s, hi_s = raw.split("-", 1)
        lo, hi = int(lo_s), int(hi_s)
        if lo > hi:
            lo, hi = hi, lo
        return list(range(lo, hi + 1))
    return [int(x.strip()) for x in raw.split(",") if x.strip()]


def main(argv: list[str] | None = None) -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Build on-disk cache of static wallets.")
    parser.add_argument(
        "--key-counts",
        default="6",
        help="Key counts to cache: e.g. '6', '1,2,3', or '1-4' (default: 6)",
    )
    args = parser.parse_args(argv)

    key_counts: Iterable[int] = _parse_key_counts(args.key_counts)
    build_cache(key_counts=key_counts)


if __name__ == "__main__":
    main()

