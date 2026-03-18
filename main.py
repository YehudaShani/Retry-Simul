import computations
import wallet_enumerations
from consts import SAFE, LOST, LEAKED, STOLEN
from types_of_wallets import symmetric_wallet, generate_all_bitmasks
import optimal_symmetric_wallets
import wallet_differences
import wallet_state
import types_of_wallets
import random
import json
import constrained_probabilities
import experiments
import wallet_visualizer
from plot_utils import plot_key_count_distributions



def main():
    keyCount = 6
    probabilities = computations.generateKeyFaultProbabilityScenarios(step=0.05)
    sampled_probabilities = random.sample(probabilities, min(3, len(probabilities)))

    for index, probability in enumerate(sampled_probabilities, start=1):
        result = experiments.build_key_count_distributions_with_optimal_threshold(keyCount, probability)
        title = (
            f"Scenario {index}/3 | "
            f"SAFE={probability[SAFE]:.2f}, LOST={probability[LOST]:.2f}, "
            f"LEAKED={probability[LEAKED]:.2f}, STOLEN={probability[STOLEN]:.2f}"
        )
        plot_key_count_distributions(
            result["user_key_count_probabilities"],
            result["attacker_key_count_probabilities"],
            result["success_by_threshold"],
            result["optimal_threshold"],
            title=title,
        )


if __name__ == "__main__":
    main()