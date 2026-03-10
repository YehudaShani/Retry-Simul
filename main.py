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
from plot_utils import plot_symmetric_success_wallets



def main():
    result = experiments.check_if_symmetric_wallets_are_concave()
    if result is None:
        print("No result found")
    else:
        probability, middle_threshold, success_by_threshold, second_difference = result
        print(f"Counterexample probability: {probability}")
        print(f"Middle threshold: {middle_threshold}")
        print(f"Second difference: {second_difference}")
        plot_symmetric_success_wallets(
            success_by_threshold,
            title=f"Concavity counterexample at threshold {middle_threshold}",
        )


if __name__ == "__main__":
    main()