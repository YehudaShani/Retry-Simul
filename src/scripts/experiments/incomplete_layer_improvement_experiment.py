"""Test: when pLEAKED=0 and pSAFE>0.5, wallets with >1 incomplete layer can be improved.

Layer completeness is defined by COVERAGE (matching the visualizer): a combination in
popcount layer k counts as "present" if it is covered by some wallet term (isCovered),
not merely if it is listed explicitly. A layer is incomplete when some but not all of its
C(n, k) combinations are covered.

For a wallet with >1 incomplete layer, at least one of these edits should strictly increase
success probability:
  1. Remove the whole first incomplete layer (lowest incomplete k): toggle off every covered
     combination in that layer via ``remove_bitmask_and_subsets`` (same as the visualizer).
  2. Complete the whole last incomplete layer (highest incomplete k): add every uncovered
     combination in that layer via ``add_bitmask`` (same as "Add all" in the visualizer).
  3. Do both edits.
"""
import json
import random
import sys
from pathlib import Path
from typing import Any

for _src in Path(__file__).resolve().parents:
    if (_src / "helpers").is_dir() and (_src / "scripts").is_dir():
        if str(_src) not in sys.path:
            sys.path.insert(0, str(_src))
        break

from helpers import computations, wallet_enumerations
from helpers.consts import KeyStates, KeyStateString, LEAKED, LOST, SAFE, STOLEN
from helpers.paths import data_path
from helpers.wallet_cache import get_cached_static_wallets
from helpers.wallet_enumerations import isCovered
from helpers.wallet_state import WalletState

from scripts.experiments.incomplete_layers_experiment import layer_bitmasks

EDIT_NAMES = ("remove_first", "complete_last", "both")
EDIT_BUCKETS = ("remove_first", "complete_last", "both", "none")


def _edit_files(file_suffix: str = "") -> dict[str, str]:
    """Per-edit log file names, optionally suffixed (e.g. '_6keys')."""
    return {bucket: f"layer_edit_{bucket}{file_suffix}.json" for bucket in EDIT_BUCKETS}


def covered_in_layer(wallet: list[int], key_count: int, k: int) -> set[int]:
    """Combinations in popcount layer k that are covered by the wallet."""
    return {c for c in layer_bitmasks(key_count, k) if isCovered(c, wallet)}


def incomplete_layer_ks(wallet: list[int], key_count: int) -> list[int]:
    """Popcount layers that are partially covered (some but not all combos), ascending.

    Completeness is coverage-based: a layer is complete when every one of its C(n, k)
    combinations is covered by some wallet term.
    """
    result = []
    for k in range(1, key_count + 1):
        layer = layer_bitmasks(key_count, k)
        covered = covered_in_layer(wallet, key_count, k)
        if covered and covered != layer:
            result.append(k)
    return result


def count_incomplete_layers(wallet: list[int], key_count: int) -> int:
    return len(incomplete_layer_ks(wallet, key_count))


def wallets_with_many_incomplete_layers(
    wallets: list[list[int]], key_count: int, *, min_incomplete: int = 2
) -> list[tuple[list[int], int]]:
    """(wallet, incomplete_layer_count) for wallets with >1 incomplete (coverage) layer."""
    result = []
    for wallet in wallets:
        incomplete = count_incomplete_layers(wallet, key_count)
        if incomplete >= min_incomplete:
            result.append((wallet, incomplete))
    return result


def shifted_wallet(wallet: list[int], key_count: int) -> list[int]:
    """Return the wallet after applying the combinatorial down-shift (compression)."""
    return sorted(_wallet_for_edits(wallet, key_count).shift().bitmasks)


