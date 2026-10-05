"""Test: adding a key to an optimal wallet cannot increase its incomplete-layer count.

Theory: fix a probability scenario. Let opt_n be an optimal static wallet on n keys.
If opt_n uses more than 1 key, then some optimal wallet on n+1 keys has at most as many
incomplete layers as opt_n.

Layer completeness is defined by COVERAGE (matching the visualizer): a combination in
popcount layer k counts as "present" if it is covered by some wallet term (isCovered).
A layer is incomplete when some but not all of its C(n, k) combinations are covered.

Tie handling: optima are often non-unique. The n-key incomplete count is the MIN over
optimal n-key wallets that use more than one key (scenario skipped if there are none);
the (n+1)-key count is the MIN over all optimal (n+1)-key wallets. A counterexample
therefore means EVERY optimal wallet at n+1 has strictly more incomplete layers than
the best optimal at n.
"""
import sys
from math import comb
from pathlib import Path
from typing import Any

import numpy as np

for _src in Path(__file__).resolve().parents:
    if (_src / "helpers").is_dir() and (_src / "scripts").is_dir():
        if str(_src) not in sys.path:
            sys.path.insert(0, str(_src))
        break

from helpers import computations, wallet_enumerations
from helpers.consts import SAFE, LOST, LEAKED, STOLEN
from helpers.wallet_cache import get_cached_static_wallets

TOL = 1e-12


def coverage_matrix(wallets: list[list[int]], key_count: int) -> np.ndarray:
    """Boolean matrix cov[w, mask] = wallet w covers key-combination mask."""
    masks = np.arange(1 << key_count)
    cov = np.zeros((len(wallets), 1 << key_count), dtype=bool)
    for i, wallet in enumerate(wallets):
        row = cov[i]
        for term in wallet:
            row |= (masks & term) == term
    return cov


def pair_probability_matrix(key_count: int, probabilities: dict[int, float]) -> np.ndarray:
    """P[owner_mask, adv_mask] = probability of that (owner, adversary) key-holding pair.

    Keys are i.i.d., so P is the n-fold Kronecker product of the single-key 2x2 joint:
    owner-bit x adv-bit -> SAFE=(1,0), LOST=(0,0), LEAKED=(1,1), STOLEN=(0,1).
    """
    single = np.array(
        [
            [probabilities[LOST], probabilities[STOLEN]],
            [probabilities[SAFE], probabilities[LEAKED]],
        ]
    )
    P = np.array([[1.0]])
    for _ in range(key_count):
        P = np.kron(P, single)
    return P


def success_probabilities(cov: np.ndarray, P: np.ndarray) -> np.ndarray:
    """Success probability per wallet: p_w = c_w . P . (1 - c_w)."""
    covf = cov.astype(float)
    return ((covf @ P) * (1.0 - covf)).sum(axis=1)


def layer_index_arrays(key_count: int) -> list[np.ndarray]:
    """For each k in 1..n, the array of masks with popcount k."""
    masks = np.arange(1 << key_count)
    popcounts = np.array([m.bit_count() for m in range(1 << key_count)])
    return [masks[popcounts == k] for k in range(1, key_count + 1)]


def incomplete_layer_counts(cov: np.ndarray, key_count: int) -> np.ndarray:
    """Coverage-based incomplete-layer count per wallet."""
    counts = np.zeros(cov.shape[0], dtype=int)
    for k, layer in enumerate(layer_index_arrays(key_count), start=1):
        covered = cov[:, layer].sum(axis=1)
        counts += (covered > 0) & (covered < comb(key_count, k))
    return counts


