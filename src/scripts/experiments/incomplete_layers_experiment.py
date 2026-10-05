"""Test: when pSAFE > 0.5, wallets with >1 incomplete layer are beaten by some threshold wallet.

An incomplete layer k is a popcount layer where the wallet contains some but not all
C(n, k) conjunctions. A threshold wallet is a symmetric k-of-n wallet.
"""
import sys
from itertools import combinations
from pathlib import Path
from typing import Any

for _src in Path(__file__).resolve().parents:
    if (_src / "helpers").is_dir() and (_src / "scripts").is_dir():
        if str(_src) not in sys.path:
            sys.path.insert(0, str(_src))
        break

from helpers import computations, wallet_enumerations
from helpers.consts import SAFE
from helpers.types_of_wallets import symmetric_wallet
from helpers.wallet_cache import get_cached_static_wallets
from helpers.wallet_state import WalletState


def layer_bitmasks(key_count: int, k: int) -> set[int]:
    return {
        sum(1 << (i - 1) for i in combo)
        for combo in combinations(range(1, key_count + 1), k)
    }


def count_incomplete_layers(wallet: list[int], key_count: int) -> int:
    wallet_set = set(wallet)
    incomplete = 0
    for k in range(1, key_count + 1):
        layer = layer_bitmasks(key_count, k)
        present = wallet_set & layer
        if present and present != layer:
            incomplete += 1
    return incomplete


def wallets_with_many_incomplete_layers(
    wallets: list[list[int]], key_count: int, *, min_incomplete: int = 2
) -> list[tuple[list[int], int]]:
    """Return (wallet, incomplete_layer_count) for wallets meeting the threshold."""
    result = []
    for wallet in wallets:
        incomplete = count_incomplete_layers(wallet, key_count)
        if incomplete > min_incomplete - 1:
            result.append((wallet, incomplete))
    return result


def best_threshold_wallet_success(
    key_count: int,
    probabilities: dict[int, float],
    *,
    owner_states=None,
    adv_states=None,
    state_probs=None,
) -> tuple[float, int | None]:
    """Return (best success, best k) over all symmetric k-of-n threshold wallets."""
    if owner_states is None:
        states, state_probs = wallet_enumerations.enumerateStates(key_count, probabilities)
        owner_states, adv_states = wallet_enumerations.ownerAdvKeysFromStates(states)

    best_p = -1.0
    best_k: int | None = None
    for k in range(1, key_count + 1):
        wallet = symmetric_wallet(key_count, k)
        p = computations.computeSuccessProbability(wallet, owner_states, adv_states, state_probs)
        if p > best_p:
            best_p = p
            best_k = k
    return best_p, best_k


