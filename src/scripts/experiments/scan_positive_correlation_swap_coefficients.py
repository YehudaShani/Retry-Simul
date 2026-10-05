r"""Exact scan of positive-correlation extreme-swap coefficient signs.

For row=owner set O and column=attacker set A, use

    W(O, A) / s**n = u**|A\O| y**|A| z**(n-|O|).

For each shifted wallet with at least two incomplete layers, remove the
lexicographically largest authorized set in the lowest incomplete layer and
add the lexicographically smallest missing set in the highest incomplete
layer.  The normalized swap gain is a polynomial

    D(u) = sum_b d_b(y, z) u**b.

This script tests, at exact rational (y,z) grid points, the sign-persistence
claim

    d_b < 0  implies  d_c <= 0 for every c > b.

It is an experiment, not a proof.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from fractions import Fraction
from pathlib import Path

for _src in Path(__file__).resolve().parents:
    if (_src / "helpers").is_dir() and (_src / "scripts").is_dir():
        if str(_src) not in sys.path:
            sys.path.insert(0, str(_src))
        break

from helpers.wallet_cache import get_cached_static_wallets
from helpers.wallet_enumerations import isCovered
from scripts.experiments.incomplete_layer_improvement_experiment import (
    incomplete_layer_ks,
    shifted_target_wallets,
)
from scripts.experiments.incomplete_layers_experiment import layer_bitmasks


Monomial = tuple[int, int]
Coefficient = Counter[Monomial]


def _lex_key(mask: int, key_count: int) -> tuple[int, ...]:
    return tuple(i + 1 for i in range(key_count) if mask & (1 << i))


def _covered_family(wallet: list[int], key_count: int) -> set[int]:
    return {
        mask
        for mask in range(1 << key_count)
        if isCovered(mask, wallet)
    }


def _add_weight(
    coefficients: list[Coefficient],
    owner: int,
    attacker: int,
    sign: int,
    key_count: int,
) -> None:
    u_degree = (attacker & ~owner).bit_count()
    y_degree = attacker.bit_count()
    z_degree = key_count - owner.bit_count()
    coefficients[u_degree][(y_degree, z_degree)] += sign


def extreme_swap_coefficients(
    family: set[int],
    removed: int,
    added: int,
    key_count: int,
) -> list[Coefficient]:
    """Return integer monomial terms for every ordinary-u coefficient."""
    coefficients: list[Coefficient] = [Counter() for _ in range(key_count + 1)]
    complement = set(range(1 << key_count)) - family

    # d^T W (1-f), where d = 1_added - 1_removed.
    for attacker in complement:
        _add_weight(coefficients, added, attacker, +1, key_count)
        _add_weight(coefficients, removed, attacker, -1, key_count)

    # -f^T W d.
    for owner in family:
        _add_weight(coefficients, owner, added, -1, key_count)
        _add_weight(coefficients, owner, removed, +1, key_count)

    # -d^T W d.
    _add_weight(coefficients, added, added, -1, key_count)
    _add_weight(coefficients, added, removed, +1, key_count)
    _add_weight(coefficients, removed, added, +1, key_count)
    _add_weight(coefficients, removed, removed, -1, key_count)

    for coefficient in coefficients:
        for monomial in list(coefficient):
            if coefficient[monomial] == 0:
                del coefficient[monomial]
    return coefficients


def rational_grid(max_denominator: int) -> list[tuple[Fraction, Fraction]]:
    """Unique positive rational pairs y,z with y+z<1."""
    points: set[tuple[Fraction, Fraction]] = set()
    for denominator in range(3, max_denominator + 1):
        for y_numerator in range(1, denominator - 1):
            for z_numerator in range(1, denominator - y_numerator):
                points.add(
                    (
                        Fraction(y_numerator, denominator),
                        Fraction(z_numerator, denominator),
                    )
                )
    return sorted(points)


def _common_integer_coordinates(
    y: Fraction, z: Fraction
) -> tuple[int, int, int]:
    denominator = math.lcm(y.denominator, z.denominator)
    return (
        y.numerator * (denominator // y.denominator),
        z.numerator * (denominator // z.denominator),
        denominator,
    )


def evaluate_coefficient_scaled(
    coefficient: Coefficient,
    y: Fraction,
    z: Fraction,
    key_count: int,
) -> int:
    """Evaluate exactly, multiplied by a positive common denominator."""
    y_num, z_num, denominator = _common_integer_coordinates(y, z)
    scale_degree = 2 * key_count
    return sum(
        multiplicity
        * y_num**y_degree
        * z_num**z_degree
        * denominator ** (scale_degree - y_degree - z_degree)
        for (y_degree, z_degree), multiplicity in coefficient.items()
    )


def _serialize_coefficient(coefficient: Coefficient) -> list[dict[str, int]]:
    return [
        {"multiplicity": multiplicity, "y_degree": y_degree, "z_degree": z_degree}
        for (y_degree, z_degree), multiplicity in sorted(coefficient.items())
    ]


def run_scan(
    key_count: int,
    max_denominator: int,
    output_path: Path,
) -> dict:
    wallets = get_cached_static_wallets(
        key_count, deduplicate_by_architecture=True
    )
    targets = shifted_target_wallets(wallets, key_count)
    points = rational_grid(max_denominator)
    swaps_tested = 0
    coefficient_vectors_tested = 0

    for wallet_index, (wallet, incomplete_count) in enumerate(targets):
        family = _covered_family(wallet, key_count)
        incomplete = incomplete_layer_ks(wallet, key_count)
        lowest, highest = incomplete[0], incomplete[-1]
        authorized_lowest = [
            mask
            for mask in layer_bitmasks(key_count, lowest)
            if mask in family
        ]
        missing_highest = [
            mask
            for mask in layer_bitmasks(key_count, highest)
            if mask not in family
        ]
        removed = max(authorized_lowest, key=lambda mask: _lex_key(mask, key_count))
        added = min(missing_highest, key=lambda mask: _lex_key(mask, key_count))
        coefficients = extreme_swap_coefficients(
            family, removed, added, key_count
        )
        swaps_tested += 1

        for y, z in points:
            values = [
                evaluate_coefficient_scaled(coefficient, y, z, key_count)
                for coefficient in coefficients
            ]
            coefficient_vectors_tested += 1
            first_negative = next(
                (degree for degree, value in enumerate(values) if value < 0),
                None,
            )
            if first_negative is None:
                continue
            later_positive = next(
                (
                    degree
                    for degree in range(first_negative + 1, len(values))
                    if values[degree] > 0
                ),
                None,
            )
            if later_positive is None:
                continue

            result = {
                "status": "counterexample",
                "key_count": key_count,
                "max_denominator": max_denominator,
                "rational_grid_points": len(points),
                "shifted_target_wallets": len(targets),
                "wallet_index": wallet_index,
                "swaps_tested_before_stop": swaps_tested,
                "coefficient_vectors_tested_before_stop": coefficient_vectors_tested,
                "wallet_generators": wallet,
                "incomplete_layer_count": incomplete_count,
                "incomplete_layers": incomplete,
                "removed_mask": removed,
                "removed_set": _lex_key(removed, key_count),
                "added_mask": added,
                "added_set": _lex_key(added, key_count),
                "y": str(y),
                "z": str(z),
                "first_negative_degree": first_negative,
                "later_positive_degree": later_positive,
                "scaled_coefficient_values": values,
                "ordinary_u_coefficients": [
                    _serialize_coefficient(coefficient)
                    for coefficient in coefficients
                ],
            }
            output_path.write_text(
                json.dumps(result, indent=2) + "\n", encoding="utf-8"
            )
            return result

    result = {
        "status": "no_counterexample_on_grid",
        "key_count": key_count,
        "max_denominator": max_denominator,
        "rational_grid_points": len(points),
        "shifted_target_wallets": len(targets),
        "extreme_swaps_tested": swaps_tested,
        "coefficient_vectors_tested": coefficient_vectors_tested,
    }
    output_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--key-count", type=int, default=6)
    parser.add_argument("--max-denominator", type=int, default=20)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/swap_coefficient_scan_n6.json"),
    )
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result = run_scan(args.key_count, args.max_denominator, args.output)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
