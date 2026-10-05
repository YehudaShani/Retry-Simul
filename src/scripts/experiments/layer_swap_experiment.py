"""Layer swap experiment: shift + heaviest-out/lightest-in swap should not hurt.

Conjecture: for any wallet with >= 2 incomplete (coverage) layers, pLEAKED = 0 and
pSAFE > 0.5, neither of these actions DECREASES the success probability:

  1. Shifting the wallet (combinatorial down-shift / compression).
  2. One swap on the shifted wallet: remove the "heaviest" covered combination from the
     lowest incomplete layer (via ``remove_bitmask_and_subsets``, visualizer semantics)
     and add the "lightest" missing combination to the highest incomplete layer.

"Weight" compares combinations within a layer by their ascending key-index tuples,
lexicographically from the lowest index: e.g. {3,4} > {2,5} > {2,3} > {1,5}.
The heaviest covered combination is the maximum under this order; the lightest missing
combination is the minimum.

A counterexample is recorded only when an action STRICTLY decreases the success
probability (beyond tolerance); staying equal is not a counterexample.

Wallets are generated randomly per key count (5..9) and kept only if they have at least
two incomplete (coverage) layers. Results are written to ``data/saved_lists`` as
``layer_swap_all_{n}keys.json`` / ``layer_swap_counterexamples_{n}keys.json`` in the
visualizer-compatible format, including a ``highlight`` field marking the swapped
(removed/added) combinations.
"""
import json
import math
import random
import sys
from pathlib import Path
from typing import Any

for _src in Path(__file__).resolve().parents:
    if (_src / "helpers").is_dir() and (_src / "scripts").is_dir():
        if str(_src) not in sys.path:
            sys.path.insert(0, str(_src))
        break

from helpers import wallet_enumerations
from helpers.consts import LEAKED, LOST, SAFE, STOLEN
from helpers.paths import data_path
from helpers.wallet_enumerations import isCovered

from scripts.experiments.incomplete_layers_experiment import layer_bitmasks
from scripts.experiments.incomplete_layer_improvement_experiment import (
    _probs_named,
    _random_scenarios,
    _wallet_for_edits,
    covered_in_layer,
    incomplete_layer_ks,
    shifted_wallet,
)


def _key_indices(bitmask: int) -> tuple[int, ...]:
    """Ascending 1-based key indices of a bitmask, used for lexicographic weight."""
    return tuple(i + 1 for i in range(bitmask.bit_length()) if (bitmask >> i) & 1)


def _minimal_masks(masks: list[int]) -> list[int]:
    """Reduce to minimal generators: drop masks that are supersets of another mask."""
    unique = set(masks)
    return sorted(
        m for m in unique if not any(o != m and (o & m) == o for o in unique)
    )


def _covered_set(wallet: list[int], key_count: int) -> set[int]:
    """Up-closure of the wallet: every non-empty combination it covers."""
    return {m for m in range(1, 1 << key_count) if isCovered(m, wallet)}


def _success_from_covered(
    covered: set[int], owner_states, adv_states, state_probs
) -> float:
    """Success probability using O(1) coverage lookups (fast for large key counts)."""
    return math.fsum(
        p
        for owner, adv, p in zip(owner_states, adv_states, state_probs)
        if owner in covered and adv not in covered
    )


def heaviest_covered_combination(wallet: list[int], key_count: int, k: int) -> int:
    """Heaviest covered combination in layer k (lexicographic max of key tuples)."""
    covered = covered_in_layer(wallet, key_count, k)
    return max(covered, key=_key_indices)


def lightest_missing_combination(wallet: list[int], key_count: int, k: int) -> int:
    """Lightest uncovered combination in layer k (lexicographic min of key tuples)."""
    missing = layer_bitmasks(key_count, k) - covered_in_layer(wallet, key_count, k)
    return min(missing, key=_key_indices)


def swap_heaviest_for_lightest(
    wallet: list[int], key_count: int
) -> dict[str, Any] | None:
    """Remove the heaviest combo of the lowest incomplete layer, add the lightest of the
    highest incomplete layer. Returns swap details, or None if <2 incomplete layers."""
    incomplete = incomplete_layer_ks(wallet, key_count)
    if len(incomplete) < 2:
        return None
    first_k = incomplete[0]
    last_k = incomplete[-1]
    removed = heaviest_covered_combination(wallet, key_count, first_k)
    added = lightest_missing_combination(wallet, key_count, last_k)

    ws = _wallet_for_edits(wallet, key_count)
    ws.remove_bitmask_and_subsets(removed)
    ws.add_bitmask(added)
    return {
        "wallet": _minimal_masks(ws.bitmasks),
        "removed": removed,
        "added": added,
        "first_k": first_k,
        "last_k": last_k,
    }


