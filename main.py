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



def main():
    key_count, probabilities, wallet = experiments.check_if_adding_combs_to_symmetric_wallet_relative_to_optimal_symmetric(0, 1)
    wallet_visualizer.run_visualizer(key_count, probabilities, wallet)


if __name__ == "__main__":
    main()