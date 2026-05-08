import sys
import math
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

# Allow running `python scripts/ittays_experiments.py` from repo root.
_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src"
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from retry_simul import computations
from retry_simul.consts import SAFE
from retry_simul import wallet_enumerations
from retry_simul.types_of_wallets import symmetric_wallet
from retry_simul.wallet_cache import get_cached_static_wallets


def _normalize_wallet(wallet: Iterable[int] | None) -> Tuple[int, ...]:
    if not wallet:
        return tuple()
    return tuple(sorted(wallet))

def _wallet_pretty(wallet: Iterable[int] | None) -> str:
    if not wallet:
        return "<empty>"
    # Use ASCII tokens to avoid Windows console encoding issues (e.g. cp1255 can't print '∧', '∨')
    return wallet_enumerations.walletStrAscii(list(wallet), and_token="AND", or_token="OR")


def _embed_mask_skip_key(mask: int, skip_pos: int) -> int:
    """Embed a mask on (n-1) keys into n keys by skipping bit-position skip_pos.

    Bit positions are 0-based (LSB is position 0).
    Example: n=4, skip_pos=1 maps old bits [0,1,2] -> new bits [0,2,3].
    """
    if skip_pos < 0:
        raise ValueError("skip_pos must be >= 0")
    out = 0
    i = 0
    mm = int(mask)
    while (mm >> i) != 0:
        if (mm >> i) & 1:
            new_pos = i if i < skip_pos else i + 1
            out |= 1 << new_pos
        i += 1
    return out


def _embed_wallet_skip_key(wallet: Iterable[int], skip_pos: int) -> tuple[int, ...]:
    return tuple(sorted(_embed_mask_skip_key(m, skip_pos) for m in wallet))


def _build_extended_symmetric_candidates(n: int) -> list[tuple[int, ...]]:
    """Return Sym*(n): k-of-n plus embedded k-of-(n-1) ignoring one key (if n>=2)."""
    if n < 1:
        raise ValueError("n must be >= 1")

    candidates: set[tuple[int, ...]] = set()
    for k in range(1, n + 1):
        candidates.add(tuple(sorted(symmetric_wallet(n, k))))

    if n >= 2:
        for skip_pos in range(n):
            for k in range(1, n):
                base = symmetric_wallet(n - 1, k)
                candidates.add(_embed_wallet_skip_key(base, skip_pos))

    return sorted(candidates)


### NOTE
# Earlier iterations used helpers to detect and filter (n-1)-key symmetric optima.
# The current experiment instead EXTENDS the symmetric family to include those
# ignore-one-key wallets for all n (see _build_extended_symmetric_candidates).


def _compute_psafe_threshold_from_buckets(
    *,
    bucket_all_ok_by_psafe: Dict[float, bool],
    psafe_values_desc: list[float],
) -> float | None:
    """Return smallest pSAFE in the top contiguous all-OK region.

    We sweep from high pSAFE downwards; once we hit any failure bucket, all lower
    pSAFE values are excluded from the "for all scenarios with pSAFE >= T" region.
    """
    all_ok_so_far = True
    threshold: float | None = None
    for psafe in psafe_values_desc:
        if all_ok_so_far and bucket_all_ok_by_psafe.get(psafe, False):
            threshold = psafe
        else:
            all_ok_so_far = False
    return threshold


