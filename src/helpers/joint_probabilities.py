"""Joint probabilities over owner / attacker key bitmasks (i.i.d. per-key states)."""

from __future__ import annotations

from .consts import SAFE, LOST, LEAKED, STOLEN


def number_of_keys_in_common(bitmask1: int, bitmask2: int) -> int:
    return (bitmask1 & bitmask2).bit_count()


def number_of_keys_in_user_not_in_attacker(user_bitmask: int, attacker_bitmask: int) -> int:
    return (user_bitmask & ~attacker_bitmask).bit_count()


def number_of_keys_in_attacker_not_in_user(user_bitmask: int, attacker_bitmask: int) -> int:
    return (attacker_bitmask & ~user_bitmask).bit_count()


def number_of_keys_in_neither(key_count: int, user_bitmask: int, attacker_bitmask: int) -> int:
    return (
        key_count
        - number_of_keys_in_common(user_bitmask, attacker_bitmask)
        - number_of_keys_in_user_not_in_attacker(user_bitmask, attacker_bitmask)
        - number_of_keys_in_attacker_not_in_user(user_bitmask, attacker_bitmask)
    )


def probability_attacker_has_key_if_user_has_key(probabilities: dict[int, float]) -> float:
    """Given the user has the key, the key is SAFE or LEAKED; return P(attacker has | user has)."""
    return probabilities[LEAKED] / (probabilities[SAFE] + probabilities[LEAKED])


def probability_attacker_has_key_if_user_doesnt_have_key(probabilities: dict[int, float]) -> float:
    """Given the user lacks the key, the key is LOST or STOLEN; return P(attacker has | user lacks)."""
    return probabilities[STOLEN] / (probabilities[LOST] + probabilities[STOLEN])


def probability_user_has_key_if_attacker_has_key(probabilities: dict[int, float]) -> float:
    return probabilities[LEAKED] / (probabilities[LEAKED] + probabilities[STOLEN])


def probability_user_has_key_if_attacker_doesnt_have_key(probabilities: dict[int, float]) -> float:
    return probabilities[SAFE] / (probabilities[SAFE] + probabilities[LOST])


def joint_probability(
    key_count: int,
    user_bitmask: int,
    attacker_bitmask: int,
    key_probabilities: dict[int, float],
) -> float:
    """Unconditional P(owner bitmask = u, attacker bitmask = a) for i.i.d. keys.

    Per position: both have → LEAKED; user only → SAFE; attacker only → STOLEN; neither → LOST.
    """
    if key_count <= 0:
        raise ValueError("key_count must be positive")
    full = (1 << key_count) - 1
    u = user_bitmask & full
    a = attacker_bitmask & full

    n_both = number_of_keys_in_common(u, a)
    n_adv_only = number_of_keys_in_attacker_not_in_user(u, a)
    n_user_only = number_of_keys_in_user_not_in_attacker(u, a)
    n_neither = number_of_keys_in_neither(key_count, u, a)

    return (
        key_probabilities[LEAKED] ** n_both
        * key_probabilities[STOLEN] ** n_adv_only
        * key_probabilities[SAFE] ** n_user_only
        * key_probabilities[LOST] ** n_neither
    )


def joint_probability_given_user_bitmask(
    key_count: int,
    user_bitmask: int,
    attacker_bitmask: int,
    key_probabilities: dict[int, float],
) -> float:
    """P(attacker bitmask = a | owner bitmask = u)."""
    p_user = probability_user_bitmask(key_count, user_bitmask, key_probabilities)
    if p_user <= 0.0:
        return 0.0
    return joint_probability(key_count, user_bitmask, attacker_bitmask, key_probabilities) / p_user


def joint_probability_given_attacker_bitmask(
    key_count: int,
    user_bitmask: int,
    attacker_bitmask: int,
    key_probabilities: dict[int, float],
) -> float:
    """P(owner bitmask = u | attacker bitmask = a)."""
    p_adv = probability_attacker_bitmask(key_count, attacker_bitmask, key_probabilities)
    if p_adv <= 0.0:
        return 0.0
    return joint_probability(key_count, user_bitmask, attacker_bitmask, key_probabilities) / p_adv


def probability_user_bitmask(
    key_count: int,
    user_bitmask: int,
    key_probabilities: dict[int, float],
) -> float:
    """P(owner bitmask = u): each set bit requires {SAFE, LEAKED}, each clear bit {LOST, STOLEN}."""
    full = (1 << key_count) - 1
    u = user_bitmask & full
    k = u.bit_count()
    p_has = key_probabilities[SAFE] + key_probabilities[LEAKED]
    p_lacks = key_probabilities[LOST] + key_probabilities[STOLEN]
    return (p_has**k) * (p_lacks ** (key_count - k))


def probability_attacker_bitmask(
    key_count: int,
    attacker_bitmask: int,
    key_probabilities: dict[int, float],
) -> float:
    """P(attacker bitmask = a): each set bit requires {LEAKED, STOLEN}, each clear {SAFE, LOST}."""
    full = (1 << key_count) - 1
    a = attacker_bitmask & full
    k = a.bit_count()
    p_has = key_probabilities[LEAKED] + key_probabilities[STOLEN]
    p_lacks = key_probabilities[SAFE] + key_probabilities[LOST]
    return (p_has**k) * (p_lacks ** (key_count - k))


def main():
    key_count = 3
    user_bitmask = 0b101
    attacker_bitmask = 0b110
    key_probabilities = {SAFE: 0.7, LEAKED: 0.1, LOST: 0.1, STOLEN: 0.1}
    print(joint_probability(key_count, user_bitmask, attacker_bitmask, key_probabilities))


if __name__ == "__main__":
    main()