from helpers import computations
from helpers.consts import SAFE
from helpers import wallet_enumerations
from helpers.wallet_cache import get_cached_static_wallets
from scripts.experiments.ittays_experiments import (
    find_lowest_psafe_where_symmetric_is_globally_optimal,
    _embed_wallet_skip_key,
    _build_extended_symmetric_candidates,
)


def test_psafe_threshold_logic_consistent_coarse_grid():
    # Coarse grid keeps test fast and deterministic.
    key_count = 3
    step = 0.5
    threshold, _examples = find_lowest_psafe_where_symmetric_is_globally_optimal(
        key_count=key_count,
        step=step,
        include_zero=True,
        deduplicate_by_architecture=True,
        max_failure_examples=0,
        verbose=False,
    )

    # If threshold is returned, it must actually satisfy the definition:
    # for all scenarios with pSAFE >= threshold, symmetric optimal is globally optimal (ties allowed).
    if threshold is None:
        return

    wallets = get_cached_static_wallets(key_count, deduplicate_by_architecture=True)
    scenarios = computations.generateKeyFaultProbabilityScenarios(step=step, include_zero=True)
    candidates = _build_extended_symmetric_candidates(key_count)
    for probs in scenarios:
        if probs[SAFE] < threshold:
            continue

        _optimal_wallets, best_p = computations.findOptimalWallet(wallets, key_count, probs)
        states, state_probabilities = wallet_enumerations.enumerateStates(key_count, probs)
        owner_states, adv_states = wallet_enumerations.ownerAdvKeysFromStates(states)

        best_sym_p = -1.0
        for cand in candidates:
            p = computations.computeSuccessProbability(
                list(cand), owner_states, adv_states, state_probabilities
            )
            best_sym_p = max(best_sym_p, p)

        assert abs(best_sym_p - best_p) <= 1e-12


def test_embed_wallet_skip_key():
    # Base wallet is W(3,2): (1&2) OR (1&3) OR (2&3)
    base = (0b011, 0b101, 0b110)

    # Embed into n=4 by skipping the last key (pos=3): should be unchanged.
    assert _embed_wallet_skip_key(base, 3) == base

    # Skip pos=1 (key 2): bits [0,1,2] -> [0,2,3]
    # 0b011 -> {0,1} -> {0,2} => 0b0101
    # 0b101 -> {0,2} -> {0,3} => 0b1001
    # 0b110 -> {1,2} -> {2,3} => 0b1100
    assert _embed_wallet_skip_key(base, 1) == (0b0101, 0b1001, 0b1100)