def shifted_target_wallets(
    wallets: list[list[int]], key_count: int, *, min_incomplete: int = 2
) -> list[tuple[list[int], int]]:
    """Shift each wallet first, dedup, then keep those with >1 incomplete (coverage) layer.

    Because the shift canonicalizes many distinct static wallets onto the same shifted
    form, results are deduplicated by their shifted bitmask tuple.
    """
    seen: set[tuple[int, ...]] = set()
    result: list[tuple[list[int], int]] = []
    for wallet in wallets:
        shifted = shifted_wallet(wallet, key_count)
        key = tuple(shifted)
        if key in seen:
            continue
        seen.add(key)
        incomplete = count_incomplete_layers(shifted, key_count)
        if incomplete >= min_incomplete:
            result.append((shifted, incomplete))
    return result


def _wallet_for_edits(wallet: list[int], key_count: int) -> WalletState:
    """WalletState for bitmask edits; probabilities are unused by edit methods."""
    return WalletState(key_count, list(wallet), {SAFE: 0.25, LOST: 0.25, LEAKED: 0.25, STOLEN: 0.25})


def remove_incomplete_layer(wallet: list[int], key_count: int, k: int) -> list[int]:
    """Toggle off every covered combination in layer k (visualizer semantics)."""
    ws = _wallet_for_edits(wallet, key_count)
    for combo in sorted(layer_bitmasks(key_count, k)):
        if ws.bitmask_is_in_wallet(combo):
            ws.remove_bitmask_and_subsets(combo)
    return sorted(ws.bitmasks)


def complete_layer(wallet: list[int], key_count: int, k: int) -> list[int]:
    """Add every uncovered combination in layer k (visualizer "Add all")."""
    ws = _wallet_for_edits(wallet, key_count)
    for combo in sorted(layer_bitmasks(key_count, k)):
        if not ws.bitmask_is_in_wallet(combo):
            ws.add_bitmask(combo)
    return sorted(ws.bitmasks)


def layer_edit_variants(wallet: list[int], key_count: int) -> dict[str, list[int] | None]:
    """Return the three improvement candidates, or None if not applicable."""
    incomplete = incomplete_layer_ks(wallet, key_count)
    if len(incomplete) < 2:
        return {
            "remove_first": None,
            "complete_last": None,
            "both": None,
            "first_k": None,
            "last_k": None,
        }

    first_k = incomplete[0]
    last_k = incomplete[-1]

    removed_first = remove_incomplete_layer(wallet, key_count, first_k)
    completed_last = complete_layer(wallet, key_count, last_k)
    both = complete_layer(removed_first, key_count, last_k)

    return {
        "remove_first": removed_first,
        "complete_last": completed_last,
        "both": both,
        "first_k": first_k,
        "last_k": last_k,
    }


def _wallet_success(
    wallet: list[int],
    owner_states,
    adv_states,
    state_probs,
) -> float:
    return computations.computeSuccessProbability(
        wallet, owner_states, adv_states, state_probs
    )


