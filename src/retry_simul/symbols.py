"""Symbolic success probability as a polynomial in the four per-key state probabilities."""

from __future__ import annotations

import sys
from collections import defaultdict
from collections.abc import Sequence
from typing import Mapping

from .consts import SAFE, LOST, LEAKED, STOLEN, KeyStates, KeyStateString
from . import wallet_cache
from .wallet_enumerations import enumerateStates, ownerAdvKeysFromStates, isCovered

# Uniform placeholder; only the state list structure is used.
_PLACEHOLDER_PROBS: dict[int, float] = {s: 0.25 for s in KeyStates}

# Tuple (n_SAFE, n_LOST, n_LEAKED, n_STOLEN) with fixed KeyStates order
ExponentTuple = tuple[int, int, int, int]

# Single-letter monomial names in ``sorted(KeyStates)`` order (SAFE, LOST, LEAKED, STOLEN).
UI_MONOMIAL_STATE_LABELS: tuple[str, str, str, str] = ("S", "O", "E", "T")

# Unicode superscripts for terminals that support them (UTF-8, etc.)
_SUP_DIGITS = "⁰¹²³⁴⁵⁶⁷⁸⁹"


def _stdout_prefers_unicode() -> bool:
    enc = (getattr(sys.stdout, "encoding", None) or "").lower()
    return enc.startswith("utf") or enc in ("cp65001",)


def _mult_sep() -> str:
    return " · " if _stdout_prefers_unicode() else " * "


def _exp_suffix(n: int) -> str:
    if n < 0:
        raise ValueError(n)
    if n == 1:
        return ""
    if _stdout_prefers_unicode():
        return "".join(_SUP_DIGITS[int(c)] for c in str(n))
    return f"^{n}"


def success_probability_polynomial_coefficients(
    key_count: int,
    bitmasks: list[int],
) -> dict[ExponentTuple, int]:
    """Coefficient of p_SAFE^a p_LOST^b p_LEAKED^c p_STOLEN^d for each successful ordered world.

    Keys are i.i.d.; each assignment contributes one monomial. Coefficients count
    successful key-state assignments sharing the same counts (multiset).
    """
    states, _ = enumerateStates(key_count, _PLACEHOLDER_PROBS)
    owner_states, adv_states = ownerAdvKeysFromStates(states)

    coeffs: dict[ExponentTuple, int] = defaultdict(int)
    for i, state_row in enumerate(states):
        if isCovered(owner_states[i], bitmasks) and not isCovered(adv_states[i], bitmasks):
            counts = {s: 0 for s in KeyStates}
            for ks in state_row:
                counts[ks] += 1
            tup = tuple(counts[s] for s in sorted(KeyStates))
            coeffs[tup] += 1

    return dict(coeffs)


def all_static_wallet_success_polynomial_coefficients(
    key_count: int,
) -> tuple[bool, list[tuple[list[int], dict[ExponentTuple, int]]]]:
    """Success-probability polynomial coefficients for every static wallet at this key count."""
    cache_preloaded = wallet_cache.has_cached_wallets(key_count)
    wallets = wallet_cache.get_cached_static_wallets(key_count, deduplicate_by_architecture=True)
    pairs: list[tuple[list[int], dict[ExponentTuple, int]]] = []
    for bitmasks in wallets:
        coeffs = success_probability_polynomial_coefficients(key_count, bitmasks)
        pairs.append((bitmasks, coeffs))
    return cache_preloaded, pairs


def success_probability_polynomial_difference_coefficients(
    before: Mapping[ExponentTuple, int],
    after: Mapping[ExponentTuple, int],
) -> dict[ExponentTuple, int]:
    """Coefficient-wise difference ``after - before``; keys with zero net drop out."""
    keys = set(before) | set(after)
    out: dict[ExponentTuple, int] = {}
    for k in keys:
        d = after.get(k, 0) - before.get(k, 0)
        if d != 0:
            out[k] = d
    return out


def _monomial_factor_body(
    exponents: ExponentTuple,
    *,
    variable_prefix: str,
    state_labels: list[str],
    mult_sep: str,
    exp_suffix_fn,
) -> str:
    factors: list[str] = []
    for label, e in zip(state_labels, exponents):
        if e == 0:
            continue
        base = f"{variable_prefix}_{label}" if variable_prefix else label
        if e == 1:
            factors.append(base)
        else:
            factors.append(f"{base}{exp_suffix_fn(e)}")
    return mult_sep.join(factors) if factors else "1"


