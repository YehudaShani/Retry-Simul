from fractions import Fraction

import pytest

from helpers import computations, wallet_enumerations
from helpers.consts import LEAKED, LOST, SAFE, STOLEN
from helpers.symbols import success_probability_polynomial_coefficients
from helpers.theorem_optimizer import (
    _solve_fixed_rank_branch,
    _solve_fixed_rank_gray,
    find_optimal_half_safe_wallet,
    theorem_candidate_count,
    wallet_for_one_incomplete_layer,
)
from helpers.wallet_cache import get_cached_static_wallets


def _float_probabilities(probabilities):
    return {state: float(value) for state, value in probabilities.items()}


def _exact_wallet_score(key_count, wallet, probabilities):
    coefficients = success_probability_polynomial_coefficients(
        key_count, list(wallet)
    )
    return sum(
        coefficient
        * probabilities[SAFE] ** exponents[0]
        * probabilities[LOST] ** exponents[1]
        * probabilities[LEAKED] ** exponents[2]
        * probabilities[STOLEN] ** exponents[3]
        for exponents, coefficient in coefficients.items()
    )


def test_theorem_candidate_count_is_subsets_not_layer_size():
    assert [theorem_candidate_count(n) for n in range(1, 7)] == [
        1,
        4,
        15,
        94,
        2109,
        1114236,
    ]


def test_one_incomplete_layer_converts_to_minimal_terms():
    # At rank 2, authorize only {1,2}; all triples must nevertheless be full.
    # The missing triples {1,3,4} and {2,3,4} therefore become minimal terms.
    assert wallet_for_one_incomplete_layer(4, 2, (0b0011,)) == (
        0b0011,
        0b1101,
        0b1110,
    )


def test_known_nonsymmetric_half_safe_optimum_is_found_exactly():
    probabilities = {
        SAFE: Fraction(11, 20),
        LOST: Fraction(0),
        LEAKED: Fraction(1, 5),
        STOLEN: Fraction(1, 4),
    }

    result = find_optimal_half_safe_wallet(3, probabilities)

    assert result.success_probability == Fraction(4609, 8000)
    assert result.incomplete_rank == 2
    assert len(result.selected_rank_masks) == 2
    assert wallet_enumerations.canonicalizeWallet(list(result.wallet), 3) == (
        0b011,
        0b101,
    )


def test_genuine_weighted_cut_optimum_is_found_exactly():
    # Intersecting and disjoint pairs have different weights here, so this
    # exercises the generic Johnson-weighted cut rather than a shortcut.
    probabilities = {
        SAFE: Fraction(11, 20),
        LOST: Fraction(1, 5),
        LEAKED: Fraction(1, 5),
        STOLEN: Fraction(1, 20),
    }

    result = find_optimal_half_safe_wallet(4, probabilities, solver="gray")

    assert result.success_probability == Fraction(11319, 16000)
    assert result.incomplete_rank == 2
    assert len(result.selected_rank_masks) == 3
    assert result.threshold is None


@pytest.mark.parametrize("key_count", range(1, 6))
def test_matches_existing_exhaustive_optimizer(key_count):
    probabilities = {
        SAFE: Fraction(3, 5),
        LOST: Fraction(1, 10),
        LEAKED: Fraction(1, 10),
        STOLEN: Fraction(1, 5),
    }
    result = find_optimal_half_safe_wallet(key_count, probabilities)
    assert _exact_wallet_score(
        key_count, result.wallet, probabilities
    ) == result.success_probability

    wallets = get_cached_static_wallets(key_count, deduplicate_by_architecture=True)
    _best_wallets, exhaustive_score = computations.findOptimalWallet(
        wallets, key_count, _float_probabilities(probabilities)
    )

    assert float(result.success_probability) == pytest.approx(exhaustive_score)

    states, state_probabilities = wallet_enumerations.enumerateStates(
        key_count, _float_probabilities(probabilities)
    )
    owner_states, attacker_states = wallet_enumerations.ownerAdvKeysFromStates(states)
    result_score = computations.computeSuccessProbability(
        list(result.wallet), owner_states, attacker_states, state_probabilities
    )
    assert result_score == pytest.approx(exhaustive_score)


