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



def main():
    experiments.check_if_every_added_combination_to_previous_symmetric_increases_success_probability()



if __name__ == "__main__":
    main()