import computations
import wallet_enumerations
from types_of_wallets import generate_all_bitmasks
from consts import SAFE, LOST, LEAKED, STOLEN

def calculate_wallet_differences(keyCount, optimal_wallet, ownerStates, advStates, state_probabilities):
    all_bitmasks = generate_all_bitmasks(keyCount)

    negative_differences = []

    for bitmask in all_bitmasks:
        if wallet_enumerations.isCovered(bitmask, optimal_wallet):
            success_probability = computations.computeSuccessProbability(optimal_wallet, ownerStates, advStates, state_probabilities)
            success_probability_with_forbidden_term = computations.computeSuccessProbabilityWithForbiddenTerm(optimal_wallet, bitmask, ownerStates, advStates, state_probabilities)
            #print(f"The bitmask is : ", bitmask)
            #print("The difference in success probability is : ", success_probability - success_probability_with_forbidden_term)

            #return all cases where the difference is negative
            if success_probability - success_probability_with_forbidden_term < 0:
                negative_differences.append((bitmask, success_probability - success_probability_with_forbidden_term))
    
    return negative_differences