def check_incomplete_layers_improvable_by_layer_edit(
    *,
    key_count: int = 5,
    step: float = 0.02,
    psafe_min: float = 0.5,
    tol: float = 1e-12,
    deduplicate_by_architecture: bool = True,
    max_counterexamples: int = 5,
    shift_wallets: bool = False,
    verbose: bool = True,
    quiet: bool = False,
) -> list[dict[str, Any]]:
    """Search for counterexamples to the layer-edit improvement theory.

    Theory: for every scenario with pLEAKED=0 and pSAFE > psafe_min, every wallet
    with >1 incomplete layer is strictly improved by at least one of:
      - removing the first incomplete layer
      - completing the last incomplete layer
      - doing both

    When ``shift_wallets`` is True, each static wallet is first canonicalized via the
    combinatorial down-shift and the whole theory is evaluated on that shifted wallet.

    Returns counterexample dicts (empty if theory holds on tested inputs).
    """
    if psafe_min < 0.5:
        raise ValueError("psafe_min must be >= 0.5 for this experiment")

    scenarios = [
        p
        for p in computations.generateKeyFaultProbabilityScenarios(step=step)
        if p[SAFE] > psafe_min and p[LEAKED] == 0.0
    ]
    wallets = get_cached_static_wallets(
        key_count, deduplicate_by_architecture=deduplicate_by_architecture
    )
    if shift_wallets:
        target_wallets = shifted_target_wallets(wallets, key_count)
    else:
        target_wallets = wallets_with_many_incomplete_layers(wallets, key_count)

    counterexamples: list[dict[str, Any]] = []
    checks = 0

    for probs in scenarios:
        states, state_probs = wallet_enumerations.enumerateStates(key_count, probs)
        owner_states, adv_states = wallet_enumerations.ownerAdvKeysFromStates(states)

        # Best achievable success over all static wallets in this scenario. A wallet that
        # already attains this cannot be improved, so the claim does not apply to it.
        best_overall = max(
            _wallet_success(w, owner_states, adv_states, state_probs) for w in wallets
        )

        for wallet, incomplete in target_wallets:
            checks += 1
            wallet_p = _wallet_success(wallet, owner_states, adv_states, state_probs)

            # Skip wallets that are already (globally) optimal: nothing can improve them.
            if wallet_p >= best_overall - tol:
                continue

            variants = layer_edit_variants(wallet, key_count)

            variant_results: dict[str, float | None] = {}
            for name in ("remove_first", "complete_last", "both"):
                candidate = variants[name]
                if candidate is None:
                    variant_results[name] = None
                    continue
                variant_results[name] = _wallet_success(
                    candidate, owner_states, adv_states, state_probs
                )

            best_variant = max(
                (p for p in variant_results.values() if p is not None),
                default=-1.0,
            )

            if best_variant <= wallet_p + tol:
                counterexamples.append(
                    {
                        "probabilities": probs,
                        "pSAFE": probs[SAFE],
                        "pLEAKED": probs[LEAKED],
                        "wallet": list(wallet),
                        "wallet_p": wallet_p,
                        "best_overall_p": best_overall,
                        "incomplete_layers": incomplete,
                        "first_k": variants["first_k"],
                        "last_k": variants["last_k"],
                        "remove_first_wallet": variants["remove_first"],
                        "complete_last_wallet": variants["complete_last"],
                        "both_wallet": variants["both"],
                        "remove_first_p": variant_results["remove_first"],
                        "complete_last_p": variant_results["complete_last"],
                        "both_p": variant_results["both"],
                        "wallet_pretty": wallet_enumerations.walletStrAscii(
                            wallet, and_token="AND", or_token="OR"
                        ),
                    }
                )
                if verbose and not quiet:
                    print("Counterexample found.")
                    print(f"  pSAFE={probs[SAFE]}, pLEAKED={probs[LEAKED]}")
                    print(f"  incomplete_layers={incomplete}, first_k={variants['first_k']}, last_k={variants['last_k']}")
                    print(f"  wallet_p={wallet_p} (best_overall={best_overall})")
                    print(f"  remove_first_p={variant_results['remove_first']}")
                    print(f"  complete_last_p={variant_results['complete_last']}")
                    print(f"  both_p={variant_results['both']}")
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


def _probs_named(probs: dict[int, float]) -> dict[str, float]:
    return {KeyStateString[k]: probs[k] for k in KeyStates}


def _subset_files(file_suffix: str = "") -> dict[frozenset[str], str]:
    """Single-edit subset file names, optionally suffixed (e.g. '_6keys')."""
    return {
        frozenset(["remove_first"]): f"layer_edit_only_remove_first{file_suffix}.json",
        frozenset(["complete_last"]): f"layer_edit_only_complete_last{file_suffix}.json",
        frozenset(["both"]): f"layer_edit_only_both{file_suffix}.json",
    }


def _improving_set(record: dict[str, Any]) -> frozenset[str]:
    return frozenset(
        name for name, info in record["edits"].items() if info.get("improves")
    )