def incomplete_layer_counts_support_relative(
    wallets: list[list[int]], key_count: int
) -> np.ndarray:
    """Incomplete-layer count per wallet, measured relative to the keys it actually uses.

    A wallet that ignores some keys is projected onto its support before counting, so
    unused keys do not inflate the count (embedding (1 AND 2) in 4 keys still counts 0).
    """
    layers_by_support: dict[int, list[np.ndarray]] = {}
    counts = np.zeros(len(wallets), dtype=int)
    for i, wallet in enumerate(wallets):
        union = 0
        for term in wallet:
            union |= term
        support = union.bit_count()
        bits = [b for b in range(key_count) if (union >> b) & 1]
        projected = []
        for term in wallet:
            mask = 0
            for j, b in enumerate(bits):
                if (term >> b) & 1:
                    mask |= 1 << j
            projected.append(mask)

        masks = np.arange(1 << support)
        cov = np.zeros(1 << support, dtype=bool)
        for term in projected:
            cov |= (masks & term) == term

        if support not in layers_by_support:
            layers_by_support[support] = layer_index_arrays(support)
        count = 0
        for k, layer in enumerate(layers_by_support[support], start=1):
            covered = cov[layer].sum()
            if 0 < covered < comb(support, k):
                count += 1
        counts[i] = count
    return counts


def uses_multiple_keys(wallets: list[list[int]]) -> np.ndarray:
    """Per wallet: does the union of its terms involve more than one key?"""
    result = np.zeros(len(wallets), dtype=bool)
    for i, wallet in enumerate(wallets):
        union = 0
        for term in wallet:
            union |= term
        result[i] = union.bit_count() > 1
    return result


def _self_check(key_count: int = 3, step: float = 0.25) -> None:
    """Verify the vectorized success computation against computations.py."""
    wallets = get_cached_static_wallets(key_count)
    cov = coverage_matrix(wallets, key_count)
    for probs in computations.generateKeyFaultProbabilityScenarios(step=step):
        P = pair_probability_matrix(key_count, probs)
        fast = success_probabilities(cov, P)
        states, state_probs = wallet_enumerations.enumerateStates(key_count, probs)
        owner_states, adv_states = wallet_enumerations.ownerAdvKeysFromStates(states)
        for i, wallet in enumerate(wallets):
            slow = computations.computeSuccessProbability(
                wallet, owner_states, adv_states, state_probs
            )
            if abs(slow - fast[i]) > 1e-9:
                raise AssertionError(
                    f"self-check failed: wallet={wallet}, probs={probs}, "
                    f"fast={fast[i]}, slow={slow}"
                )


