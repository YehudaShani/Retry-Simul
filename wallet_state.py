from dataclasses import dataclass
from typing import Iterable, List, Sequence, Dict
from consts import SAFE, LOST, LEAKED, STOLEN, KeyStates

import computations
import wallet_enumerations


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
        self.bitmasks.append(bitmask)

    def remove_bitmask(self, bitmask: int) -> None:
        if bitmask not in self.bitmasks:
            raise ValueError("bitmask not found in wallet state")
        self.bitmasks.remove(bitmask)

    def __str__(self) -> str:
        return (
            "The combinations in the wallet are: "
            f"{self.bitmasks} (key_count={self.key_count})"
        )


    def compute_success_probability(
        self, key_count: int | None = None
    ):
        states, state_probabilities = wallet_enumerations.enumerateStates(self.key_count, self.probabilities)
        owner_states, adv_states = wallet_enumerations.ownerAdvKeysFromStates(states)
        return computations.computeSuccessProbability(self.bitmasks, owner_states, adv_states, state_probabilities)


    def fill_up_to_threshold(self, threshold: int):
        # fill the wallet from the largest bitmask to smallest until all bitsmasks of size threshold are added
        # after every addition, check if the wallet success rate has increased. if not, print the wallet and break.
        for bitmask in range(2 ** self.key_count - 1, -1, -1):
            success_probability = self.compute_success_probability()
            if bin(bitmask).count('1') >= threshold:
                self.add_bitmask(bitmask)
                new_success_probability = self.compute_success_probability()
                if new_success_probability > success_probability:
                    success_probability = new_success_probability
                else:
                
                    return self.bitmasks, bitmask, success_probability
        
        return self.bitmasks, None, success_probability