def generate_random_wallets(
    key_count: int,
    count: int,
    rng: random.Random,
    *,
    min_incomplete: int = 2,
    max_attempts_per_wallet: int = 200,
) -> list[list[int]]:
    """Random distinct wallets (minimal generators) with >= min_incomplete
    incomplete (coverage) layers."""
    max_mask = (1 << key_count) - 1
    max_terms = max(4, 2 * key_count)
    seen: set[tuple[int, ...]] = set()
    wallets: list[list[int]] = []
    attempts = 0
    while len(wallets) < count and attempts < count * max_attempts_per_wallet:
        attempts += 1
        term_count = rng.randint(2, max_terms)
        masks = rng.sample(range(1, max_mask + 1), term_count)
        wallet = _minimal_masks(masks)
        key = tuple(wallet)
        if key in seen:
            continue
        seen.add(key)
        if len(incomplete_layer_ks(wallet, key_count)) >= min_incomplete:
            wallets.append(wallet)
    return wallets


def _prepare_wallet(wallet: list[int], key_count: int) -> dict[str, Any]:
    """Scenario-independent per-wallet data: shift, swap and coverage sets."""
    shifted = shifted_wallet(wallet, key_count)
    swap = swap_heaviest_for_lightest(shifted, key_count)
    prep = {
        "original": wallet,
        "original_covered": _covered_set(wallet, key_count),
        "shifted": shifted,
        "shifted_covered": _covered_set(shifted, key_count),
        "swap": swap,
    }
    if swap is not None:
        prep["swap_covered"] = _covered_set(swap["wallet"], key_count)
    return prep


def _evaluate_case(
    prep: dict[str, Any],
    key_count: int,
    probs: dict[int, float],
    owner_states,
    adv_states,
    state_probs,
    tol: float,
) -> dict[str, Any]:
    p_original = _success_from_covered(
        prep["original_covered"], owner_states, adv_states, state_probs
    )
    p_shifted = _success_from_covered(
        prep["shifted_covered"], owner_states, adv_states, state_probs
    )
    shift_decreased = p_shifted < p_original - tol

    swap = prep["swap"]
    p_swapped: float | None = None
    swap_result: str | None = None
    if swap is not None:
        p_swapped = _success_from_covered(
            prep["swap_covered"], owner_states, adv_states, state_probs
        )
        if p_swapped < p_shifted - tol:
            swap_result = "decrease"
        elif p_swapped > p_shifted + tol:
            swap_result = "increase"
        else:
            swap_result = "equal"

    issues = []
    if shift_decreased:
        issues.append("shift_decrease")
    if swap_result == "decrease":
        issues.append("swap_decrease")
    if issues:
        status = "+".join(issues)
    elif swap is None:
        status = "skipped_after_shift"
    elif swap_result == "equal":
        status = "swap_equal"
    else:
        status = "ok"
    counterexample = bool(issues)

    parts = [f"shift {p_shifted - p_original:+.6f} (p {p_original:.6f} -> {p_shifted:.6f})"]
    if swap is None:
        parts.append("swap skipped: <2 incomplete layers after shift")
    else:
        removed_label = "(" + " AND ".join(map(str, _key_indices(swap["removed"]))) + ")"
        added_label = "(" + " AND ".join(map(str, _key_indices(swap["added"]))) + ")"
        parts.append(
            f"swap removed {removed_label} from layer {swap['first_k']}, "
            f"added {added_label} to layer {swap['last_k']}: "
            f"{p_swapped - p_shifted:+.6f} (p -> {p_swapped:.6f})"
        )
    message = (("COUNTEREXAMPLE [" + status + "] | ") if counterexample else "") + " | ".join(parts)

    final_wallet = swap["wallet"] if swap is not None else prep["shifted"]
    record = {
        "key_count": key_count,
        "probabilities": _probs_named(probs),
        "wallet": final_wallet,
        "wallet_pretty": wallet_enumerations.walletStrAscii(
            final_wallet, and_token="AND", or_token="OR"
        ),
        "original_wallet": prep["original"],
        "shifted_wallet": prep["shifted"],
        "removed": swap["removed"] if swap is not None else None,
        "added": swap["added"] if swap is not None else None,
        "first_k": swap["first_k"] if swap is not None else None,
        "last_k": swap["last_k"] if swap is not None else None,
        "p_original": p_original,
        "p_shifted": p_shifted,
        "p_swapped": p_swapped,
        "shift_delta": p_shifted - p_original,
        "swap_delta": (p_swapped - p_shifted) if p_swapped is not None else None,
        "shift_decreased": shift_decreased,
        "swap_result": swap_result,
        "status": status,
        "counterexample": counterexample,
        "message": message,
    }
    if swap is not None:
        record["highlight"] = {"removed": [swap["removed"]], "added": [swap["added"]]}
    return record