def test_complement_quotient_halves_each_generic_rank_search():
    probabilities = {
        SAFE: Fraction(3, 5),
        LOST: Fraction(1, 10),
        LEAKED: Fraction(1, 10),
        STOLEN: Fraction(1, 5),
    }

    result = find_optimal_half_safe_wallet(4, probabilities, solver="gray")

    assert result.dominance_skipped_ranks == (1, 3)
    # Four thresholds; ranks 1 and 3 are field-dominated, while rank 2 uses
    # one representative from each complementary pair of its 2^6 subsets.
    assert result.candidates_considered == 94
    assert result.search_states_evaluated == 4 + 2**5
    assert result.gray_states_evaluated == 2**5
    assert result.branch_nodes_visited == 0


def test_branch_and_bound_matches_gray_and_prunes_at_n6():
    probabilities = {
        SAFE: Fraction(3, 5),
        LOST: Fraction(1, 10),
        LEAKED: Fraction(1, 10),
        STOLEN: Fraction(1, 5),
    }

    branch = find_optimal_half_safe_wallet(
        6, probabilities, cross_check_gray=True
    )
    gray = find_optimal_half_safe_wallet(6, probabilities, solver="gray")

    assert branch.success_probability == gray.success_probability
    assert branch.branch_nodes_visited > 0
    assert branch.branch_nodes_pruned > 0
    assert branch.gray_states_evaluated == gray.gray_states_evaluated
    assert branch.branch_nodes_visited < gray.gray_states_evaluated


def test_external_global_incumbent_may_prune_a_weaker_fixed_rank():
    # This models a prior threshold/rank score already above this rank's local
    # optimum.  Such pruning is valid globally but must be disabled for a local
    # Gray cross-check.
    kernel = [
        [0, 3, 2, 1],
        [3, 0, 1, 2],
        [2, 1, 0, 3],
        [1, 2, 3, 0],
    ]
    gray_value, _gray_bits, _gray_states = _solve_fixed_rank_gray(kernel, 0)
    pruned_value, _bits, _nodes, pruned = _solve_fixed_rank_branch(
        kernel, 0, gray_value + 1
    )
    exact_value, _bits, _nodes, _pruned = _solve_fixed_rank_branch(
        kernel, 0, None
    )

    assert pruned
    assert pruned_value < gray_value
    assert exact_value == gray_value


def test_determinant_zero_surface_searches_only_cardinalities():
    # safe*stolen == leaked*lost == 16/625.
    probabilities = {
        SAFE: Fraction(16, 25),
        LOST: Fraction(4, 25),
        LEAKED: Fraction(4, 25),
        STOLEN: Fraction(1, 25),
    }

    result = find_optimal_half_safe_wallet(4, probabilities)
    wallets = get_cached_static_wallets(4, deduplicate_by_architecture=True)
    _best_wallets, exhaustive_score = computations.findOptimalWallet(
        wallets, 4, _float_probabilities(probabilities)
    )

    assert result.cardinality_reduced_ranks
    # Four thresholds plus at most the floor/ceiling around the concave
    # cardinality quadratic's real-valued vertex for every reduced rank.
    assert result.search_states_evaluated <= 4 + 2 * len(
        result.cardinality_reduced_ranks
    )
    assert float(result.success_probability) == pytest.approx(exhaustive_score)


def test_cut_field_dominance_can_skip_entire_ranks():
    probabilities = {
        SAFE: Fraction(9, 10),
        LOST: Fraction(1, 20),
        LEAKED: Fraction(1, 50),
        STOLEN: Fraction(3, 100),
    }

    result = find_optimal_half_safe_wallet(4, probabilities)

    assert result.dominance_skipped_ranks
    assert result.search_states_evaluated < 4 + 2**3 + 2**5 + 2**3


@pytest.mark.parametrize(
    "probabilities",
    [
        {SAFE: 0.5, LOST: 0.2, LEAKED: 0.1, STOLEN: 0.2},
        {SAFE: 0.4, LOST: 0.2, LEAKED: 0.1, STOLEN: 0.3},
    ],
)
def test_rejects_probabilities_outside_the_proved_region(probabilities):
    with pytest.raises(ValueError, match="p_SAFE > 1/2"):
        find_optimal_half_safe_wallet(3, probabilities)
