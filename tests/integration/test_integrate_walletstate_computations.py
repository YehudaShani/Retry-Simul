import pytest
from consts import SAFE, LOST, LEAKED, STOLEN
import computations
import wallet_enumerations
import constrained_probabilities
from tests.conftest import key_count
from types_of_wallets import symmetric_wallet
import optimal_symmetric_wallets



class TestSuccessProbabilityOfWallet:

    def test_same_success_when_adding_superset(self):
        keyCount = 3
        wallet = symmetric_wallet(keyCount, 2)
        probabilities = {SAFE: 0.2, LOST: 0.22, LEAKED: 0.48, STOLEN: 0.1}
        states, state_probabilities = wallet_enumerations.enumerateStates(keyCount, probabilities)
        owner_states, adversary_states = wallet_enumerations.ownerAdvKeysFromStates(states)
        success_prob = computations.computeSuccessProbability(wallet, owner_states, adversary_states, state_probabilities)

        new_wallet = wallet + [0b111]
        new_success_prob = computations.computeSuccessProbability(new_wallet, owner_states, adversary_states, state_probabilities)
        assert success_prob == pytest.approx(new_success_prob)