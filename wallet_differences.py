"""Wallet difference analysis: find cases where removing a combination diminishes success."""
import computations
import wallet_enumerations
import optimal_symmetric_wallets
from types_of_wallets import symmetric_wallet, generate_single_bitmask


def calculate_wallet_differences(
    probabilities_list: list,
    key_count: int,
):
    """For each probability set, find symmetric optimal k, use k+1 wallet, check if forbidding
    one combination per layer (k+1 to key_count) increases success probability.

    Returns the first counterexample found (success_forbidden > success_full): the term hurts the wallet.
    Returns (probabilities, k, layer, bitmask, success_full, success_forbidden), or None if none found.
    """
    for probabilities in probabilities_list:
        opt_wallet, opt_prob, k = optimal_symmetric_wallets.find_optimal_symmetric_wallets(
            key_count, probabilities
        )
        if k>= key_count:
            continue
        wallet = symmetric_wallet(key_count, k + 1)
        states, state_probs = wallet_enumerations.enumerateStates(key_count, probabilities)
        owner_states, adv_states = wallet_enumerations.ownerAdvKeysFromStates(states)

        success_full = computations.computeSuccessProbability(
            wallet, owner_states, adv_states, state_probs
        )

        for layer in range(k + 1, key_count):
            bitmask = generate_single_bitmask(layer)
            success_forbidden = computations.computeSuccessProbabilityWithForbiddenTerm(
                wallet, bitmask, owner_states, adv_states, state_probs
            )
            if success_forbidden > success_full:
                return (
                    probabilities,
                    k,
                    layer,
                    bitmask,
                    success_full,
                    success_forbidden,
                )
    return None

if __name__ == "__main__":
    import random

    key_count = 6
    probabilities_list = computations.generateKeyFaultProbabilityScenarios(step=0.02)
    probabilities_list = random.sample(probabilities_list, min(1000, len(probabilities_list)))
    result = calculate_wallet_differences(probabilities_list, key_count)
    if result:
        probs, k, layer, bitmask, success_full, success_forbidden = result
        print(f"Found: probs={probs}, k={k}, layer={layer}, bitmask={bitmask}")
        print(f"  success_full={success_full:.6f}, success_forbidden={success_forbidden:.6f}")
    else:
        print("No counterexample found.")