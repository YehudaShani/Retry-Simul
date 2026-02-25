"""Unit tests for gain_breakdown module."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pytest
from wallet_state import WalletState
from gain_breakdown import probability_user_has_specific_bitmasks, total_change_when_adding_bitmask


class TestJointProbabilities:
    """Verify the base functions work as expected."""

    def test_probability_user_has_specific_bitmasks(self, uniform_probs):

        ws = WalletState(2, [0b10], uniform_probs)
        expected = probability_user_has_specific_bitmasks(ws.probabilities, ws.key_count, [0b10])
        actual = ws.compute_success_probability()
        assert actual == expected
        


class TestTotalChangeWhenAddingBitmask:
    """Verify total_change_when_adding_bitmask matches actual success probability change."""

    def test_single_bitmask_matches_actual_change(self, uniform_probs):
        """Adding one bitmask: predicted change equals actual success prob delta."""
        ws = WalletState(3, [0b111], uniform_probs)
        prob_before = ws.compute_success_probability()
        bitmasks_to_add = [0b011]
        predicted = total_change_when_adding_bitmask(ws, bitmasks_to_add)
        ws.add_bitmask(bitmasks_to_add[0])
        prob_after = ws.compute_success_probability()
        actual_change = prob_after - prob_before
        assert predicted == pytest.approx(actual_change)

    def test_multiple_bitmasks_matches_actual_change(self, uniform_probs):
        """Adding multiple bitmasks: predicted change equals actual success prob delta."""
        ws = WalletState(4, [0b1111], uniform_probs)
        prob_before = ws.compute_success_probability()
        bitmasks_to_add = [0b0110, 0b1001]
        predicted = total_change_when_adding_bitmask(ws, bitmasks_to_add)
        for b in bitmasks_to_add:
            ws.add_bitmask(b)
        prob_after = ws.compute_success_probability()
        actual_change = prob_after - prob_before
        assert predicted == pytest.approx(actual_change)

    def test_empty_wallet_single_bitmask(self, uniform_probs):
        """Adding bitmask to empty wallet."""
        ws = WalletState(3, [], uniform_probs)
        prob_before = ws.compute_success_probability()
        bitmasks_to_add = [0b101]
        predicted = total_change_when_adding_bitmask(ws, bitmasks_to_add)
        ws.add_bitmask(bitmasks_to_add[0])
        prob_after = ws.compute_success_probability()
        actual_change = prob_after - prob_before
        assert predicted == pytest.approx(actual_change)

    def test_custom_probs_matches_actual_change(self, safe_heavy_probs):
        """Non-uniform probabilities: predicted change equals actual."""
        ws = WalletState(4, [0b1111, 0b0111], safe_heavy_probs)
        prob_before = ws.compute_success_probability()
        bitmasks_to_add = [0b0101]
        predicted = total_change_when_adding_bitmask(ws, bitmasks_to_add)
        ws.add_bitmask(bitmasks_to_add[0])
        prob_after = ws.compute_success_probability()
        actual_change = prob_after - prob_before
        assert predicted == pytest.approx(actual_change)
