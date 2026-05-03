"""Gain breakdown analysis for wallet key probabilities."""

from typing import Dict, List

from .consts import SAFE, LOST, LEAKED, STOLEN
from .wallet_enumerations import enumerateStates, ownerAdvKeysFromStates
from .wallet_state import WalletState


def _validate_matching_wallet_models(
    user_wallet: WalletState,
    attacker_wallet: WalletState,
) -> None:
    """Ensure both wallets are evaluated under the same probability model."""
    if user_wallet.key_count != attacker_wallet.key_count:
        raise ValueError("user_wallet and attacker_wallet must have the same key_count")
    if user_wallet.probabilities != attacker_wallet.probabilities:
        raise ValueError("user_wallet and attacker_wallet must have identical probabilities")


def conditional_wallet_satisfaction_probabilities(
    user_wallet: WalletState,
    attacker_wallet: WalletState,
) -> dict[str, float | None]:
    """Return joint and conditional acceptance probabilities for two wallets."""
    _validate_matching_wallet_models(user_wallet, attacker_wallet)

    states, state_probabilities = enumerateStates(
        user_wallet.key_count, user_wallet.probabilities
    )
    owner_states, adv_states = ownerAdvKeysFromStates(states)

    p_user_satisfies = 0.0
    p_attacker_satisfies = 0.0
    p_joint = 0.0
    for probability, owner_state, adv_state in zip(
        state_probabilities, owner_states, adv_states
    ):
        user_ok = user_wallet.bitmask_is_in_wallet(owner_state)
        attacker_ok = attacker_wallet.bitmask_is_in_wallet(adv_state)
        if user_ok:
            p_user_satisfies += probability
        if attacker_ok:
            p_attacker_satisfies += probability
        if user_ok and attacker_ok:
            p_joint += probability

    return {
        "joint_probability": p_joint,
        "p_user_satisfies": p_user_satisfies,
        "p_attacker_satisfies": p_attacker_satisfies,
        "user_given_attacker": (
            p_joint / p_attacker_satisfies if p_attacker_satisfies > 0.0 else None
        ),
        "attacker_given_user": (
            p_joint / p_user_satisfies if p_user_satisfies > 0.0 else None
        ),
    }


def probability_user_has_specific_bitmasks(
    probabilities: Dict[int, float],
    key_count: int,
    bitmasks: List[int],
) -> float:
    """Probability owner has specific bitmasks (SAFE or LEAKED for set bits)."""
    p_owner_has = probabilities.get(SAFE, 0.0) + probabilities.get(LEAKED, 0.0)
    p_owner_lacks = probabilities.get(LOST, 0.0) + probabilities.get(STOLEN, 0.0)
    total = 0.0
    for b in bitmasks:
        k = b.bit_count()
        total += (p_owner_has**k) * (p_owner_lacks ** (key_count - k))
    return total


def probability_user_has_bitmasks_and_attacker_accepted(
    wallet_state: WalletState,
    bitmasks: List[int],
) -> float:
    """Probability owner has bitmask AND attacker is accepted by the wallet."""
    states, state_probabilities = enumerateStates(
        wallet_state.key_count, wallet_state.probabilities
    )
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
    """Probability attacker has bitmask AND owner is accepted by the wallet."""
    states, state_probabilities = enumerateStates(
        wallet_state.key_count, wallet_state.probabilities
    )
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
    """Probability both owner and attacker match one of the bitmasks."""
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

    p_user_has_specific_bitmasks = probability_user_has_specific_bitmasks(
        wallet_state.probabilities, wallet_state.key_count, bitmasks
    )
    p_attacker_has_bitmasks_and_user_accepted = probability_attacker_has_bitmasks_and_user_accepted(
        wallet_state, bitmasks
    )
    p_user_has_bitmasks_and_attacker_accepted = probability_user_has_bitmasks_and_attacker_accepted(
        wallet_state, bitmasks
    )
    p_both_have_same_bitmasks = probability_both_have_same_bitmasks(
        wallet_state.probabilities, wallet_state.key_count, bitmasks
    )

    return (
        p_user_has_specific_bitmasks
        - p_attacker_has_bitmasks_and_user_accepted
        - p_user_has_bitmasks_and_attacker_accepted
        - p_both_have_same_bitmasks
    )