def find_lowest_psafe_where_symmetric_is_globally_optimal(
    *,
    key_count: int,
    step: float = 0.05,
    include_zero: bool = True,
    deduplicate_by_architecture: bool = True,
    tol: float = 1e-12,
    max_failure_examples: int = 10,
    verbose: bool = True,
) -> tuple[float | None, list[dict[str, Any]]]:
    """Find the minimum pSAFE threshold where symmetric becomes globally optimal.

    Definition (extended symmetric family):
    For a probability scenario, the condition holds if the best success probability
    achievable by the extended symmetric family equals the global optimum success
    probability (within tol).

    The extended symmetric family for n keys includes:
      - all k-of-n symmetric wallets (k=1..n)
      - all embedded k-of-(n-1) symmetric wallets obtained by ignoring exactly one key
        (for all skip positions and k=1..n-1), for n>=2.

    Threshold T (assuming monotonicity in pSAFE):
    We assume that once the condition fails at some pSAFE bucket, it will also fail
    for all lower pSAFE buckets. Under that assumption, we can evaluate buckets from
    high→low and stop at the first failing bucket.
    """
    if key_count < 1:
        raise ValueError("key_count must be >= 1")
    if step <= 0 or step > 1:
        raise ValueError("step must be in (0, 1]")
    if max_failure_examples < 0:
        raise ValueError("max_failure_examples must be >= 0")

    scenarios = computations.generateKeyFaultProbabilityScenarios(
        step=step, include_zero=include_zero
    )
    wallets = get_cached_static_wallets(
        key_count, deduplicate_by_architecture=deduplicate_by_architecture
    )
    extended_candidates = _build_extended_symmetric_candidates(key_count)

    scenarios_by_psafe: dict[float, list[dict]] = defaultdict(list)
    for probs in scenarios:
        scenarios_by_psafe[float(probs[SAFE])].append(probs)

    psafe_values_desc = sorted(scenarios_by_psafe.keys(), reverse=True)
    scenarios_evaluated = 0
    failures_total = 0

    last_all_ok_psafe: float | None = None
    highest_psafe_where_not_hold: float | None = None
    highest_psafe_failure_case: dict[str, Any] | None = None
    failure_examples: list[dict[str, Any]] = []

    # Monotonicity shortcut: stop at first failing bucket.
    for psafe in psafe_values_desc:
        bucket_ok = True
        for probs in scenarios_by_psafe[psafe]:
            scenarios_evaluated += 1
            optimal_wallets, best_p = computations.findOptimalWallet(wallets, key_count, probs)

            states, state_probabilities = wallet_enumerations.enumerateStates(key_count, probs)
            owner_states, adv_states = wallet_enumerations.ownerAdvKeysFromStates(states)
            best_sym_p = -1.0
            best_sym_wallet: tuple[int, ...] | None = None
            for cand in extended_candidates:
                p = computations.computeSuccessProbability(
                    list(cand), owner_states, adv_states, state_probabilities
                )
                if p > best_sym_p:
                    best_sym_p = p
                    best_sym_wallet = cand

            holds = abs(best_sym_p - best_p) <= tol

            if not holds:
                bucket_ok = False
                failures_total += 1

                if highest_psafe_failure_case is None:
                    highest_psafe_failure_case = {
                        "pSAFE": psafe,
                        "probabilities": probs,
                        "best_success_probability": best_p,
                        "optimal_wallets": optimal_wallets,
                        "best_extended_symmetric_success_probability": best_sym_p,
                        "best_extended_symmetric_wallet": list(best_sym_wallet or []),
                    }

                if len(failure_examples) < max_failure_examples:
                    failure_examples.append(
                        {
                            "pSAFE": psafe,
                            "probabilities": probs,
                            "best_success_probability": best_p,
                            "optimal_wallets": optimal_wallets,
                            "best_extended_symmetric_success_probability": best_sym_p,
                            "best_extended_symmetric_wallet": list(best_sym_wallet or []),
                        }
                    )

                # No need to check rest of this bucket.
                break

        if bucket_ok:
            last_all_ok_psafe = psafe
        else:
            highest_psafe_where_not_hold = psafe
            break

    # If we never saw a failing bucket, threshold is the smallest pSAFE on the grid.
    # If the very top bucket failed, there's no T on this grid that satisfies the definition.
    if highest_psafe_where_not_hold is None:
        threshold = min(psafe_values_desc) if psafe_values_desc else None
    else:
        threshold = last_all_ok_psafe

    if verbose:
        print(
            f"key_count={key_count} step={step} include_zero={include_zero} dedup={deduplicate_by_architecture}"
        )
        print(f"scenarios_evaluated={scenarios_evaluated} failures={failures_total}")
        print(f"lowest_psafe_threshold={threshold}")
        print(f"highest_psafe_where_not_hold={highest_psafe_where_not_hold}")
        if highest_psafe_failure_case is not None:
            print(
                "highest_psafe_failure_case_probabilities="
                + str(highest_psafe_failure_case["probabilities"])
            )
            print(
                "highest_psafe_failure_case_optimal_wallets="
                + str(highest_psafe_failure_case.get("optimal_wallets"))
            )
            optimal_wallets = highest_psafe_failure_case.get("optimal_wallets") or []
            if optimal_wallets:
                print("highest_psafe_failure_case_optimal_wallets_pretty=")
                for w in optimal_wallets:
                    print("  " + _wallet_pretty(w))
            best_ext = highest_psafe_failure_case.get("best_extended_symmetric_wallet")
            if best_ext:
                print("highest_psafe_failure_case_best_extended_symmetric_wallet_pretty=")
                print("  " + _wallet_pretty(best_ext))

    return threshold, failure_examples


if __name__ == "__main__":
    # Launch the wallet visualizer on the first (highest-psafe) failure case.
    from retry_simul.wallet_state import WalletState
    from scripts.wallet_visualizer import run_visualizer

    key_count = 5
    step = 0.01

    _threshold, failure_examples = find_lowest_psafe_where_symmetric_is_globally_optimal(
        key_count=key_count,
        step=step,
        include_zero=True,
        deduplicate_by_architecture=True,
        tol=1e-12,
        max_failure_examples=1,
        verbose=True,
    )

    if not failure_examples:
        print("No failure case found; not launching visualizer.")
        raise SystemExit(0)

    failure = failure_examples[0]
    probabilities = failure["probabilities"]
    optimal_wallets = failure.get("optimal_wallets") or []
    base_wallet = (
        WalletState(key_count, list(optimal_wallets[0]), probabilities)
        if optimal_wallets
        else WalletState(key_count, [], probabilities)
    )

    run_visualizer(key_count=key_count, probabilities=probabilities, base_wallet=base_wallet, orientation="columns")

