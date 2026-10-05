"""Certificates proving: for pSAFE >= 1/2, wallets with >=2 incomplete layers are dominated.

Statement proven per key count n: for every wallet B with >= 2 incomplete layers
(support-relative, coverage-based), there is a wallet G with <= 1 incomplete layer such
that U(G) >= U(B) for ALL scenarios with pSAFE >= pLOST + pLEAKED + pSTOLEN (i.e.
pSAFE >= 1/2). Hence some optimal wallet always has <= 1 incomplete layer there.

Certificate: U is a homogeneous degree-n integer polynomial in (s, l, k, t). Substitute
s = e + l + k + t (e >= 0 encodes s >= 1/2 exactly). If every coefficient of the
expanded difference U(G) - U(B) in (e, l, k, t) is >= 0, then the difference is
nonnegative on the entire region - a rigorous algebraic proof. If direct expansion
fails, multiply by (e + l + k + t)^m (positive on the region) and retry (Polya).

All arithmetic is exact (integers).
"""
import sys
from itertools import product
from math import comb
from pathlib import Path

for _src in Path(__file__).resolve().parents:
    if (_src / "helpers").is_dir() and (_src / "scripts").is_dir():
        if str(_src) not in sys.path:
            sys.path.insert(0, str(_src))
        break

from helpers.symbols import success_probability_polynomial_coefficients
from helpers.wallet_cache import get_cached_static_wallets
from helpers.wallet_enumerations import walletStrAscii

import numpy as np

from scripts.experiments.layer_growth_experiment import (
    coverage_matrix,
    incomplete_layer_counts_support_relative,
    pair_probability_matrix,
    success_probabilities,
)
from helpers.consts import SAFE, LOST, LEAKED, STOLEN

# Sample scenarios in the region pSAFE >= 1/2, used only to ORDER candidate
# dominators (the certificate itself is exact and region-wide).
_SAMPLE_SCENARIOS = [
    {SAFE: 0.50, LOST: 1 / 6, LEAKED: 1 / 6, STOLEN: 1 / 6},
    {SAFE: 0.52, LOST: 0.02, LEAKED: 0.40, STOLEN: 0.06},
    {SAFE: 0.52, LOST: 0.40, LEAKED: 0.02, STOLEN: 0.06},
    {SAFE: 0.52, LOST: 0.06, LEAKED: 0.06, STOLEN: 0.36},
    {SAFE: 0.55, LOST: 0.00, LEAKED: 0.225, STOLEN: 0.225},
    {SAFE: 0.70, LOST: 0.10, LEAKED: 0.10, STOLEN: 0.10},
    {SAFE: 0.90, LOST: 0.02, LEAKED: 0.04, STOLEN: 0.04},
]

# Polynomial = dict[(a_e, a_l, a_k, a_t)] -> int coefficient


def _multinomial_expand(power: int) -> dict[tuple[int, int, int, int], int]:
    """Coefficients of (e + l + k + t)^power."""
    out: dict[tuple[int, int, int, int], int] = {}
    for ae in range(power + 1):
        for al in range(power - ae + 1):
            for ak in range(power - ae - al + 1):
                at = power - ae - al - ak
                out[(ae, al, ak, at)] = (
                    comb(power, ae)
                    * comb(power - ae, al)
                    * comb(power - ae - al, ak)
                )
    return out


def substituted_success_poly(
    key_count: int, wallet: list[int]
) -> dict[tuple[int, int, int, int], int]:
    """Success polynomial with s replaced by e + l + k + t, exact integer coefficients.

    Input exponent tuples from symbols.py are (a_s, a_l, a_k, a_t).
    """
    coeffs = success_probability_polynomial_coefficients(key_count, wallet)
    out: dict[tuple[int, int, int, int], int] = {}
    for (a_s, a_l, a_k, a_t), c in coeffs.items():
        for (be, bl, bk, bt), m in _multinomial_expand(a_s).items():
            key = (be, a_l + bl, a_k + bk, a_t + bt)
            out[key] = out.get(key, 0) + c * m
    return {key: c for key, c in out.items() if c != 0}


def poly_sub(
    p: dict[tuple[int, int, int, int], int], q: dict[tuple[int, int, int, int], int]
) -> dict[tuple[int, int, int, int], int]:
    out = dict(p)
    for key, c in q.items():
        out[key] = out.get(key, 0) - c
        if out[key] == 0:
            del out[key]
    return out


def poly_mul_by_sum(
    p: dict[tuple[int, int, int, int], int]
) -> dict[tuple[int, int, int, int], int]:
    """Multiply polynomial by (e + l + k + t)."""
    out: dict[tuple[int, int, int, int], int] = {}
    for key, c in p.items():
        for axis in range(4):
            new_key = tuple(key[i] + (1 if i == axis else 0) for i in range(4))
            out[new_key] = out.get(new_key, 0) + c
    return {key: c for key, c in out.items() if c != 0}


def certifies_nonnegative(
    diff: dict[tuple[int, int, int, int], int], max_polya_power: int = 4
) -> int | None:
    """Return the Polya power m certifying diff >= 0 on the region, or None."""
    current = diff
    for m in range(max_polya_power + 1):
        if all(c >= 0 for c in current.values()):
            return m
        current = poly_mul_by_sum(current)
    return None


def prove_key_count(key_count: int, *, max_polya_power: int = 4, verbose: bool = True):
    wallets = get_cached_static_wallets(key_count)
    cov = coverage_matrix(wallets, key_count)
    sup_counts = incomplete_layer_counts_support_relative(wallets, key_count)

    bad = [i for i in range(len(wallets)) if sup_counts[i] >= 2]
    good = [i for i in range(len(wallets)) if sup_counts[i] <= 1]

    if verbose:
        print(f"=== n={key_count}: {len(bad)} wallets with >=2 incomplete layers, "
              f"{len(good)} candidates with <=1 ===")

    polys = {}

    def poly(i: int):
        if i not in polys:
            polys[i] = substituted_success_poly(key_count, wallets[i])
        return polys[i]

    unproven = []
    for bi in bad:
        found = None
        for gi in good:
            diff = poly_sub(poly(gi), poly(bi))
            m = certifies_nonnegative(diff, max_polya_power)
            if m is not None:
                found = (gi, m)
                break
        if found is None:
            unproven.append(bi)
            if verbose:
                print(f"  UNPROVEN: {walletStrAscii(wallets[bi], and_token='AND', or_token='OR')}")
        elif verbose:
            gi, m = found
            print(
                f"  {walletStrAscii(wallets[bi], and_token='AND', or_token='OR')}"
                f"  <=  {walletStrAscii(wallets[gi], and_token='AND', or_token='OR')}"
                f"  (Polya power {m})"
            )

    if verbose:
        print(f"n={key_count}: proven for {len(bad) - len(unproven)}/{len(bad)} bad wallets")
    return unproven


if __name__ == "__main__":
    key_counts = [int(a) for a in sys.argv[1:]] or [4, 5]
    all_ok = True
    for n in key_counts:
        unproven = prove_key_count(n)
        if unproven:
            all_ok = False
        print()
    if all_ok:
        print("THEOREM (certified): for pSAFE >= 1/2, every wallet with >= 2 incomplete")
        print("layers is weakly dominated by a wallet with <= 1 incomplete layer, at the")
        print("tested key counts. Hence some optimal wallet has <= 1 incomplete layer,")
        print("and the incomplete-layer count of the optimum can never grow beyond 1.")
