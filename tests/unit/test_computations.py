"""Unit tests for computations module."""
import pytest
from helpers.consts import SAFE, LOST, LEAKED, STOLEN
from helpers.computations import (
    computeSuccessProbability,
    computeSuccessProbabilityWithForbiddenTerm,
    findOptimalWallet,
    generateKeyFaultProbabilityScenarios,
)
from helpers.wallet_enumerations import (
    enumerateStates,
    ownerAdvKeysFromStates,
    enumerateStaticWallets,
)


class TestComputeSuccessProbability:
    """Tests for computeSuccessProbability."""

    def test_owner_ok_adv_not_ok_success(self):
        # Minimal: 1 key, owner has it, adv doesn't
        owner_states = [1]
        adv_states = [0]
        probs = [1.0]
        wallet = [1]
        p = computeSuccessProbability(wallet, owner_states, adv_states, probs)
        assert p == pytest.approx(1.0)

    def test_both_ok_no_success(self):
        owner_states = [1]
        adv_states = [1]
        probs = [1.0]
        wallet = [1]
        p = computeSuccessProbability(wallet, owner_states, adv_states, probs)
        assert p == pytest.approx(0.0)

    def test_probabilities_sum_correct(self, key_count, uniform_probs):
        states, state_probs = enumerateStates(key_count, uniform_probs)
        owner, adv = ownerAdvKeysFromStates(states)
        wallet = [0b111]  # all keys
        p = computeSuccessProbability(wallet, owner, adv, state_probs)
        assert 0 <= p <= 1.0


class TestGenerateKeyFaultProbabilityScenarios:
    def test_step_must_divide_one(self):
        with pytest.raises(ValueError, match="evenly divide"):
            generateKeyFaultProbabilityScenarios(step=0.3)

    def test_safe_greater_than_stolen(self):
        scenarios = generateKeyFaultProbabilityScenarios(step=0.5)
        for s in scenarios:
            assert s[SAFE] > s[STOLEN]

    def test_probabilities_sum_to_one_per_scenario(self):
        scenarios = generateKeyFaultProbabilityScenarios(step=0.25)
        for s in scenarios:
            total = s[SAFE] + s[LOST] + s[LEAKED] + s[STOLEN]
            assert total == pytest.approx(1.0)


class TestFindOptimalWallet:
    def test_returns_wallet_and_prob(self, key_count, uniform_probs):
        wallets = enumerateStaticWallets(key_count, deduplicate_by_architecture=True)
        best_wallets, best_p = findOptimalWallet(wallets, key_count, uniform_probs)
        assert isinstance(best_wallets, list)
        assert len(best_wallets) >= 1
        assert 0 <= best_p <= 1.0
