"""Unit tests for wallet_enumerations module."""
import pytest
from consts import SAFE, LOST, LEAKED, STOLEN
from wallet_enumerations import (
    isCovered,
    enumerateStates,
    ownerAdvKeysFromStates,
    enumerateStaticWallets,
    oneBitIndices,
    walletStr,
)


class TestIsCovered:
    """Tests for isCovered (subset/superset check on bitmasks)."""

    def test_exact_match_covered(self):
        wallet = [0b011, 0b100]  # keys 1&2 OR key 3
        assert isCovered(0b011, wallet) is True
        assert isCovered(0b100, wallet) is True

    def test_superset_covered(self):
        wallet = [0b011]  # keys 1&2
        assert isCovered(0b111, wallet) is True  # 111 contains 011

    def test_subset_not_covered(self):
        wallet = [0b111]  # keys 1&2&3
        assert isCovered(0b011, wallet) is False

    def test_empty_wallet_not_covered(self):
        assert isCovered(0b011, []) is False

    def test_no_overlap_not_covered(self):
        wallet = [0b100]
        assert isCovered(0b011, wallet) is False

    def test_overlapping_combinations(self):
        wallet = [0b011, 0b111]
        assert isCovered(0b011, wallet) is True
        assert isCovered(0b111, wallet) is True


class TestEnumerateStates:
    """Tests for enumerateStates."""

    def test_single_key_four_states(self):
        probs = {SAFE: 0.25, LOST: 0.25, LEAKED: 0.25, STOLEN: 0.25}
        states, probs_out = enumerateStates(1, probs)
        assert len(states) == 4
        assert len(probs_out) == 4
        assert sum(probs_out) == pytest.approx(1.0)

    def test_probabilities_sum_to_one(self, key_count, uniform_probs):
        states, probs = enumerateStates(key_count, uniform_probs)
        assert sum(probs) == pytest.approx(1.0)

    def test_total_states_count(self, key_count, uniform_probs):
        states, probs = enumerateStates(key_count, uniform_probs)
        assert len(states) == 4 ** key_count

    def test_invalid_key_count_raises(self, uniform_probs):
        with pytest.raises(Exception, match="Invalid"):
            enumerateStates(0, uniform_probs)


class TestOwnerAdvKeysFromStates:
    """Tests for ownerAdvKeysFromStates."""

    def test_all_safe_owner_has_all_adv_none(self):
        states = [[SAFE, SAFE, SAFE]]
        owner, adv = ownerAdvKeysFromStates(states)
        assert owner[0] == 0b111
        assert adv[0] == 0

    def test_all_stolen_adv_has_all_owner_none(self):
        states = [[STOLEN, STOLEN, STOLEN]]
        owner, adv = ownerAdvKeysFromStates(states)
        assert owner[0] == 0
        assert adv[0] == 0b111

    def test_leaked_both_have_key(self):
        states = [[LEAKED]]
        owner, adv = ownerAdvKeysFromStates(states)
        assert owner[0] == 1
        assert adv[0] == 1


class TestOneBitIndices:
    def test_single_bit(self):
        assert oneBitIndices(1) == ["1"]
        assert oneBitIndices(2) == ["2"]

    def test_multiple_bits(self):
        assert oneBitIndices(0b011) == ["1", "2"]
        assert oneBitIndices(0b101) == ["1", "3"]


class TestEnumerateStaticWallets:
    def test_returns_list_of_wallets(self, key_count):
        wallets = enumerateStaticWallets(key_count, deduplicate_by_architecture=False)
        assert isinstance(wallets, list)
        assert all(isinstance(w, list) for w in wallets)

    def test_wallet_bitmasks_valid(self, key_count):
        wallets = enumerateStaticWallets(key_count, deduplicate_by_architecture=False)
        for w in wallets:
            for mask in w:
                assert 0 <= mask < 2 ** key_count