def split_logged_records_by_improving_set(
    *, out_dir: Path | None = None, file_suffix: str = "", verbose: bool = True
) -> dict[str, int]:
    """Read the per-edit log files and write subset files by exactly-which-edits-improve.

    Produces one file per single-edit subset (only remove_first / only complete_last /
    only both). Deduplicates the (scenario, wallet) records that overlap across the
    per-edit log files. Requires ``classify_and_log_layer_edits`` to have been run first
    with the same ``file_suffix``.
    """
    if out_dir is None:
        out_dir = data_path("saved_lists")

    edit_files = _edit_files(file_suffix)
    subset_files = _subset_files(file_suffix)

    seen: dict[tuple, dict[str, Any]] = {}
    for file_name in edit_files.values():
        path = out_dir / file_name
        if not path.exists():
            continue
        for record in json.loads(path.read_text(encoding="utf-8")):
            key = (
                tuple(sorted(record["probabilities"].items())),
                tuple(record["wallet"]),
            )
            seen[key] = record

    subsets: dict[frozenset[str], list[dict[str, Any]]] = {
        combo: [] for combo in subset_files
    }
    for record in seen.values():
        improving = _improving_set(record)
        if improving in subsets:
            subsets[improving].append(record)

    counts: dict[str, int] = {}
    for combo, file_name in subset_files.items():
        path = out_dir / file_name
        path.write_text(json.dumps(subsets[combo], indent=2), encoding="utf-8")
        counts[file_name] = len(subsets[combo])

    if verbose:
        print()
        print("=== Single-edit subset files ===")
        print(f"unique (scenario, wallet) records read: {len(seen)}")
        for _combo, file_name in subset_files.items():
            print(f"  {file_name}: {counts[file_name]} records")
        print(f"output dir: {out_dir}")

    return counts


def _random_scenarios(
    count: int, psafe_min: float, rng: random.Random
) -> list[dict[int, float]]:
    """Random probability scenarios with pLEAKED=0 and pSAFE > psafe_min.

    pSAFE is uniform in (psafe_min, 1]; the remaining mass is split between pLOST and
    pSTOLEN. pSAFE > pSTOLEN holds automatically because pSTOLEN <= 1 - pSAFE < pSAFE.
    """
    scenarios: list[dict[int, float]] = []
    for _ in range(count):
        psafe = round(rng.uniform(psafe_min, 1.0), 6)
        if psafe <= psafe_min:
            psafe = round(min(1.0, psafe_min + 1e-6), 6)
        remaining = max(0.0, 1.0 - psafe)
        pstolen = round(rng.uniform(0.0, remaining), 6)
        plost = 1.0 - psafe - pstolen
        if plost < 0.0:
            plost = 0.0
        scenarios.append({SAFE: psafe, LOST: plost, LEAKED: 0.0, STOLEN: pstolen})
    return scenarios