def check_incomplete_layers_beaten_by_threshold(
    *,
    key_count: int = 5,
    step: float = 0.02,
    psafe_min: float = 0.5,
    tol: float = 1e-12,
    deduplicate_by_architecture: bool = True,
    max_counterexamples: int = 5,
    verbose: bool = True,
    quiet: bool = False,
) -> list[dict[str, Any]]:
    """Search for counterexamples to the incomplete-layers theory.

    Theory: for every scenario with pSAFE > psafe_min, every wallet with >1 incomplete
    layer is strictly beaten by at least one symmetric threshold wallet.

    Returns a list of counterexample dicts (empty if theory holds on tested inputs).
    """
    if psafe_min < 0.5:
        raise ValueError("psafe_min must be >= 0.5 for this experiment")

    scenarios = [
        p
        for p in computations.generateKeyFaultProbabilityScenarios(step=step)
        if p[SAFE] > psafe_min
    ]
    wallets = get_cached_static_wallets(
        key_count, deduplicate_by_architecture=deduplicate_by_architecture
    )
    target_wallets = wallets_with_many_incomplete_layers(wallets, key_count)

    counterexamples: list[dict[str, Any]] = []
    checks = 0

    for probs in scenarios:
        states, state_probs = wallet_enumerations.enumerateStates(key_count, probs)
        owner_states, adv_states = wallet_enumerations.ownerAdvKeysFromStates(states)
        best_threshold_p, best_threshold_k = best_threshold_wallet_success(
            key_count,
            probs,
            owner_states=owner_states,
            adv_states=adv_states,
            state_probs=state_probs,
        )

        for wallet, incomplete in target_wallets:
            checks += 1
            wallet_p = computations.computeSuccessProbability(
                wallet, owner_states, adv_states, state_probs
            )

            if best_threshold_p <= wallet_p + tol:
                counterexamples.append(
                    {
                        "probabilities": probs,
                        "pSAFE": probs[SAFE],
                        "wallet": list(wallet),
                        "wallet_p": wallet_p,
                        "incomplete_layers": incomplete,
                        "best_threshold_k": best_threshold_k,
                        "best_threshold_p": best_threshold_p,
                        "wallet_pretty": wallet_enumerations.walletStrAscii(
                            wallet, and_token="AND", or_token="OR"
                        ),
                        "best_threshold_pretty": wallet_enumerations.walletStrAscii(
                            symmetric_wallet(key_count, best_threshold_k),
                            and_token="AND",
                            or_token="OR",
                        )
                        if best_threshold_k is not None
                        else None,
                    }
                )
                if verbose and not quiet:
                    print("Counterexample found.")
                    print(f"  pSAFE={probs[SAFE]}")
                    print(f"  incomplete_layers={incomplete}")
                    print(f"  wallet_p={wallet_p}")
                    print(f"  best_threshold={best_threshold_k}-of-{key_count}, p={best_threshold_p}")
                    print(f"  wallet: {counterexamples[-1]['wallet_pretty']}")
                if len(counterexamples) >= max_counterexamples:
                    if verbose:
                        _print_summary(
                            key_count=key_count,
                            step=step,
                            psafe_min=psafe_min,
                            scenario_count=len(scenarios),
                            wallet_count=len(wallets),
                            target_wallet_count=len(target_wallets),
                            checks=checks,
                            counterexamples=counterexamples,
                        )
                    return counterexamples

    if verbose:
        _print_summary(
            key_count=key_count,
            step=step,
            psafe_min=psafe_min,
            scenario_count=len(scenarios),
            wallet_count=len(wallets),
            target_wallet_count=len(target_wallets),
            checks=checks,
            counterexamples=counterexamples,
        )

    return counterexamples


def _print_summary(
    *,
    key_count: int,
    step: float,
    psafe_min: float,
    scenario_count: int,
    wallet_count: int,
    target_wallet_count: int,
    checks: int,
    counterexamples: list[dict[str, Any]],
) -> None:
    print()
    print("=== Incomplete layers vs threshold wallets ===")
    print(f"key_count={key_count}, step={step}, psafe_min={psafe_min}")
    print(f"scenarios tested: {scenario_count}")
    print(f"static wallets: {wallet_count}")
    print(f"wallets with >1 incomplete layer: {target_wallet_count}")
    print(f"wallet-scenario checks: {checks}")
    print(f"counterexamples: {len(counterexamples)}")
    if not counterexamples:
        print("No counterexample found — theory holds on this grid.")


if __name__ == "__main__":
    from scripts.wallet_visualizer import run_visualizer

    key_count = 5
    step = 0.02

    counterexamples = check_incomplete_layers_beaten_by_threshold(
        key_count=key_count,
        step=step,
        psafe_min=0.5,
        max_counterexamples=1,
        verbose=True,
    )

    if not counterexamples:
        raise SystemExit(0)

    failure = counterexamples[0]
    run_visualizer(
        key_count=key_count,
        probabilities=failure["probabilities"],
        base_wallet=WalletState(key_count, failure["wallet"], failure["probabilities"]),
        orientation="columns",
    )
