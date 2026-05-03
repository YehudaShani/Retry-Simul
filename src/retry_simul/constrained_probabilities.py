import math
from typing import Iterable, Sequence


def constrain_amount_of_keys(
    user_states: Sequence[int],
    adversary_states: Sequence[int],
    probabilities: Sequence[float],
    user_key_counts: Iterable[int],
    adversary_key_counts: Iterable[int],
) -> float:
    user_allowed = set(user_key_counts)
    adversary_allowed = set(adversary_key_counts)
    terms = []
    for i, p in enumerate(probabilities):
        user_safe = user_states[i].bit_count()
        adversary_safe = adversary_states[i].bit_count()
        if user_safe in user_allowed and adversary_safe in adversary_allowed:
            terms.append(p)
    return math.fsum(terms)