def check_layer_growth(
    *,
    n_small: int,
    step: float = 0.05,
    tol: float = TOL,
    max_counterexamples: int = 10,
    min_incomplete_small: int = 0,
    psafe_min: float | None = None,
    verbose: bool = True,
    print_each: bool = True,
) -> list[dict[str, Any]]:
    """Search for counterexamples to the layer-growth theory for n_small -> n_small+1.

    min_incomplete_small: only report counterexamples whose n-key optimum already has
    at least this many incomplete layers (0 -> 1 growth is often a definitional
    artifact of the layer denominator C(n, k) growing with n).

    Always scans the full scenario grid and prints a histogram of
    (incomplete at n) -> (incomplete at n+1) transitions.
    """
    n_big = n_small + 1

    wallets_small = get_cached_static_wallets(n_small)
    wallets_big = get_cached_static_wallets(n_big)
    cov_small = coverage_matrix(wallets_small, n_small)
    cov_big = coverage_matrix(wallets_big, n_big)
    incomplete_small = incomplete_layer_counts(cov_small, n_small)
    incomplete_big = incomplete_layer_counts(cov_big, n_big)
    sup_small = incomplete_layer_counts_support_relative(wallets_small, n_small)
    sup_big = incomplete_layer_counts_support_relative(wallets_big, n_big)
    multi_key = uses_multiple_keys(wallets_small)

    scenarios = computations.generateKeyFaultProbabilityScenarios(step=step)
    if psafe_min is not None:
        scenarios = [p for p in scenarios if p[SAFE] > psafe_min]

    counterexamples: list[dict[str, Any]] = []
    transitions: dict[tuple[int, int], int] = {}
    sup_transitions: dict[tuple[int, int], int] = {}
    skipped_single_key = 0
    tested = 0

    for probs in scenarios:
        p_small = success_probabilities(cov_small, pair_probability_matrix(n_small, probs))
        p_big = success_probabilities(cov_big, pair_probability_matrix(n_big, probs))

        optima_small = p_small >= p_small.max() - tol
        eligible = optima_small & multi_key
        if not eligible.any():
            skipped_single_key += 1
            continue
        tested += 1

        optima_big = p_big >= p_big.max() - tol
        i_small = incomplete_small[eligible].min()
        i_big = incomplete_big[optima_big].min()
        transitions[(int(i_small), int(i_big))] = (
            transitions.get((int(i_small), int(i_big)), 0) + 1
        )

        s_small = sup_small[eligible].min()
        s_big = sup_big[optima_big].min()
        sup_transitions[(int(s_small), int(s_big))] = (
            sup_transitions.get((int(s_small), int(s_big)), 0) + 1
        )

        if s_big > s_small and s_small >= min_incomplete_small and (
            len(counterexamples) < max_counterexamples
        ):
            small_idx = int(np.flatnonzero(eligible)[sup_small[eligible].argmin()])
            big_idx = int(np.flatnonzero(optima_big)[sup_big[optima_big].argmin()])
            counterexamples.append(
                {
                    "probabilities": probs,
                    "pSAFE": probs[SAFE],
                    "n_small": n_small,
                    "incomplete_small": int(i_small),
                    "incomplete_big": int(i_big),
                    "support_incomplete_small": int(s_small),
                    "support_incomplete_big": int(s_big),
                    "optimal_small": list(wallets_small[small_idx]),
                    "optimal_small_p": float(p_small[small_idx]),
                    "optimal_big": list(wallets_big[big_idx]),
                    "optimal_big_p": float(p_big[big_idx]),
                    "optimal_small_pretty": wallet_enumerations.walletStrAscii(
                        wallets_small[small_idx], and_token="AND", or_token="OR"
                    ),
                    "optimal_big_pretty": wallet_enumerations.walletStrAscii(
                        wallets_big[big_idx], and_token="AND", or_token="OR"
                    ),
                }
            )
            if verbose and print_each:
                ce = counterexamples[-1]
                print(f"Counterexample ({n_small} -> {n_big} keys):")
                print(f"  probabilities={probs}")
                print(
                    f"  incomplete layers (support-relative): "
                    f"{ce['support_incomplete_small']} -> {ce['support_incomplete_big']}"
                    f" (embedded: {ce['incomplete_small']} -> {ce['incomplete_big']})"
                )
                print(f"  opt_{n_small}: {ce['optimal_small_pretty']} (p={ce['optimal_small_p']})")
                print(f"  opt_{n_big}: {ce['optimal_big_pretty']} (p={ce['optimal_big_p']})")

    if verbose:
        print()
        print(f"=== Layer growth {n_small} -> {n_big} keys ===")
        print(f"step={step}, scenarios={len(scenarios)}")
        print(f"tested (multi-key optimum at n={n_small}): {tested}")
        print(f"skipped (all optima use <=1 key): {skipped_single_key}")
        print("embedded transitions (incomplete at n -> incomplete at n+1): count")
        for (a, b), count in sorted(transitions.items()):
            marker = "  <-- GROWTH" if b > a else ""
            print(f"  {a} -> {b}: {count}{marker}")
        print("support-relative transitions (unused keys don't inflate the count):")
        for (a, b), count in sorted(sup_transitions.items()):
            marker = "  <-- GROWTH" if b > a else ""
            print(f"  {a} -> {b}: {count}{marker}")
        print(
            f"reported counterexamples (support-relative growth from >= "
            f"{min_incomplete_small}): {len(counterexamples)}"
        )
        if not counterexamples:
            print("No counterexample found - theory holds on this grid.")

    return counterexamples


if __name__ == "__main__":
    step = float(sys.argv[1]) if len(sys.argv) > 1 else 0.05

    _self_check()
    print("Self-check passed.\n")

    all_counterexamples = {}
    for n_small in range(2, 6):
        ces = check_layer_growth(
            n_small=n_small,
            step=step,
            min_incomplete_small=1,
            max_counterexamples=10**9,
            verbose=True,
            print_each=False,
        )
        all_counterexamples[n_small] = ces
        if ces:
            psafes = sorted(ce["pSAFE"] for ce in ces)
            print(f"pSAFE among growth-from->=1 cases: min={psafes[0]}, max={psafes[-1]}")
            above_half = [p for p in psafes if p > 0.5]
            print(f"cases with pSAFE > 0.5: {len(above_half)}")
        print()

    total = sum(len(v) for v in all_counterexamples.values())
    print(f"Total counterexamples across all key counts: {total}")
