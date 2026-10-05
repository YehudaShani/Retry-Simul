r"""Exact rational-grid scan for negative positive-correlation swap gains.

Uses

    W(O,A) / s**n = u**|A\O| y**|A| z**(n-|O|)

with 0 <= u <= 1 and y+z+u*y*z < 1.  The latter inequality is exactly
s>1/2 after normalization.  Every sign comparison is integer-exact.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
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
from scripts.experiments.scan_positive_correlation_swap_coefficients import (
    _common_integer_coordinates,
    _lex_key,
    evaluate_coefficient_scaled,
    extreme_swap_coefficients,
    rational_grid,
)


def rational_unit_grid(max_denominator: int) -> list[Fraction]:
    points = {Fraction(0), Fraction(1)}
    for denominator in range(2, max_denominator + 1):
        for numerator in range(1, denominator):
            points.add(Fraction(numerator, denominator))
    return sorted(points)


def _family(wallet: list[int], key_count: int) -> set[int]:
    return {
        mask
        for mask in range(1 << key_count)
        if isCovered(mask, wallet)
    }


def _extreme_swap(
    wallet: list[int], key_count: int
) -> tuple[set[int], list[int], int, int]:
    family = _family(wallet, key_count)
    incomplete = incomplete_layer_ks(wallet, key_count)
    lowest, highest = incomplete[0], incomplete[-1]
    authorized = [
        mask
        for mask in layer_bitmasks(key_count, lowest)
        if mask in family
    ]
    missing = [
        mask
        for mask in layer_bitmasks(key_count, highest)
        if mask not in family
    ]
    removed = max(authorized, key=lambda mask: _lex_key(mask, key_count))
    added = min(missing, key=lambda mask: _lex_key(mask, key_count))
    return family, incomplete, removed, added


def _gain_fraction_data(
    scaled_coefficients: list[int],
    y: Fraction,
    z: Fraction,
    u: Fraction,
    key_count: int,
) -> tuple[int, int]:
    """Return exact actual gain as numerator / denominator."""
    y_num, z_num, yz_den = _common_integer_coordinates(y, z)
    u_num, u_den = u.numerator, u.denominator
    numerator = sum(
        value * u_num**degree * u_den ** (key_count - degree)
        for degree, value in enumerate(scaled_coefficients)
    )
    # s = u_den*yz_den**2 / normalization_denominator.
    normalization_denominator = (
        u_den * yz_den**2
        + u_den * yz_den * (y_num + z_num)
        + u_num * y_num * z_num
    )
    return numerator, normalization_denominator**key_count


def run_scan(
    key_count: int,
    yz_max_denominator: int,
    u_max_denominator: int,
    output_path: Path,
) -> dict:
    wallets = get_cached_static_wallets(
        key_count, deduplicate_by_architecture=True
    )
    targets = shifted_target_wallets(wallets, key_count)
    yz_points = rational_grid(yz_max_denominator)
    u_points = rational_unit_grid(u_max_denominator)

    triples_tested = 0
    swaps_tested = 0
    zero_gains = 0
    minimum: dict | None = None
    minimum_num = 0
    minimum_den = 1

    for wallet_index, (wallet, _) in enumerate(targets):
        family, incomplete, removed, added = _extreme_swap(wallet, key_count)
        coefficients = extreme_swap_coefficients(
            family, removed, added, key_count
        )
        swaps_tested += 1

        for y, z in yz_points:
            scaled_coefficients = [
                evaluate_coefficient_scaled(coefficient, y, z, key_count)
                for coefficient in coefficients
            ]
            for u in u_points:
                # Exact feasibility: y+z+u*y*z < 1.
                if y + z + u * y * z >= 1:
                    continue
                triples_tested += 1
                numerator, denominator = _gain_fraction_data(
                    scaled_coefficients, y, z, u, key_count
                )
                if numerator < 0:
                    result = {
                        "status": "negative_gain_counterexample",
                        "key_count": key_count,
                        "yz_max_denominator": yz_max_denominator,
                        "u_max_denominator": u_max_denominator,
                        "yz_grid_points": len(yz_points),
                        "u_grid_points": len(u_points),
                        "shifted_target_wallets": len(targets),
                        "swaps_tested_before_stop": swaps_tested,
                        "feasible_triples_tested_before_stop": triples_tested,
                        "wallet_index": wallet_index,
                        "wallet_generators": wallet,
                        "incomplete_layers": incomplete,
                        "removed_mask": removed,
                        "removed_set": _lex_key(removed, key_count),
                        "added_mask": added,
                        "added_set": _lex_key(added, key_count),
                        "y": str(y),
                        "z": str(z),
                        "u": str(u),
                        "actual_swap_gain": str(Fraction(numerator, denominator)),
                        "scaled_ordinary_u_coefficients": scaled_coefficients,
                    }
                    output_path.write_text(
                        json.dumps(result, indent=2) + "\n", encoding="utf-8"
                    )
                    return result

                if numerator == 0:
                    zero_gains += 1
                if minimum is None or numerator * minimum_den < minimum_num * denominator:
                    minimum_num, minimum_den = numerator, denominator
                    y_num, z_num, yz_den = _common_integer_coordinates(y, z)
                    normalization = (
                        u.denominator * yz_den**2
                        + u.denominator * yz_den * (y_num + z_num)
                        + u.numerator * y_num * z_num
                    )
                    s = Fraction(u.denominator * yz_den**2, normalization)
                    e = s * y
                    lost = s * z
                    stolen = s * u * y * z
                    minimum = {
                        "wallet_index": wallet_index,
                        "wallet_generators": wallet,
                        "incomplete_layers": incomplete,
                        "removed_mask": removed,
                        "removed_set": _lex_key(removed, key_count),
                        "added_mask": added,
                        "added_set": _lex_key(added, key_count),
                        "y": str(y),
                        "z": str(z),
                        "u": str(u),
                        "probabilities_s_t_lost_leaked": [
                            str(s),
                            str(stolen),
                            str(lost),
                            str(e),
                        ],
                        "actual_swap_gain": str(Fraction(numerator, denominator)),
                        "gain_numerator_before_reduction": numerator,
                        "gain_denominator_before_reduction": denominator,
                        "scaled_ordinary_u_coefficients": scaled_coefficients,
                    }

    result = {
        "status": "no_negative_gain_on_grid",
        "key_count": key_count,
        "yz_max_denominator": yz_max_denominator,
        "u_max_denominator": u_max_denominator,
        "yz_grid_points": len(yz_points),
        "u_grid_points": len(u_points),
        "shifted_target_wallets": len(targets),
        "extreme_swaps_tested": swaps_tested,
        "feasible_parameter_triples_tested": triples_tested,
        "zero_gains": zero_gains,
        "minimum_observed": minimum,
    }
    output_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--key-count", type=int, default=6)
    parser.add_argument("--yz-max-denominator", type=int, default=8)
    parser.add_argument("--u-max-denominator", type=int, default=12)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("swap_gain_scan_n6.json"),
    )
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result = run_scan(
        args.key_count,
        args.yz_max_denominator,
        args.u_max_denominator,
        args.output,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
