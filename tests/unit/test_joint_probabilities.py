"""Unit tests for joint_probabilities helpers."""
import pytest

from helpers.consts import SAFE, LOST, LEAKED, STOLEN
from helpers.joint_probabilities import (
    joint_probability,
    joint_probability_given_attacker_bitmask,
    joint_probability_given_user_bitmask,
    number_of_keys_in_attacker_not_in_user,
    number_of_keys_in_common,
    number_of_keys_in_neither,
    number_of_keys_in_user_not_in_attacker,
    probability_attacker_bitmask,
    probability_attacker_has_key_if_user_doesnt_have_key,
    probability_attacker_has_key_if_user_has_key,
    probability_user_bitmask,
    probability_user_has_key_if_attacker_doesnt_have_key,
    probability_user_has_key_if_attacker_has_key,
)


class TestNumberOfKeysInCommon:
    def test_empty_intersection(self):
        assert number_of_keys_in_common(0b101, 0b010) == 0

    def test_full_overlap(self):
        assert number_of_keys_in_common(0b111, 0b111) == 3

    def test_partial_overlap(self):
        assert number_of_keys_in_common(0b101, 0b011) == 1

    def test_zero_masks(self):
        assert number_of_keys_in_common(0, 0) == 0


class TestKeyRegionCountsPartition:
    def test_counts_sum_to_key_count(self):
        key_count = 5
        u, a = 0b10101, 0b01110
        total = (
            number_of_keys_in_common(u, a)
            + number_of_keys_in_user_not_in_attacker(u, a)
            + number_of_keys_in_attacker_not_in_user(u, a)
            + number_of_keys_in_neither(key_count, u, a)
        )
        assert total == key_count

    def test_user_only_and_adv_only(self):
        assert number_of_keys_in_user_not_in_attacker(0b100, 0b010) == 1
        assert number_of_keys_in_attacker_not_in_user(0b100, 0b010) == 1
        assert number_of_keys_in_neither(3, 0b100, 0b010) == 1


class TestConditionalAttackerProbabilities:
    def test_attacker_has_key_given_user_has_key(self):
        probs = {SAFE: 0.5, LOST: 0.1, LEAKED: 0.3, STOLEN: 0.1}
        expected = 0.3 / (0.5 + 0.3)
        assert probability_attacker_has_key_if_user_has_key(probs) == pytest.approx(expected)

    def test_attacker_has_key_given_user_does_not_have_key(self):
        probs = {SAFE: 0.5, LOST: 0.2, LEAKED: 0.2, STOLEN: 0.1}
        expected = 0.1 / (0.2 + 0.1)
        assert probability_attacker_has_key_if_user_doesnt_have_key(probs) == pytest.approx(
            expected
        )


class TestConditionalUserProbabilities:
    def test_user_has_key_given_attacker_has_key(self):
        probs = {SAFE: 0.4, LOST: 0.1, LEAKED: 0.3, STOLEN: 0.2}
        expected = 0.3 / (0.3 + 0.2)
        assert probability_user_has_key_if_attacker_has_key(probs) == pytest.approx(expected)

    def test_user_has_key_given_attacker_does_not_have_key(self):
        probs = {SAFE: 0.6, LOST: 0.2, LEAKED: 0.1, STOLEN: 0.1}
        expected = 0.6 / (0.6 + 0.2)
        assert probability_user_has_key_if_attacker_doesnt_have_key(probs) == pytest.approx(
            expected
        )


class TestMarginalBitmaskProbabilities:
    def test_user_bitmask_all_keys(self, uniform_probs):
        key_count = 3
        p_has = uniform_probs[SAFE] + uniform_probs[LEAKED]
        assert probability_user_bitmask(key_count, 0b111, uniform_probs) == pytest.approx(
            p_has**key_count
        )

    def test_attacker_bitmask_matches_joint_normalization(self, uniform_probs):
        key_count = 3
        u, a = 0b101, 0b011
        j = joint_probability(key_count, u, a, uniform_probs)
        assert j == pytest.approx(
            probability_user_bitmask(key_count, u, uniform_probs)
            * joint_probability_given_user_bitmask(key_count, u, a, uniform_probs)
        )


class TestJointProbability:
    def test_rejects_non_positive_key_count(self, uniform_probs):
        with pytest.raises(ValueError, match="key_count must be positive"):
            joint_probability(0, 0, 0, uniform_probs)

    def test_masks_trimmed_to_key_count(self, uniform_probs):
        key_count = 2
        assert joint_probability(key_count, 0b1111, 0b1111, uniform_probs) == pytest.approx(
            joint_probability(key_count, 0b11, 0b11, uniform_probs)
        )

    def test_single_key_states(self):
        probs = {SAFE: 0.7, LOST: 0.1, LEAKED: 0.1, STOLEN: 0.1}
        assert joint_probability(1, 1, 1, probs) == pytest.approx(probs[LEAKED])
        assert joint_probability(1, 1, 0, probs) == pytest.approx(probs[SAFE])
        assert joint_probability(1, 0, 1, probs) == pytest.approx(probs[STOLEN])
        assert joint_probability(1, 0, 0, probs) == pytest.approx(probs[LOST])



class TestConditionalJointFromDefinition:
    def test_given_user_matches_ratio(self, uniform_probs):
        key_count = 3
        u, a = 0b111, 0b110
        num = joint_probability(key_count, u, a, uniform_probs)
        den = probability_user_bitmask(key_count, u, uniform_probs)
        assert joint_probability_given_user_bitmask(key_count, u, a, uniform_probs) == pytest.approx(
            num / den
        )

    def test_given_attacker_matches_ratio(self, uniform_probs):
        key_count = 3
        u, a = 0b101, 0b011
        num = joint_probability(key_count, u, a, uniform_probs)
        den = probability_attacker_bitmask(key_count, a, uniform_probs)
        assert joint_probability_given_attacker_bitmask(
            key_count, u, a, uniform_probs
        ) == pytest.approx(num / den)

    def test_given_user_zero_when_user_bitmask_impossible(self):
        key_count = 1
        probs = {SAFE: 1.0, LOST: 0.0, LEAKED: 0.0, STOLEN: 0.0}
        assert joint_probability_given_user_bitmask(key_count, 0, 0, probs) == 0.0
