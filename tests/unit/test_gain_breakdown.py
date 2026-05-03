"""Unit tests for gain_breakdown module."""
import pytest
from retry_simul.wallet_state import WalletState
from retry_simul.gain_breakdown import (
    conditional_wallet_satisfaction_probabilities,
    probability_user_has_bitmasks_and_attacker_accepted,
    probability_user_has_specific_bitmasks,
    total_change_when_adding_bitmask,
)


class TestJointProbabilities:
    """Verify the base functions work as expected."""

    def test_probability_user_has_specific_bitmasks(self, uniform_probs):

        ws = WalletState(2, [], uniform_probs)
        predicted = probability_user_has_specific_bitmasks(ws.probabilities, ws.key_count, [0b10])
        actual = 0.25
        assert predicted == actual
    
    def test_probability_user_has_bitmasks_and_attacker_accepted(self, uniform_probs):

        ws = WalletState(2, [0b11], uniform_probs)
        actual = probability_user_has_bitmasks_and_attacker_accepted(ws, [0b10])
        expected = 0.25 * 0.25
        assert actual == expected

    def test_probability_user_has_bitmasks_and_attacker_accepted_2(self, uniform_probs):

        ws = WalletState(2, [0b10, 0b11], uniform_probs)
        actual = probability_user_has_bitmasks_and_attacker_accepted(ws, [0b01])
        expected = 0.25 * 0.5
        assert actual == expected

    def test_probability_user_has_bitmasks_and_attacker_accepted_3(self, uniform_probs):

        ws = WalletState(2, [0b11], uniform_probs)
        actual = probability_user_has_bitmasks_and_attacker_accepted(ws, [0b01, 0b10])
        # Can either be leaked and stolen, or the other way around
        expected = 0.25 * 0.25 * 2
        assert actual == expected


class TestConditionalWalletSatisfactionProbabilities:
    """Verify conditional acceptance probabilities between two wallets."""

    def test_returns_joint_and_both_conditionals(self, uniform_probs):
        user_wallet = WalletState(2, [0b11], uniform_probs)
        attacker_wallet = WalletState(2, [0b01], uniform_probs)

        actual = conditional_wallet_satisfaction_probabilities(user_wallet, attacker_wallet)

        assert actual["joint_probability"] == pytest.approx(0.125)
        assert actual["p_user_satisfies"] == pytest.approx(0.25)
        assert actual["p_attacker_satisfies"] == pytest.approx(0.5)
        assert actual["user_given_attacker"] == pytest.approx(0.25)
        assert actual["attacker_given_user"] == pytest.approx(0.5)

    def test_returns_none_when_conditioning_event_is_impossible(self, uniform_probs):
        user_wallet = WalletState(2, [0b01], uniform_probs)
        attacker_wallet = WalletState(2, [], uniform_probs)

        actual = conditional_wallet_satisfaction_probabilities(user_wallet, attacker_wallet)

        assert actual["joint_probability"] == pytest.approx(0.0)
        assert actual["p_user_satisfies"] == pytest.approx(0.5)
        assert actual["p_attacker_satisfies"] == pytest.approx(0.0)
        assert actual["user_given_attacker"] is None
        assert actual["attacker_given_user"] == pytest.approx(0.0)

    def test_raises_for_mismatched_key_count(self, uniform_probs):
        user_wallet = WalletState(2, [0b01], uniform_probs)
        attacker_wallet = WalletState(3, [0b001], uniform_probs)

        with pytest.raises(ValueError, match="same key_count"):
            conditional_wallet_satisfaction_probabilities(user_wallet, attacker_wallet)

    def test_raises_for_mismatched_probabilities(self, uniform_probs, safe_heavy_probs):
        user_wallet = WalletState(2, [0b01], uniform_probs)
        attacker_wallet = WalletState(2, [0b01], safe_heavy_probs)

        with pytest.raises(ValueError, match="identical probabilities"):
            conditional_wallet_satisfaction_probabilities(user_wallet, attacker_wallet)



class TestTotalChangeWhenAddingBitmask:
    """Verify total_change_when_adding_bitmask matches actual success probability change."""

    def test_single_bitmask_matches_actual_change(self, uniform_probs):
        """Adding one bitmask: predicted change equals actual success prob delta."""
        ws = WalletState(3, [0b111], uniform_probs)
        prob_before = ws.compute_success_probability()
        bitmasks_to_add = [0b011]
        predicted = total_change_when_adding_bitmask(ws,  bitmasks_to_add)
        ws.add_bitmask(bitmasks_to_add[0])
        prob_after = ws.compute_success_probability()
        actual_change = prob_after - prob_before
        assert actual_change == pytest.approx(predicted)

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
        assert actual_change == pytest.approx(predicted)

    def test_multiple_bitmasks_matches_actual_change_2(self, uniform_probs):
        """Adding multiple bitmasks: predicted change equals actual success prob delta."""
        ws = WalletState(2, [0b11], uniform_probs)
        prob_before = ws.compute_success_probability()
        bitmasks_to_add = [0b01, 0b10]
        predicted = total_change_when_adding_bitmask(ws, bitmasks_to_add)
        for b in bitmasks_to_add:
            ws.add_bitmask(b)
        prob_after = ws.compute_success_probability()
        actual_change = prob_after - prob_before
        assert actual_change == pytest.approx(predicted)

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
