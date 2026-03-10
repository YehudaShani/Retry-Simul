"""Gain breakdown analysis for wallet key probabilities."""
from typing import Dict, List

from consts import SAFE, LOST, LEAKED, STOLEN
from wallet_enumerations import enumerateStates, ownerAdvKeysFromStates
from wallet_state import WalletState


def probability_user_has_specific_bitmasks(
    probabilities: Dict[int, float],
    key_count: int,
    bitmasks: List[int],
) -> float:
    """Probability of particular combinations: for each bitmask, keys set are in {SAFE, LEAKED}, unset in {LOST, STOLEN}.

    Args:
        probabilities: Dict mapping KeyStates (SAFE, LOST, LEAKED, STOLEN) to probability.
        key_count: Total number of keys (n).
        bitmasks: List of bitmasks (built outside, typically not in the wallet).

    Returns:
        Sum over bitmasks of (p_safe + p_leak)^popcount(b) * (p_lost + p_stolen)^(n - popcount(b))
    """
    p_owner_has = probabilities.get(SAFE, 0.0) + probabilities.get(LEAKED, 0.0)
    p_owner_lacks = probabilities.get(LOST, 0.0) + probabilities.get(STOLEN, 0.0)
    total = 0.0
    for b in bitmasks:
        k = b.bit_count()
        total += (p_owner_has ** k) * (p_owner_lacks ** (key_count - k))
    return total


def probability_user_has_bitmasks_and_attacker_accepted(
    wallet_state: WalletState,
    bitmasks: List[int],
) -> float:
    """Probability that the user has one of the given bitmasks AND the attacker is accepted by the wallet.

    Args:
        wallet_state: WalletState with key_count, probabilities, and bitmasks.
        bitmasks: List of bitmasks (built outside, typically not in the wallet).

    Returns:
        Sum of state probabilities where owner_state in bitmasks and adversary covers the wallet.
    """
    states, state_probabilities = enumerateStates(wallet_state.key_count, wallet_state.probabilities)
    owner_states, adv_states = ownerAdvKeysFromStates(states)
    bitmasks_set = set(bitmasks)
    total = 0.0
    for i, (owner_state, adv_state) in enumerate(zip(owner_states, adv_states)):
        if owner_state in bitmasks_set and wallet_state.bitmask_is_in_wallet(adv_state):
            total += state_probabilities[i]
    return total


def probability_attacker_has_bitmasks_and_user_accepted(
    wallet_state: WalletState,
    bitmasks: List[int],
) -> float:
    """Probability that the attacker has one of the given bitmasks AND the user is accepted by the wallet.

    Args:
        wallet_state: WalletState with key_count, probabilities, and bitmasks.
        bitmasks: List of bitmasks (built outside, typically not in the wallet).

    Returns:
        Sum of state probabilities where adv_state in bitmasks and owner covers the wallet.
    """
    states, state_probabilities = enumerateStates(wallet_state.key_count, wallet_state.probabilities)
    owner_states, adv_states = ownerAdvKeysFromStates(states)
    bitmasks_set = set(bitmasks)
    total = 0.0
    for i, (owner_state, adv_state) in enumerate(zip(owner_states, adv_states)):
        if adv_state in bitmasks_set and wallet_state.bitmask_is_in_wallet(owner_state):
            total += state_probabilities[i]
    return total


def probability_both_have_same_bitmasks(
    probabilities: Dict[int, float],
    key_count: int,
    bitmasks: List[int],
) -> float:
    """Probability of particular combinations: for each bitmask, keys set are LEAKED (both have them), unset are not.

    Args:
        probabilities: Dict mapping KeyStates (SAFE, LOST, LEAKED, STOLEN) to probability.
        key_count: Total number of keys (n).
        bitmasks: List of bitmasks (built outside, typically not in the wallet).

    Returns:
        Sum over bitmasks of (p_leak)^popcount(b) * (1 - p_leak)^(n - popcount(b))
    """
    states, state_probabilities = enumerateStates(key_count, probabilities)
    owner_states, adv_states = ownerAdvKeysFromStates(states)
    bitmasks_set = set(bitmasks)
    total = 0.0
    for i, (owner_state, adv_state) in enumerate(zip(owner_states, adv_states)):
        if owner_state in bitmasks_set and adv_state in bitmasks_set:
            total += state_probabilities[i]
    return total


def total_change_when_adding_bitmask(
    wallet_state: WalletState,
    bitmasks: List[int],
) -> float:
    """Total change in success probability when adding the given bitmasks to the wallet."""

    # remove bitmasks that are covered by wallet
    bitmasks_to_remove = set()
    for bitmask in bitmasks:
        if wallet_state.bitmask_is_in_wallet(bitmask):
            bitmasks_to_remove.add(bitmask)
    for bitmask in bitmasks_to_remove:
        bitmasks.remove(bitmask)
    
    p_user_has_specific_bitmasks = probability_user_has_specific_bitmasks(wallet_state.probabilities, wallet_state.key_count, bitmasks)
    p_attacker_has_bitmasks_and_user_accepted = probability_attacker_has_bitmasks_and_user_accepted(wallet_state, bitmasks)
    p_user_has_bitmasks_and_attacker_accepted = probability_user_has_bitmasks_and_attacker_accepted(wallet_state, bitmasks)
    p_both_have_same_bitmasks = probability_both_have_same_bitmasks(wallet_state.probabilities, wallet_state.key_count, bitmasks)

    return p_user_has_specific_bitmasks - p_attacker_has_bitmasks_and_user_accepted - p_user_has_bitmasks_and_attacker_accepted - p_both_have_same_bitmasks
