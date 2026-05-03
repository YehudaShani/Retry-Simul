import pytest

from retry_simul.consts import LEAKED, LOST, SAFE, STOLEN
from scripts.wallet_visualizer import redistribute_probability_change


def assert_probabilities_sum_to_one(probabilities: dict[int, float]) -> None:
    assert sum(probabilities.values()) == pytest.approx(1.0)


def test_redistributes_increase_equally_across_all_other_checked_states():
    probabilities = {SAFE: 0.25, LOST: 0.25, LEAKED: 0.25, STOLEN: 0.25}

    updated, changed = redistribute_probability_change(
        probabilities,
        SAFE,
        0.40,
        {SAFE, LOST, LEAKED, STOLEN},
    )

    assert changed
    assert updated[SAFE] == pytest.approx(0.40)
    assert updated[LOST] == pytest.approx(0.20)
    assert updated[LEAKED] == pytest.approx(0.20)
    assert updated[STOLEN] == pytest.approx(0.20)
    assert_probabilities_sum_to_one(updated)


def test_redistributes_only_within_checked_group():
    probabilities = {SAFE: 0.40, LOST: 0.20, LEAKED: 0.10, STOLEN: 0.30}

    updated, changed = redistribute_probability_change(
        probabilities,
        SAFE,
        0.55,
        {SAFE, STOLEN},
    )

    assert changed
    assert updated[SAFE] == pytest.approx(0.55)
    assert updated[STOLEN] == pytest.approx(0.15)
    assert updated[LOST] == pytest.approx(probabilities[LOST])
    assert updated[LEAKED] == pytest.approx(probabilities[LEAKED])
    assert_probabilities_sum_to_one(updated)


def test_unchecked_changed_state_does_not_move():
    probabilities = {SAFE: 0.40, LOST: 0.20, LEAKED: 0.10, STOLEN: 0.30}

    updated, changed = redistribute_probability_change(
        probabilities,
        SAFE,
        0.55,
        {LOST, STOLEN},
    )

    assert not changed
    assert updated == probabilities


def test_clamps_before_any_probability_goes_negative():
    probabilities = {SAFE: 0.25, LOST: 0.05, LEAKED: 0.35, STOLEN: 0.35}

    updated, changed = redistribute_probability_change(
        probabilities,
        SAFE,
        0.70,
        {SAFE, LOST, LEAKED, STOLEN},
    )

    assert changed
    assert updated[SAFE] == pytest.approx(0.40)
    assert updated[LOST] == pytest.approx(0.0)
    assert updated[LEAKED] == pytest.approx(0.30)
    assert updated[STOLEN] == pytest.approx(0.30)
    assert_probabilities_sum_to_one(updated)
