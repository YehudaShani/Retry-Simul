from dataclasses import dataclass
import random
from typing import Iterable, List, Dict

from .consts import SAFE, LOST, LEAKED, STOLEN, KeyStates

from . import computations
from . import wallet_enumerations
from .types_of_wallets import generate_bitmasks_above_threshold
from .wallet_enumerations import isCovered


@dataclass
class WalletState:
    key_count: int
    bitmasks: List[int]
    probabilities: Dict[int, float]

    def __post_init__(self):
        if not isinstance(self.key_count, int) or self.key_count <= 0:
            raise ValueError("key_count must be a positive integer")
        if not isinstance(self.bitmasks, list):
            self.bitmasks = list(self.bitmasks)
        if any(not isinstance(mask, int) or mask < 0 for mask in self.bitmasks):
            raise ValueError("bitmasks must be a list of non-negative integers")

    @classmethod
    def from_iterable(cls, key_count: int, bitmasks: Iterable[int]) -> "WalletState":
        return cls(key_count, list(bitmasks))

    def add_bitmask(self, bitmask: int) -> None:
        if not isinstance(bitmask, int) or bitmask < 0:
            raise ValueError("bitmask must be a non-negative integer")
        if bitmask in self.bitmasks:
            return
        self.bitmasks.append(bitmask)

    def remove_bitmask(self, bitmask: int) -> None:
        if bitmask not in self.bitmasks:
            return

        # remove all instances of bitmask from the list (should technically only be one instance, but just in case)
        self.bitmasks = [mask for mask in self.bitmasks if mask != bitmask]

    def remove_bitmask_and_subsets(self, bitmask_to_remove: int) -> None:

        for bitmask in self.bitmasks:
            self.add_supersets_of_bitmask(bitmask)

        to_remove = [
            bitmask
            for bitmask in self.bitmasks
            if (bitmask & bitmask_to_remove) == bitmask
        ]

        for bitmask in to_remove:
            self.remove_bitmask(bitmask)

        # self.add_supersets_of_bitmask(bitmask_to_remove)
        # self.remove_bitmask(bitmask_to_remove)

    def add_supersets_of_bitmask(self, bitmask: int) -> None:
        for i in range(self.key_count):
            new_bitmask = bitmask | (1 << i)
            if new_bitmask not in self.bitmasks:
                self.bitmasks.append(new_bitmask)

    def bitmask_is_in_wallet(self, bitmask: int) -> bool:
        return isCovered(bitmask, self.bitmasks)

    def __str__(self) -> str:
        return (
            "The combinations in the wallet are: "
            f"{self.bitmasks} (key_count={self.key_count})"
        )

    def compute_success_probability(self, key_count: int | None = None):
        states, state_probabilities = wallet_enumerations.enumerateStates(
            self.key_count, self.probabilities
        )
        owner_states, adv_states = wallet_enumerations.ownerAdvKeysFromStates(states)
        return computations.computeSuccessProbability(
            self.bitmasks, owner_states, adv_states, state_probabilities
        )

    def fill_up_to_threshold(self, threshold: int):
        # fill the wallet from the largest bitmask to smallest until all bitsmasks of size threshold are added
        # after every addition, check if the wallet success rate has increased. if not, print the wallet and break.
        bitmasks_to_add = generate_bitmasks_above_threshold(self.key_count, threshold)
        bitmasks_to_add.sort(key=lambda x: random.random())
        success_probability = self.compute_success_probability()
        for bitmask in bitmasks_to_add:
            self.add_bitmask(bitmask)
            new_success_probability = self.compute_success_probability()
            if new_success_probability >= success_probability:
                success_probability = new_success_probability
            else:
                return self.bitmasks, bitmask, success_probability

        return self.bitmasks, None, success_probability

    def return_optimal_wallet_for_probability(self) -> List["WalletState"]:
        results = computations.reportOptimalWalletsForProbabilities(
            [self.probabilities],
            self.key_count,
            print_fn=lambda *_args, **_kwargs: None,
        )
        optimal_wallets, _best_p, _probs = results[0]
        return [
            WalletState(self.key_count, list(bitmasks), self.probabilities)
            for bitmasks in optimal_wallets
        ]

    def shift(self) -> "WalletState":
        """Apply the combinatorial down-shift (compression) operator in place.

        A wallet's accepting family is the up-closure of ``bitmasks`` (via
        ``isCovered``). We shift that full up-set toward the lowest key indices
        and re-extract the minimal generators. This canonicalizes the wallet
        downward; note the success probability generally changes.
        """
        family = _up_closure(self.bitmasks, self.key_count)
        shifted = _down_shift_family(family, self.key_count)
        self.bitmasks = _minimal_generators(shifted)
        return self


def _up_closure(bitmasks: Iterable[int], key_count: int) -> set:
    """All non-empty key combinations that grant access (the up-set)."""
    return {
        mask
        for mask in range(1, 1 << key_count)
        if isCovered(mask, bitmasks)
    }


def _down_shift_family(family: Iterable[int], key_count: int) -> set:
    """Repeatedly apply the ij-shift (i < j) until the family stabilizes.

    For a pair of bit positions ``i < j``, each member with bit ``j`` set and
    bit ``i`` clear is moved to the candidate obtained by clearing ``j`` and
    setting ``i``, but only when that candidate is not already present.
    """
    current = set(family)
    changed = True
    while changed:
        changed = False
        for j in range(1, key_count):
            for i in range(j):
                shifted = set(current)
                for mask in current:
                    if (mask >> j) & 1 and not ((mask >> i) & 1):
                        candidate = (mask & ~(1 << j)) | (1 << i)
                        if candidate not in current:
                            shifted.discard(mask)
                            shifted.add(candidate)
                if shifted != current:
                    current = shifted
                    changed = True
    return current


def _minimal_generators(family: Iterable[int]) -> List[int]:
    """Minimal elements of an up-set: masks with no proper subset in the family."""
    members = set(family)
    minimal = []
    for mask in members:
        is_minimal = True
        remaining = mask
        while remaining:
            bit = remaining & (-remaining)
            if (mask & ~bit) in members:
                is_minimal = False
                break
            remaining &= remaining - 1
        if is_minimal:
            minimal.append(mask)
    return sorted(minimal)