def run_layer_swap_experiment(
    *,
    key_count: int,
    wallet_count: int = 100,
    scenario_count: int = 10,
    psafe_min: float = 0.5,
    tol: float = 1e-12,
    seed: int = 0,
    out_dir: Path | None = None,
    verbose: bool = True,
) -> dict[str, Any]:
    """Run the shift + swap check for one key count and write result JSON files.

    Returns a summary dict with per-status counts and output file paths.
    """
    if psafe_min < 0.5:
        raise ValueError("psafe_min must be >= 0.5 for this experiment")
    if out_dir is None:
        out_dir = data_path("saved_lists")
    out_dir.mkdir(parents=True, exist_ok=True)

    rng = random.Random(seed * 1000 + key_count)
    scenarios = _random_scenarios(scenario_count, psafe_min, rng)
    wallets = generate_random_wallets(key_count, wallet_count, rng)
    preps = [_prepare_wallet(wallet, key_count) for wallet in wallets]

    records: list[dict[str, Any]] = []
    for probs in scenarios:
        states, state_probs = wallet_enumerations.enumerateStates(key_count, probs)
        owner_states, adv_states = wallet_enumerations.ownerAdvKeysFromStates(states)
        for prep in preps:
            records.append(
                _evaluate_case(
                    prep, key_count, probs, owner_states, adv_states, state_probs, tol
                )
            )

    counterexamples = [r for r in records if r["counterexample"]]
    all_file = out_dir / f"layer_swap_all_{key_count}keys.json"
    counter_file = out_dir / f"layer_swap_counterexamples_{key_count}keys.json"
    all_file.write_text(json.dumps(records, indent=2), encoding="utf-8")
    counter_file.write_text(json.dumps(counterexamples, indent=2), encoding="utf-8")

    status_counts: dict[str, int] = {}
    for record in records:
        status_counts[record["status"]] = status_counts.get(record["status"], 0) + 1

    if verbose:
        print()
        print(f"=== Layer swap experiment (key_count={key_count}) ===")
        print(f"random wallets with >=2 incomplete layers: {len(wallets)}")
        print(f"random scenarios (pLEAKED=0, pSAFE>{psafe_min}): {len(scenarios)}")
        print(f"cases checked: {len(records)}")
        for status in sorted(status_counts):
            print(f"  {status}: {status_counts[status]}")
        print(f"counterexamples: {len(counterexamples)}")
        if not counterexamples:
            print("No counterexample found - conjecture holds on tested inputs.")
        print(f"  {all_file}")
        print(f"  {counter_file}")

    return {
        "key_count": key_count,
        "cases": len(records),
        "status_counts": status_counts,
        "counterexample_count": len(counterexamples),
        "all_file": all_file,
        "counterexamples_file": counter_file,
    }


if __name__ == "__main__":
    summaries = []
    for n in range(5, 10):
        summaries.append(
            run_layer_swap_experiment(
                key_count=n,
                wallet_count=100,
                scenario_count=10,
                seed=0,
                verbose=True,
            )
        )

    print()
    print("=== Overall ===")
    total_counterexamples = 0
    first_counter_file: Path | None = None
    for summary in summaries:
        total_counterexamples += summary["counterexample_count"]
        if summary["counterexample_count"] and first_counter_file is None:
            first_counter_file = summary["counterexamples_file"]
        print(
            f"key_count={summary['key_count']}: {summary['cases']} cases, "
            f"{summary['counterexample_count']} counterexamples"
        )

    if first_counter_file is not None:
        from scripts.wallet_visualizer import run_visualizer_from_json

        run_visualizer_from_json(str(first_counter_file))
