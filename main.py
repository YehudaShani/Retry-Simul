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

def main():
    keyCount = 7
    probabilities = computations.generateKeyFaultProbabilityScenarios(step=0.02)
    #probabilities = random.sample(probabilities, 3000)

    #save a list of the wallets that stopped at each bitmask
    stopped_at_bitmasks = []

    for index, probability in enumerate(probabilities):
        print(f"Processing probability {index} of {len(probabilities)}")
        optimal_wallet, optimal_success_probability, optimal_threshold = optimal_symmetric_wallets.find_optimal_symmetric_wallets(keyCount, probability)
        baseline_wallet = wallet_state.WalletState(keyCount, [], probability)
        if optimal_threshold == keyCount:
            continue
        else:   
            wallet_bitmasks, wallet_stopped_at_bitmask, wallet_success_probability = baseline_wallet.fill_up_to_threshold(optimal_threshold+1)

        if wallet_stopped_at_bitmask is not None:
            stopped_at_bitmasks.append([wallet_bitmasks, wallet_stopped_at_bitmask, wallet_success_probability])
            print("Baseline wallet bitmasks are: ", wallet_bitmasks)
            print("Baseline wallet stopped at bitmask: ", wallet_stopped_at_bitmask)
            print("Baseline wallet success probability is: ", wallet_success_probability)
            print("--------------------------------")

            print("Optimal wallet bitmasks are: ", optimal_wallet)
            print("Optimal wallet success probability is: ", optimal_success_probability)
            print("Optimal threshold is: ", optimal_threshold)
            print("--------------------------------")

            print("Probability is: ", probability)
            print("--------------------------------")
            print("--------------------------------")

        #save the list of stopped at bitmasks to a file
    with open('stopped_at_bitmasks.json', 'w') as f:
        json.dump(stopped_at_bitmasks, f)
        

if __name__ == "__main__":
    main()