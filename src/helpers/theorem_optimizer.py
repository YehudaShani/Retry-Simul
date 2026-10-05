"""Exact optimizer using the half-safe one-incomplete-layer theorem.

When ``p_SAFE > 1/2``, the theorem proved in
``COMPLETE_PROOF_INCOMPLETE_LAYERS.tex`` guarantees that some global optimum
has at most one incomplete rank.  Such a wallet is determined by either:

* a pure rank threshold; or
* a rank ``k`` and a nonempty proper subset of the ``k``-sets.

This module searches exactly that reduced family.  It never enumerates the
full set of monotone wallets and it uses integer arithmetic throughout, so
decimal and rational inputs produce an exact rational optimum.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
from math import comb, lcm
from numbers import Rational
from typing import Literal, Mapping

from .consts import LEAKED, LOST, SAFE, STOLEN, KeyStates


@dataclass(frozen=True)
class TheoremOptimizerResult:
    """One exact optimum in the theorem-reduced family."""

    key_count: int
    wallet: tuple[int, ...]
    success_probability: Fraction
    threshold: int | None
    incomplete_rank: int | None
    selected_rank_masks: tuple[int, ...]
    # Conceptual wallets in the theorem-reduced family.
    candidates_considered: int
    # Actual threshold/cardinality/Gray representatives visited by the search.
    search_states_evaluated: int
    # Ranks certified by the cut-field marginal bound without subset search.
    dominance_skipped_ranks: tuple[int, ...]
    # Remaining ranks collapsed to a cardinality scan because st = e*lost.
    cardinality_reduced_ranks: tuple[int, ...]
    generic_solver: str
    branch_nodes_visited: int
    branch_nodes_pruned: int
    gray_states_evaluated: int


def theorem_candidate_count(key_count: int) -> int:
    """Number of nonconstant labelled wallets with at most one incomplete rank.

    There are ``key_count`` pure thresholds.  At an incomplete rank ``k``, any
    nonempty proper subset of its ``C(n,k)`` sets may be selected.
    """

    if key_count <= 0:
        raise ValueError("key_count must be positive")
    return key_count + sum(
        (1 << comb(key_count, rank)) - 2 for rank in range(1, key_count)
    )


@lru_cache(maxsize=None)
def _layer_masks(key_count: int, rank: int) -> tuple[int, ...]:
    return tuple(
        mask for mask in range(1 << key_count) if mask.bit_count() == rank
    )


def wallet_for_one_incomplete_layer(
    key_count: int, rank: int, selected_rank_masks: tuple[int, ...] | list[int]
) -> tuple[int, ...]:
    """Return minimal DNF terms for the family selected at one rank.

    The resulting up-family contains exactly ``selected_rank_masks`` at
    ``rank``, no smaller sets, and every larger set.  Missing ``rank + 1``
    sets are added as minimal terms so the representation matches the rest of
    this repository.
    """

    if key_count <= 0:
        raise ValueError("key_count must be positive")
    if rank <= 0 or rank >= key_count:
        raise ValueError("rank must be in [1, key_count - 1]")

    layer = set(_layer_masks(key_count, rank))
    selected = set(selected_rank_masks)
    if not selected <= layer:
        raise ValueError("selected masks must all belong to the requested rank")

    next_terms = [
        mask
        for mask in _layer_masks(key_count, rank + 1)
        if not any((chosen & mask) == chosen for chosen in selected)
    ]
    return tuple(sorted(selected | set(next_terms)))


def _as_fraction(value: object) -> Fraction:
    # Treat a float as the decimal the caller wrote, not its binary expansion.
    if isinstance(value, float):
        return Fraction(str(value))
    if isinstance(value, Rational):
        return Fraction(value)
    return Fraction(value)  # Decimal and numeric strings are accepted too.


def _integer_probabilities(
    probabilities: Mapping[int, object],
) -> tuple[tuple[int, int, int, int], int]:
    if set(probabilities) != set(KeyStates):
        raise ValueError("probabilities must contain exactly the four key states")

    values = tuple(
        _as_fraction(probabilities[state])
        for state in (SAFE, STOLEN, LEAKED, LOST)
    )
    if any(value < 0 for value in values):
        raise ValueError("probabilities must be nonnegative")
    if sum(values) != 1:
        raise ValueError("probabilities must sum to one")

    denominator = 1
    for value in values:
        denominator = lcm(denominator, value.denominator)
    numerators = tuple(
        value.numerator * (denominator // value.denominator) for value in values
    )
    return numerators, denominator


def _rank_weight_matrix(
    key_count: int, numerators: tuple[int, int, int, int]
) -> list[list[int]]:
    """Integer weights of ``(|owner|, |attacker|)`` after ``key_count`` keys."""

    safe, stolen, leaked, lost = numerators
    weights = [[0] * (key_count + 1) for _ in range(key_count + 1)]
    weights[0][0] = 1
    for used in range(key_count):
        nxt = [[0] * (key_count + 1) for _ in range(key_count + 1)]
        for owner_rank in range(used + 1):
            for attacker_rank in range(used + 1):
                weight = weights[owner_rank][attacker_rank]
                if not weight:
                    continue
                nxt[owner_rank + 1][attacker_rank] += weight * safe
                nxt[owner_rank][attacker_rank + 1] += weight * stolen
                nxt[owner_rank + 1][attacker_rank + 1] += weight * leaked
                nxt[owner_rank][attacker_rank] += weight * lost
        weights = nxt
    return weights


def _threshold_score_numerator(
    rank_weights: list[list[int]], key_count: int, threshold: int
) -> int:
    return sum(
        rank_weights[owner_rank][attacker_rank]
        for owner_rank in range(threshold, key_count + 1)
        for attacker_rank in range(threshold)
    )


def _same_rank_kernel(
    key_count: int,
    rank: int,
    masks: tuple[int, ...],
    numerators: tuple[int, int, int, int],
) -> list[list[int]]:
    """K[A,B] = integer weight of the exact event ``O=A, D=B``."""

    safe, stolen, leaked, lost = numerators
    by_intersection = {
        intersection: (
            safe ** (rank - intersection)
            * stolen ** (rank - intersection)
            * leaked**intersection
            * lost ** (key_count - 2 * rank + intersection)
        )
        for intersection in range(max(0, 2 * rank - key_count), rank + 1)
    }
    return [
        [by_intersection[(left & right).bit_count()] for right in masks]
        for left in masks
    ]


def _top_prefix(values: list[int]) -> list[int]:
    """Prefix sums of values in descending order, starting with zero."""

    out = [0]
    for value in sorted(values, reverse=True):
        out.append(out[-1] + value)
    return out


def _mask_row_sum(row: list[int], mask: int, *, skip: int = -1) -> int:
    total = 0
    while mask:
        low = mask & -mask
        index = low.bit_length() - 1
        if index != skip:
            total += row[index]
        mask ^= low
    return total


def _weight_between(kernel: list[list[int]], left: int, right: int) -> int:
    total = 0
    while left:
        low = left & -left
        index = low.bit_length() - 1
        total += _mask_row_sum(kernel[index], right)
        left ^= low
    return total


def _comb_bound(
    kernel: list[list[int]], field: int, selected: int, rejected: int, undecided: int
) -> tuple[int, dict[int, int]]:
    """Cardinality-aware upper bound for a partial weighted-cut assignment.

    For each possible number ``r`` of undecided vertices ultimately selected,
    this is the minimum of three cut bounds supplied in the proof sketch, plus
    the better linear field value of the completion and its complement.
    """

    vertex_count = len(kernel)
    selected_count = selected.bit_count()
    baseline = _weight_between(kernel, selected, rejected) + _weight_between(
        kernel, selected, undecided
    )

    gains: list[int] = []
    deltas: list[int] = []
    delta_by_vertex: dict[int, int] = {}
    remaining = undecided
    while remaining:
        low = remaining & -remaining
        vertex = low.bit_length() - 1
        row = kernel[vertex]
        gain = _mask_row_sum(row, rejected) - _mask_row_sum(row, selected)
        delta = _mask_row_sum(row, undecided, skip=vertex)
        gains.append(gain)
        deltas.append(delta)
        delta_by_vertex[vertex] = delta
        remaining ^= low

    total_delta = sum(deltas)
    undecided_weight = total_delta // 2
    top_gain = _top_prefix(gains)
    top_gain_plus_delta = _top_prefix(
        [gain + delta for gain, delta in zip(gains, deltas)]
    )
    top_gain_minus_delta = _top_prefix(
        [gain - delta for gain, delta in zip(gains, deltas)]
    )

    best = -1
    for completion_size in range(len(gains) + 1):
        cut_gain = min(
            undecided_weight + top_gain[completion_size],
            top_gain_plus_delta[completion_size],
            total_delta + top_gain_minus_delta[completion_size],
        )
        final_size = selected_count + completion_size
        field_bound = max(field * final_size, field * (vertex_count - final_size))
        best = max(best, baseline + cut_gain + field_bound)
    return best, delta_by_vertex


def _solve_fixed_rank_branch(
    kernel: list[list[int]], field: int, incumbent: int | None
) -> tuple[int, int, int, int]:
    """Maximize ``field*|S| + cut(S,S^c)`` modulo complementation."""

    vertex_count = len(kernel)
    full = (1 << vertex_count) - 1

    # Empty/full are the threshold pair.  They provide a valid fixed-rank
    # incumbent even when the caller's global incumbent is stronger.
    if field * vertex_count > 0:
        best_value = field * vertex_count
        best_bits = full
    else:
        best_value = 0
        best_bits = 0
    pruning_floor = best_value if incumbent is None else max(best_value, incumbent)
    nodes_visited = 0
    nodes_pruned = 0

    def visit(selected: int, rejected: int, undecided: int) -> None:
        nonlocal best_value, best_bits, pruning_floor, nodes_visited, nodes_pruned
        nodes_visited += 1

        upper_bound, delta_by_vertex = _comb_bound(
            kernel, field, selected, rejected, undecided
        )
        if upper_bound <= pruning_floor:
            nodes_pruned += 1
            return

        if not undecided:
            cut = _weight_between(kernel, selected, rejected)
            selected_count = selected.bit_count()
            direct_field = field * selected_count
            complement_field = field * (vertex_count - selected_count)
            if direct_field >= complement_field:
                value = cut + direct_field
                bits = selected
            else:
                value = cut + complement_field
                bits = full ^ selected
            if value > best_value:
                best_value = value
                best_bits = bits
                pruning_floor = max(pruning_floor, value)
            return

        # High undecided weighted degree tends to expose the most bound slack.
        vertex = max(delta_by_vertex, key=delta_by_vertex.get)
        bit = 1 << vertex
        rest = undecided ^ bit

        row = kernel[vertex]
        gain_if_selected = (
            field
            + _mask_row_sum(row, rejected)
            - _mask_row_sum(row, selected)
        )
        if gain_if_selected >= 0:
            visit(selected | bit, rejected, rest)
            visit(selected, rejected | bit, rest)
        else:
            visit(selected, rejected | bit, rest)
            visit(selected | bit, rejected, rest)

    # Choose one representative per complementary pair by fixing vertex 0 in Q.
    anchor = 1
    visit(0, anchor, full ^ anchor)
    return best_value, best_bits, nodes_visited, nodes_pruned


def _solve_fixed_rank_gray(
    kernel: list[list[int]], field: int
) -> tuple[int, int, int]:
    """Exact complement-quotiented Gray fallback for one fixed rank."""

    layer_size = len(kernel)
    kernel_row_sum = sum(kernel[0])
    if any(sum(row) != kernel_row_sum for row in kernel[1:]):
        raise ArithmeticError("exchangeable same-rank kernel had unequal row sums")

    full_subset_bits = (1 << layer_size) - 1
    if field * layer_size > 0:
        best_value = field * layer_size
        best_bits = full_subset_bits
    else:
        best_value = 0
        best_bits = 0

    selected_row_sums = [0] * layer_size
    quadratic = 0
    selected_count = 0
    previous_gray = 0
    states_evaluated = 0

    for ordinal in range(1 << (layer_size - 1)):
        gray = ordinal ^ (ordinal >> 1)
        if ordinal:
            changed = gray ^ previous_gray
            bit = changed.bit_length() - 1
            row = kernel[bit]

            if gray & changed:
                quadratic += 2 * selected_row_sums[bit] + row[bit]
                for index in range(layer_size):
                    selected_row_sums[index] += row[index]
                selected_count += 1
            else:
                quadratic -= 2 * selected_row_sums[bit] - row[bit]
                for index in range(layer_size):
                    selected_row_sums[index] -= row[index]
                selected_count -= 1
            previous_gray = gray

        states_evaluated += 1
        cut = selected_count * kernel_row_sum - quadratic
        direct_value = field * selected_count + cut
        if direct_value > best_value:
            best_value = direct_value
            best_bits = gray

        complement_count = layer_size - selected_count
        complement_value = field * complement_count + cut
        if complement_value > best_value:
            best_value = complement_value
            best_bits = full_subset_bits ^ gray

    return best_value, best_bits, states_evaluated


def find_optimal_half_safe_wallet(
    key_count: int,
    probabilities: Mapping[int, object],
    *,
    solver: Literal["branch_and_bound", "gray"] = "branch_and_bound",
    cross_check_gray: bool = False,
) -> TheoremOptimizerResult:
    """Find an exact global optimum when ``p_SAFE > 1/2``.

    The search is exhaustive over the theorem-guaranteed canonical family, not
    over all monotone wallets.  For a fixed rank with ``L = C(n,k)`` sets, a
    cardinality-aware branch-and-bound is the default generic fixed-rank
    solver.  ``solver="gray"`` retains an exhaustive complement-quotiented
    Gray fallback, and ``cross_check_gray=True`` verifies every generic branch
    result against it.  On the determinant-zero surface ``st = e*lost``, all
    same-rank kernel entries agree and only the two integer cardinalities
    surrounding a concave quadratic's vertex need to be checked.
    """

    if key_count <= 0:
        raise ValueError("key_count must be positive")
    if solver not in ("branch_and_bound", "gray"):
        raise ValueError("solver must be 'branch_and_bound' or 'gray'")

    numerators, denominator = _integer_probabilities(probabilities)
    safe, _stolen, _leaked, _lost = numerators
    if 2 * safe <= denominator:
        raise ValueError("the theorem-aware optimizer requires p_SAFE > 1/2")

    rank_weights = _rank_weight_matrix(key_count, numerators)
    probability_denominator = denominator**key_count

    best_numerator = -1
    best_threshold: int | None = None
    best_rank: int | None = None
    best_subset_bits = 0
    search_states_evaluated = 0
    dominance_skipped_ranks: list[int] = []
    cardinality_reduced_ranks: list[int] = []
    branch_nodes_visited = 0
    branch_nodes_pruned = 0
    gray_states_evaluated = 0

    # Pure thresholds cover the zero-incomplete-layer cases.
    for threshold in range(1, key_count + 1):
        search_states_evaluated += 1
        score = _threshold_score_numerator(rank_weights, key_count, threshold)
        if score > best_numerator:
            best_numerator = score
            best_threshold = threshold
            best_rank = None
            best_subset_bits = 0

    # For rank k the variable part is the weighted-cut objective
    #   field * |S| + cut_K(S, S^c).
    for rank in range(1, key_count):
        masks = _layer_masks(key_count, rank)
        layer_size = len(masks)

        base = sum(
            rank_weights[owner_rank][attacker_rank]
            for owner_rank in range(rank + 1, key_count + 1)
            for attacker_rank in range(rank + 1)
        )
        owner_strict_boundary = sum(rank_weights[rank][:rank])
        attacker_boundary = sum(
            rank_weights[owner_rank][rank]
            for owner_rank in range(rank + 1, key_count + 1)
        )
        field_difference = owner_strict_boundary - attacker_boundary
        field, remainder = divmod(field_difference, layer_size)
        if remainder:
            raise ArithmeticError("exchangeable boundary weight was not rank-uniform")

        kernel_row_sum, remainder = divmod(
            rank_weights[rank][rank], layer_size
        )
        if remainder:
            raise ArithmeticError("exchangeable same-rank weight was not rank-uniform")
        diagonal = numerators[2] ** rank * numerators[3] ** (key_count - rank)
        off_diagonal_degree = kernel_row_sum - diagonal
        linear = field + kernel_row_sum

        # In cut form the variable part is
        #   field*|S| + cut_K(S, S^c).
        # Adding one vertex changes the cut by an amount in [-D,D], where D
        # is the uniform off-diagonal weighted degree.  A field outside that
        # interval makes the full or empty layer globally optimal at this rank.
        if field >= off_diagonal_degree or field <= -off_diagonal_degree:
            dominance_skipped_ranks.append(rank)
            continue

        # If st = e*lost, K[A,B] is constant for all pairs of k-sets:
        #   (st)^(k-h) e^h lost^(n-2k+h) = e^k lost^(n-k).
        # The objective therefore depends only on |S|.
        _safe, stolen, leaked, lost = numerators
        if safe * stolen == leaked * lost:
            cardinality_reduced_ranks.append(rank)
            kernel_value = leaked**rank * lost ** (key_count - rank)
            # The fixed-rank score is the concave integer quadratic
            #   base + linear*m - kernel_value*m^2.
            # Dominance above handles the zero-kernel case.  Otherwise its
            # maximum on 1 <= m < layer_size lies at one of the two integers
            # surrounding linear/(2*kernel_value), clipped to the interval.
            if kernel_value <= 0:
                raise ArithmeticError(
                    "zero determinant reached cardinality reduction with "
                    "a nonpositive kernel"
                )
            vertex_floor = linear // (2 * kernel_value)
            candidate_cardinalities = {
                max(1, min(layer_size - 1, vertex_floor)),
                max(1, min(layer_size - 1, vertex_floor + 1)),
            }
            for selected_count in sorted(candidate_cardinalities):
                search_states_evaluated += 1
                score = (
                    base
                    + linear * selected_count
                    - kernel_value * selected_count * selected_count
                )
                if score > best_numerator:
                    best_numerator = score
                    best_threshold = None
                    best_rank = rank
                    best_subset_bits = (1 << selected_count) - 1
            continue

        kernel = _same_rank_kernel(key_count, rank, masks, numerators)
        computed_row_sum = sum(kernel[0])
        if computed_row_sum != kernel_row_sum or any(
            sum(row) != kernel_row_sum for row in kernel[1:]
        ):
            raise ArithmeticError("exchangeable same-rank kernel had unequal row sums")

        if solver == "branch_and_bound":
            # A stronger global incumbent may deliberately prune a rank whose
            # local optimum cannot improve the final answer.  Cross-check mode
            # instead asks the branch solver for the exact local optimum.
            branch_incumbent = None if cross_check_gray else best_numerator - base
            variable_value, subset_bits, nodes, pruned = _solve_fixed_rank_branch(
                kernel, field, branch_incumbent
            )
            branch_nodes_visited += nodes
            branch_nodes_pruned += pruned
            search_states_evaluated += nodes

            if cross_check_gray:
                gray_value, _gray_bits, gray_states = _solve_fixed_rank_gray(
                    kernel, field
                )
                gray_states_evaluated += gray_states
                if gray_value != variable_value:
                    raise ArithmeticError(
                        "branch-and-bound and Gray fixed-rank optima disagree"
                    )
        else:
            variable_value, subset_bits, gray_states = _solve_fixed_rank_gray(
                kernel, field
            )
            gray_states_evaluated += gray_states
            search_states_evaluated += gray_states

        score = base + variable_value
        if score > best_numerator:
            best_numerator = score
            best_threshold = None
            best_rank = rank
            best_subset_bits = subset_bits

    if best_rank is None:
        assert best_threshold is not None
        wallet = _layer_masks(key_count, best_threshold)
        selected_masks: tuple[int, ...] = ()
    else:
        rank_masks = _layer_masks(key_count, best_rank)
        selected_masks = tuple(
            mask
            for index, mask in enumerate(rank_masks)
            if best_subset_bits & (1 << index)
        )
        wallet = wallet_for_one_incomplete_layer(
            key_count, best_rank, selected_masks
        )

    return TheoremOptimizerResult(
        key_count=key_count,
        wallet=wallet,
        success_probability=Fraction(best_numerator, probability_denominator),
        threshold=best_threshold,
        incomplete_rank=best_rank,
        selected_rank_masks=selected_masks,
        candidates_considered=theorem_candidate_count(key_count),
        search_states_evaluated=search_states_evaluated,
        dominance_skipped_ranks=tuple(dominance_skipped_ranks),
        cardinality_reduced_ranks=tuple(cardinality_reduced_ranks),
        generic_solver=solver,
        branch_nodes_visited=branch_nodes_visited,
        branch_nodes_pruned=branch_nodes_pruned,
        gray_states_evaluated=gray_states_evaluated,
    )
