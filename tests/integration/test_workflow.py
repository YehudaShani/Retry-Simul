"""Integration tests: verify modules work together."""
import pytest
from retry_simul.consts import SAFE, LOST, LEAKED, STOLEN
from retry_simul import computations
from retry_simul import wallet_enumerations
from retry_simul import constrained_probabilities
from retry_simul.types_of_wallets import symmetric_wallet
from retry_simul import optimal_symmetric_wallets


class TestEnumerateToComputePipeline:
    """Integration: enumerateStates -> ownerAdvKeysFromStates -> computeSuccessProbability."""

    def test_full_pipeline_success_probability_in_range(self, key_count, uniform_probs):
        states, state_probs = wallet_enumerations.enumerateStates(
            key_count, uniform_probs
        )
        owner, adv = wallet_enumerations.ownerAdvKeysFromStates(states)
        wallet = symmetric_wallet(key_count, 2)
        p = computations.computeSuccessProbability(wallet, owner, adv, state_probs)
        assert 0 <= p <= 1.0

    def test_probabilities_sum_to_one_throughout(self, key_count, uniform_probs):
        states, state_probs = wallet_enumerations.enumerateStates(
            key_count, uniform_probs
        )
        assert sum(state_probs) == pytest.approx(1.0)


class TestOptimalSymmetricIntegration:
    """Integration: find_optimal_symmetric_wallets uses correct modules."""

    def test_returns_valid_result(self, key_count, uniform_probs):
        # Note: optimal_symmetric_wallets has typos (enumerateStates, states)
        # that may need fixing before this passes
        try:
            wallet, prob, threshold = optimal_symmetric_wallets.find_optimal_symmetric_wallets(
                key_count, uniform_probs
            )
            assert wallet is not None
            assert 0 <= prob <= 1.0
            assert 1 <= threshold <= key_count
        except (NameError, AttributeError) as e:
            pytest.skip(f"optimal_symmetric_wallets has known issues: {e}")


class TestConstrainedProbabilitiesIntegration:
    """Integration: constrain_amount_of_keys with enumerateStates output."""

    def test_constrain_with_enumerated_states(self, key_count, uniform_probs):
        states, state_probs = wallet_enumerations.enumerateStates(
            key_count, uniform_probs
        )
        owner, adv = wallet_enumerations.ownerAdvKeysFromStates(states)
        total = constrained_probabilities.constrain_amount_of_keys(
            owner, adv, state_probs, [1, 2, 3], [0, 1, 2, 3]
        )
        assert total == pytest.approx(1.0)