def classify_and_log_layer_edits(
    *,
    key_count: int = 5,
    step: float = 0.02,
    psafe_min: float = 0.5,
    tol: float = 1e-12,
    deduplicate_by_architecture: bool = True,
    sample_per_scenario: tuple[int, int] | None = None,
    compute_best_overall: bool = True,
    random_scenarios: int | None = None,
    seed: int = 0,
    shift_wallets: bool = False,
    file_suffix: str = "",
    out_dir: Path | None = None,
    verbose: bool = True,
) -> dict[str, int]:
    """Log (wallet, scenario) pairs with >1 incomplete layer into per-edit JSON files.

    For each scenario with pLEAKED=0 and pSAFE > psafe_min, and each targeted wallet with
    >1 incomplete (coverage) layer, we test the three edits (remove first incomplete layer,
    complete last incomplete layer, both). A record is written into EACH file whose edit
    strictly improves success, with a message listing all beneficial edits. Wallets that no
    edit improves go to ``layer_edit_none{file_suffix}.json``.

    Scenario source:
      - ``random_scenarios=N``: N random continuous scenarios (better spread; good for
        hunting counterexamples).
      - otherwise: the exact integer grid from ``generateKeyFaultProbabilityScenarios(step)``.

    Wallet sampling:
      - ``sample_per_scenario=(lo, hi)``: for each scenario, sample a random count in
        [lo, hi] of the target wallets (fresh per scenario). Otherwise use all targets.

    ``compute_best_overall`` toggles the (expensive) global-optimum pass; when False the
    ``best_overall_p``/``already_optimal`` fields are omitted and we cannot label a
    no-improvement case as optimal vs. a genuine counterexample.

    Returns a dict of {bucket_name: record_count}.
    """
    if psafe_min < 0.5:
        raise ValueError("psafe_min must be >= 0.5 for this experiment")
    if out_dir is None:
        out_dir = data_path("saved_lists")
    out_dir.mkdir(parents=True, exist_ok=True)

    rng = random.Random(seed)

    if random_scenarios is not None:
        scenarios = _random_scenarios(random_scenarios, psafe_min, rng)
        scenario_desc = f"{random_scenarios} random scenarios (pLEAKED=0, pSAFE>{psafe_min})"
    else:
        scenarios = [
            p
            for p in computations.generateKeyFaultProbabilityScenarios(step=step)
            if p[SAFE] > psafe_min and p[LEAKED] == 0.0
        ]
        scenario_desc = f"grid step={step} (pLEAKED=0, pSAFE>{psafe_min})"

    wallets = get_cached_static_wallets(
        key_count, deduplicate_by_architecture=deduplicate_by_architecture
    )
    if shift_wallets:
        target_wallets = shifted_target_wallets(wallets, key_count)
        scenario_desc += " | wallets shifted (compression) first"
    else:
        target_wallets = wallets_with_many_incomplete_layers(wallets, key_count)

    edit_files = _edit_files(file_suffix)
    buckets: dict[str, list[dict[str, Any]]] = {name: [] for name in edit_files}

    for probs in scenarios:
        states, state_probs = wallet_enumerations.enumerateStates(key_count, probs)
        owner_states, adv_states = wallet_enumerations.ownerAdvKeysFromStates(states)

        best_overall: float | None = None
        if compute_best_overall:
            best_overall = max(
                _wallet_success(w, owner_states, adv_states, state_probs) for w in wallets
            )

        if sample_per_scenario is not None and target_wallets:
            lo, hi = sample_per_scenario
            hi = min(hi, len(target_wallets))
            lo = min(max(1, lo), hi)
            chosen = rng.sample(target_wallets, rng.randint(lo, hi))
        else:
            chosen = target_wallets

        for wallet, incomplete in chosen:
            wallet_p = _wallet_success(wallet, owner_states, adv_states, state_probs)
            variants = layer_edit_variants(wallet, key_count)

            edits: dict[str, dict[str, Any]] = {}
            improving: list[str] = []
            for name in EDIT_NAMES:
                candidate = variants[name]
                if candidate is None:
                    continue
                cand_p = _wallet_success(candidate, owner_states, adv_states, state_probs)
                improves = cand_p > wallet_p + tol
                edits[name] = {
                    "wallet": candidate,
                    "p": cand_p,
                    "delta": cand_p - wallet_p,
                    "improves": improves,
                }
                if improves:
                    improving.append(name)

            already_optimal = (
                best_overall is not None and wallet_p >= best_overall - tol
            )
            best_str = (
                f" best_overall={best_overall:.6f}" if best_overall is not None else ""
            )

            if improving:
                benefit_str = ", ".join(
                    f"{name}(+{edits[name]['delta']:.6f})" for name in improving
                )
                message = (
                    f"beneficial edits: {benefit_str} | first_k={variants['first_k']} "
                    f"last_k={variants['last_k']} | wallet_p={wallet_p:.6f}{best_str}"
                )
            elif already_optimal:
                message = (
                    f"no improving edit (already globally optimal) | "
                    f"first_k={variants['first_k']} last_k={variants['last_k']} | "
                    f"wallet_p={wallet_p:.6f}{best_str}"
                )
            elif best_overall is not None:
                message = (
                    f"NO IMPROVING EDIT but SUBOPTIMAL (counterexample!) | "
                    f"first_k={variants['first_k']} last_k={variants['last_k']} | "
                    f"wallet_p={wallet_p:.6f}{best_str}"
                )
            else:
                message = (
                    f"no improving edit (global optimum not computed) | "
                    f"first_k={variants['first_k']} last_k={variants['last_k']} | "
                    f"wallet_p={wallet_p:.6f}"
                )

            record = {
                "key_count": key_count,
                "shifted": shift_wallets,
                "probabilities": _probs_named(probs),
                "wallet": list(wallet),
                "wallet_pretty": wallet_enumerations.walletStrAscii(
                    wallet, and_token="AND", or_token="OR"
                ),
                "wallet_p": wallet_p,
                "best_overall_p": best_overall,
                "already_optimal": already_optimal if best_overall is not None else None,
                "incomplete_layers": incomplete,
                "first_k": variants["first_k"],
                "last_k": variants["last_k"],
                "edits": {
                    name: {
                        "wallet": info["wallet"],
                        "p": info["p"],
                        "delta": info["delta"],
                        "improves": info["improves"],
                    }
                    for name, info in edits.items()
                },
                "message": message,
            }

            if improving:
                for name in improving:
                    buckets[name].append(record)
            else:
                buckets["none"].append(record)

    counts: dict[str, int] = {}
    for bucket_name, file_name in edit_files.items():
        path = out_dir / file_name
        with open(path, "w", encoding="utf-8") as f:
            json.dump(buckets[bucket_name], f, indent=2)
        counts[bucket_name] = len(buckets[bucket_name])

    if verbose:
        print()
        print("=== Layer-edit classification logged ===")
        print(f"key_count={key_count}, {scenario_desc}")
        print(f"scenarios: {len(scenarios)}")
        print(f"wallets with >1 incomplete layer: {len(target_wallets)}")
        if sample_per_scenario is not None:
            print(f"sampled per scenario: {sample_per_scenario[0]}-{sample_per_scenario[1]}")
        for bucket_name, file_name in edit_files.items():
            print(f"  {file_name}: {counts[bucket_name]} records")
        if compute_best_overall:
            suboptimal_none = sum(1 for r in buckets["none"] if r.get("already_optimal") is False)
            print(f"suboptimal wallets with NO improving edit (real counterexamples): {suboptimal_none}")
        else:
            print(f"no-improvement cases (optimum not computed): {counts['none']}")
        print(f"output dir: {out_dir}")

    return counts


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
    print("=== Incomplete layer edit improvement (pLEAKED=0) ===")
    print(f"key_count={key_count}, step={step}, psafe_min={psafe_min}")
    print(f"scenarios tested (pLEAKED=0, pSAFE>{psafe_min}): {scenario_count}")
    print(f"static wallets: {wallet_count}")
    print(f"wallets with >1 incomplete layer: {target_wallet_count}")
    print(f"wallet-scenario checks: {checks}")
    print(f"counterexamples: {len(counterexamples)}")
    if not counterexamples:
        print("No counterexample found — theory holds on this grid.")


if __name__ == "__main__":
    # Shifted runs: canonicalize each static wallet with the combinatorial down-shift
    # (compression) BEFORE checking the remove-first / complete-last / both theory.

    # 5-key lists: full integer grid with the global-optimum pass, so no-improvement
    # cases can be labeled optimal vs. genuine counterexample.
    classify_and_log_layer_edits(
        key_count=5,
        step=0.02,
        psafe_min=0.5,
        compute_best_overall=True,
        shift_wallets=True,
        file_suffix="_shifted",
        verbose=True,
    )
    split_logged_records_by_improving_set(file_suffix="_shifted", verbose=True)

    # 6-key lists: random continuous scenarios (better spread to hunt for counterexamples),
    # sampling 10-20 target wallets per scenario, and no global-optimum pass.
    classify_and_log_layer_edits(
        key_count=6,
        psafe_min=0.5,
        random_scenarios=1275,
        sample_per_scenario=(10, 20),
        compute_best_overall=False,
        seed=0,
        shift_wallets=True,
        file_suffix="_shifted_6keys",
        verbose=True,
    )
    split_logged_records_by_improving_set(file_suffix="_shifted_6keys", verbose=True)
