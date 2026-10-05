from fractions import Fraction
from itertools import combinations

from helpers.symbols import success_probability_polynomial_coefficients
from helpers.wallet_cache import get_cached_static_wallets


def _covers(wallet: list[int], mask: int) -> bool:
    return any(mask & term == term for term in wallet)


def _incomplete_layer_count(wallet: list[int], key_count: int) -> int:
    count = 0
    for rank in range(1, key_count + 1):
        layer = [
            sum(1 << bit for bit in subset)
            for subset in combinations(range(key_count), rank)
        ]
        covered = sum(_covers(wallet, mask) for mask in layer)
        count += 0 < covered < len(layer)
    return count


def _exact_success(
    wallet: list[int],
    *,
    safe: Fraction,
    stolen: Fraction,
    leaked: Fraction,
    lost: Fraction,
) -> Fraction:
    # symbols.py uses exponent order (SAFE, LOST, LEAKED, STOLEN).
    coefficients = success_probability_polynomial_coefficients(3, wallet)
    return sum(
        coefficient
        * safe**exponents[0]
        * lost**exponents[1]
        * leaked**exponents[2]
        * stolen**exponents[3]
        for exponents, coefficient in coefficients.items()
    )


def test_pairwise_safe_bound_does_not_imply_canonical_optimum() -> None:
    safe = Fraction(12, 25)
    stolen = Fraction(21, 50)
    leaked = lost = Fraction(1, 20)

    assert safe + stolen + leaked + lost == 1
    assert safe > stolen + leaked
    assert safe > stolen + lost

    wallets = get_cached_static_wallets(3)
    scores = {
        tuple(wallet): _exact_success(
            wallet,
            safe=safe,
            stolen=stolen,
            leaked=leaked,
            lost=lost,
        )
        for wallet in wallets
    }

    dictator = (1,)
    majority = (3, 5, 6)

    assert scores[dictator] == Fraction(12, 25)
    assert _incomplete_layer_count(list(dictator), 3) == 2
    assert scores[majority] == Fraction(14913, 31250)
    assert scores[dictator] - scores[majority] == Fraction(87, 31250)

    best_canonical = max(
        score
        for wallet, score in scores.items()
        if _incomplete_layer_count(list(wallet), 3) <= 1
    )
    assert scores[dictator] == max(scores.values())
    assert best_canonical == scores[majority]
    assert scores[dictator] > best_canonical