def format_success_probability_polynomial(
    coeffs: Mapping[ExponentTuple, int],
    *,
    variable_prefix: str = "p",
    multiline: bool = True,
    use_unicode: bool | None = None,
    state_labels: Sequence[str] | None = None,
) -> str:
    """Human-readable sum of monomials (symbolic probabilities).

    ``state_labels`` defaults to ``KeyStateString`` values in ``sorted(KeyStates)`` order.
    If provided, it must use that same order (one label per key state).
    """
    if not coeffs:
        return "0"

    u = _stdout_prefers_unicode() if use_unicode is None else use_unicode
    mult_sep = " · " if u else " * "

    def exp_suffix_local(n: int) -> str:
        if n < 0:
            raise ValueError(n)
        if n == 1:
            return ""
        if u:
            return "".join(_SUP_DIGITS[int(c)] for c in str(n))
        return f"^{n}"

    resolved_labels = (
        list(state_labels) if state_labels is not None else [KeyStateString[s] for s in sorted(KeyStates)]
    )

    def format_monomial(exponents: ExponentTuple, coeff: int) -> str:
        body = _monomial_factor_body(
            exponents,
            variable_prefix=variable_prefix,
            state_labels=resolved_labels,
            mult_sep=mult_sep,
            exp_suffix_fn=exp_suffix_local,
        )
        if coeff == 1:
            return body
        return f"{coeff}{mult_sep}{body}"

    items = sorted(coeffs.items(), key=lambda it: (-sum(it[0]), it[0]))
    terms = [format_monomial(exp, c) for exp, c in items]
    if len(terms) == 1:
        return terms[0]
    if not multiline:
        return " + ".join(terms)

    pad = "      "
    lines = [f"{pad}{terms[0]}"]
    for t in terms[1:]:
        lines.append(f"    + {t}")
    return "\n".join(lines)


def format_signed_polynomial_sum(
    coeffs: Mapping[ExponentTuple, int],
    *,
    variable_prefix: str = "p",
    multiline: bool = True,
    use_unicode: bool | None = None,
    state_labels: Sequence[str] | None = None,
) -> str:
    """Format a signed integer-coefficient polynomial.

    ``state_labels`` defaults to ``KeyStateString`` values in ``sorted(KeyStates)`` order.
    If provided, it must use that same order (one label per key state).
    """
    items = [(e, c) for e, c in coeffs.items() if c != 0]
    if not items:
        return "0"

    u = _stdout_prefers_unicode() if use_unicode is None else use_unicode
    mult_sep = " · " if u else " * "
    resolved_labels = (
        list(state_labels) if state_labels is not None else [KeyStateString[s] for s in sorted(KeyStates)]
    )

    def exp_suffix_local(n: int) -> str:
        if n < 0:
            raise ValueError(n)
        if n == 1:
            return ""
        if u:
            return "".join(_SUP_DIGITS[int(c)] for c in str(n))
        return f"^{n}"

    def term_body(exponents: ExponentTuple, abs_c: int) -> str:
        factors = _monomial_factor_body(
            exponents,
            variable_prefix=variable_prefix,
            state_labels=resolved_labels,
            mult_sep=mult_sep,
            exp_suffix_fn=exp_suffix_local,
        )
        if abs_c == 1:
            return factors
        return f"{abs_c}{mult_sep}{factors}"

    items.sort(key=lambda it: (-sum(it[0]), it[0]))

    if not multiline:
        parts: list[str] = []
        for i, (exp, c) in enumerate(items):
            body = term_body(exp, abs(c))
            if i == 0:
                parts.append(f"- {body}" if c < 0 else body)
            else:
                parts.append(f"- {body}" if c < 0 else f"+ {body}")
        return " ".join(parts)

    pad = "      "
    lines_out: list[str] = []
    for i, (exp, c) in enumerate(items):
        body = term_body(exp, abs(c))
        if i == 0:
            lines_out.append(f"{pad}- {body}" if c < 0 else f"{pad}{body}")
        elif c < 0:
            lines_out.append(f"    - {body}")
        else:
            lines_out.append(f"    + {body}")
    return "\n".join(lines_out)


def print_success_probability_polynomial(wallet, *, variable_prefix: str = "p") -> None:
    """Print the success probability polynomial for a wallet-like object."""
    coeffs = success_probability_polynomial_coefficients(wallet.key_count, list(wallet.bitmasks))
    n_terms = len(coeffs)
    sep = " · " if _stdout_prefers_unicode() else "; "
    subtitle = (
        f"{n_terms} term{'s' if n_terms != 1 else ''}, i.i.d. keys{sep}"
        f"p_SAFE + p_LOST + p_LEAKED + p_STOLEN = 1"
    )
    print(subtitle)
    print()
    expr = format_success_probability_polynomial(coeffs, variable_prefix=variable_prefix, multiline=True)
    print(expr)
    print()


def evaluate_success_polynomial(coeffs: Mapping[ExponentTuple, int], probs: Mapping[int, float]) -> float:
    """Turn the symbolic polynomial into a number."""
    total = 0.0
    ordered = sorted(KeyStates)
    for exp_tup, c in coeffs.items():
        monomial = 1.0
        for state, exp in zip(ordered, exp_tup):
            monomial *= probs[state] ** exp
        total += c * monomial
    return total


def main() -> None:
    key_count = 3
    _cache_preloaded, static_pairs = all_static_wallet_success_polynomial_coefficients(key_count)
    for bitmasks, coeffs in static_pairs:
        poly = format_success_probability_polynomial(coeffs, multiline=False)
        print(f"{bitmasks}  {poly}")
        print("--------------------------------")


if __name__ == "__main__":
    main()

