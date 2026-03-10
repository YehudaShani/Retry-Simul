import json
import computations
from types_of_wallets import symmetric_wallet, generate_single_bitmask
import wallet_state
import optimal_symmetric_wallets
import constrained_probabilities
import wallet_enumerations
import random
from consts import SAFE, LOST, LEAKED, STOLEN


def check_sequential_combinations(counterexample=True):
    keyCount = 5
    probabilities = computations.generateKeyFaultProbabilityScenarios(step=0.02)
    probabilities = random.sample(probabilities, 200)
    #probabilities = [{SAFE: 0.2, LOST: 0.32, LEAKED: 0.48, STOLEN: 0}]

    #save a list of the wallets that stopped at each bitmask
    stopped_at_bitmasks = []

    for index, probability in enumerate(probabilities):
        print(f"Processing probability {index} of {len(probabilities)}")
        optimal_wallet, optimal_success_probability, optimal_threshold = optimal_symmetric_wallets.find_optimal_symmetric_wallets(
            keyCount, probability)
        baseline_wallet = wallet_state.WalletState(keyCount, [], probability)
        if optimal_threshold == keyCount:
            continue

        #dont forget to add 1 to the threshold
        else:
            wallet_bitmasks, wallet_stopped_at_bitmask, wallet_success_probability = baseline_wallet.fill_up_to_threshold(
                optimal_threshold + 1)

        if wallet_stopped_at_bitmask is not None:
            #save the optimal symmetric wallet as well
            stopped_at_bitmasks.append(
                [wallet_bitmasks, wallet_stopped_at_bitmask, wallet_success_probability, optimal_wallet])
            print("The optimal symmetric wallet is: ", optimal_wallet)
            print("with success probability: ", optimal_success_probability)
            print("Th wallet bitmasks are: ", wallet_bitmasks)
            print("The wallet stopped at bitmask: ", wallet_stopped_at_bitmask)
            print("The wallet success probability is: ", wallet_success_probability)
            print("--------------------------------")
            print("--------------------------------")

            if counterexample:
                return


def check_if_adding_comb_after_optimal_threshold_increases_success_probability():
    keyCount = 6
    probabilities = computations.generateKeyFaultProbabilityScenarios(step=0.02)
    probabilities = random.sample(probabilities, 200)
    for probability in probabilities:
        print(f"Processing probability {probability}")
        states, state_probabilities = wallet_enumerations.enumerateStates(keyCount, probability)
        owner_states, adversary_states = wallet_enumerations.ownerAdvKeysFromStates(states)
        optimal_symmetric_wallet, optimal_success_probability, optimal_threshold = optimal_symmetric_wallets.find_optimal_symmetric_wallets(
            keyCount, probability)
        if optimal_threshold >= keyCount:
            continue
        next_layer_symmetric_wallet = symmetric_wallet(keyCount, optimal_threshold + 1)
        wallet = wallet_state.WalletState(keyCount, next_layer_symmetric_wallet, probability)
        new_bitmask = generate_single_bitmask(optimal_threshold + 1)
        wallet.add_bitmask(new_bitmask)
        new_success_probability = wallet.compute_success_probability()
        if new_success_probability > optimal_success_probability:
            print("The optimal symmetric wallet is: threshold ", optimal_threshold, " with bitmasks ",
                  optimal_symmetric_wallet)
            print("with success probability: ", optimal_success_probability)
            print("The new bitmask is: ", new_bitmask)
            print("The new success probability is: ", new_success_probability)
            print("--------------------------------")
            print("--------------------------------")
            return

    return


def check_if_adding_combs_to_symmetric_wallet_relative_to_optimal_symmetric(symmetric_layer_from_optimal=1,
                                                                            layer_from_optimal_to_start_checking_combs=1):
    # Finds the k symmetric optimal, generates a new symmetric wallet with threshold t above the optimal. Removes
    # combinations of sizes k+2, k+3, ... and their subsets, then checks if adding them increases the success
    # probability.

    keyCount = 7
    probabilities = computations.generateKeyFaultProbabilityScenarios(step=0.01)
    probabilities = random.sample(probabilities, 2000)
    #probabilities = [{1: 0.14, 2: 0.02, 3: 0.78, 4: 0.06}]
    for probability in probabilities:
        print(f"Processing probability {probability}")
        optimal_symmetric_wallet, optimal_success_probability, optimal_threshold = optimal_symmetric_wallets.find_optimal_symmetric_wallets(
            keyCount, probability)
        if optimal_threshold + symmetric_layer_from_optimal > keyCount:
            continue

        symmetric_wallet_from_optimal = symmetric_wallet(keyCount, optimal_threshold + symmetric_layer_from_optimal)
        minimum_layer_to_check = min(keyCount, optimal_threshold + layer_from_optimal_to_start_checking_combs)

        for layer in range(minimum_layer_to_check, keyCount + 1):
            base_wallet = wallet_state.WalletState(keyCount, symmetric_wallet_from_optimal, probability)
            bitmask_to_remove = generate_single_bitmask(layer)
            base_wallet.remove_bitmask_and_subsets(bitmask_to_remove)
            success_probability_without_bitmask = base_wallet.compute_success_probability()
            base_wallet.add_bitmask(bitmask_to_remove)
            success_probability_with_bitmask = base_wallet.compute_success_probability()
            print(f"The difference in success probability is {success_probability_with_bitmask - success_probability_without_bitmask}")
            if success_probability_with_bitmask < success_probability_without_bitmask:
                print("The optimal symmetric threshold is", optimal_threshold, " with bitmasks ", )
                print("with success probability: ", optimal_success_probability)
                print("The layer we are checking is: ", layer)
                print("The bitmask is: ", bitmask_to_remove)
                print("The success probability without the bitmask is: ", success_probability_without_bitmask)
                print("The success probability with the bitmask is: ", success_probability_with_bitmask)
                print("--------------------------------")
                print("--------------------------------")
                return keyCount, probability, base_wallet



def check_if_every_added_combination_to_previous_symmetric_increases_success_probability():
    keyCount = 8
    probabilities = computations.generateKeyFaultProbabilityScenarios(step=0.01)
    probabilities = random.sample(probabilities, 200)
    #probabilities = [{1: 0.14, 2: 0.02, 3: 0.78, 4: 0.06}]
    for probability in probabilities:
        print(f"Processing probability {probability}")
        states, state_probabilities = wallet_enumerations.enumerateStates(keyCount, probability)
        owner_states, adversary_states = wallet_enumerations.ownerAdvKeysFromStates(states)
        optimal_symmetric_wallet, optimal_success_probability, optimal_threshold = optimal_symmetric_wallets.find_optimal_symmetric_wallets(
            keyCount, probability)
        if optimal_threshold <= 1:
            continue
        previous_layer_symmetric_wallet = symmetric_wallet(keyCount, optimal_threshold - 1)
        for layer in range(optimal_threshold + 2, keyCount + 1):
            base_wallet = wallet_state.WalletState(keyCount, previous_layer_symmetric_wallet, probability)
            bitmask_to_remove = generate_single_bitmask(layer)
            base_wallet.remove_bitmask_and_subsets(bitmask_to_remove)
            success_probability_without_bitmask = base_wallet.compute_success_probability()
            base_wallet.add_bitmask(bitmask_to_remove)
            success_probability_with_bitmask = base_wallet.compute_success_probability()
            if success_probability_with_bitmask < success_probability_without_bitmask:
                print("The optimal symmetric threshold is", optimal_threshold, " with bitmasks ", )
                print("with success probability: ", optimal_success_probability)
                print("The layer we are checking is: ", layer)
                print("The bitmask is: ", bitmask_to_remove)
                print("The success probability without the bitmask is: ", success_probability_without_bitmask)
                print("The success probability with the bitmask is: ", success_probability_with_bitmask)
                print("--------------------------------")
                print("--------------------------------")
                break


def check_if_every_added_combination_to_or_wallet_increases_success_probability():
    #False
    keyCount = 7
    probabilities = computations.generateKeyFaultProbabilityScenarios(step=0.01)
    probabilities = random.sample(probabilities, 200)
    #probabilities = [{1: 0.14, 2: 0.02, 3: 0.78, 4: 0.06}]
    for probability in probabilities:
        print(f"Processing probability {probability}")
        states, state_probabilities = wallet_enumerations.enumerateStates(keyCount, probability)
        owner_states, adversary_states = wallet_enumerations.ownerAdvKeysFromStates(states)
        optimal_symmetric_wallet, optimal_success_probability, optimal_threshold = optimal_symmetric_wallets.find_optimal_symmetric_wallets(
            keyCount, probability)
        if optimal_threshold <= 1:
            continue
        or_symmetric_wallet = symmetric_wallet(keyCount, 1)
        for layer in range(optimal_threshold + 2, keyCount + 1):
            base_wallet = wallet_state.WalletState(keyCount, or_symmetric_wallet, probability)
            bitmask_to_remove = generate_single_bitmask(layer)
            base_wallet.remove_bitmask_and_subsets(bitmask_to_remove)
            success_probability_without_bitmask = base_wallet.compute_success_probability()
            base_wallet.add_bitmask(bitmask_to_remove)
            success_probability_with_bitmask = base_wallet.compute_success_probability()
            if success_probability_with_bitmask < success_probability_without_bitmask:
                print("The optimal symmetric threshold is", optimal_threshold, " with bitmasks ", )
                print("with success probability: ", optimal_success_probability)
                print("The layer we are checking is: ", layer)
                print("The bitmask is: ", bitmask_to_remove)
                print("The success probability without the bitmask is: ", success_probability_without_bitmask)
                print("The success probability with the bitmask is: ", success_probability_with_bitmask)
                print("--------------------------------")
                print("--------------------------------")
                break

def check_adding_on_borders(): 
    keyCount = 7
    probabilities = computations.generateKeyFaultProbabilityScenarios(step=0.0025)
    probabilities = random.sample(probabilities, 2000)
    for probability in probabilities:
        print(f"Processing probability {probability}")
        for layer in range(keyCount - 1, 1, -1):
            symmetric_k_wallet = symmetric_wallet(keyCount, layer)

            # check if adding the last bitmask increased success
            wallet_without_last_bitmask = wallet_state.WalletState(keyCount, symmetric_k_wallet, probability)
            wallet_without_last_bitmask.remove_bitmask_and_subsets(generate_single_bitmask(layer)) # should do the same as removing just one
            success_probability_without_last_bitmask = wallet_without_last_bitmask.compute_success_probability()

            wallet_with_last_bitmask = wallet_state.WalletState(keyCount, symmetric_k_wallet, probability)
            success_probability_with_last_bitmask = wallet_with_last_bitmask.compute_success_probability()

            wallet_with_extra_bitmask = wallet_state.WalletState(keyCount, symmetric_k_wallet, probability)
            wallet_with_extra_bitmask.add_bitmask(generate_single_bitmask(layer - 1))
            success_probability_with_extra_bitmask = wallet_with_extra_bitmask.compute_success_probability()

            k_layer_improved = success_probability_with_last_bitmask > success_probability_without_last_bitmask
            k_minus_one_layer_improved = success_probability_with_extra_bitmask > success_probability_with_last_bitmask

            if not k_layer_improved and k_minus_one_layer_improved:
                print(f"The probability {probability} is a counterexample, on layer {layer}")
                return probability, layer


def check_if_symmetric_wallets_are_concave(
    keyCount=7,
    step=0.01,
    sample_size=2000,
    tol=1e-12,
):
    """Check whether symmetric-wallet success is concave in the threshold.

    For each sampled probability scenario, compute the success sequence
    S(1), S(2), ..., S(keyCount), where S(k) is the success probability of the
    k-of-n symmetric wallet. Concavity means:

        S(k - 1) - 2 * S(k) + S(k + 1) <= 0

    for every interior threshold k.

    Returns:
        None if no counterexample is found.
        Otherwise returns a tuple:
        (probability, middle_threshold, success_by_threshold, second_difference)
    """
    probabilities = computations.generateKeyFaultProbabilityScenarios(step=step)
    probabilities = random.sample(probabilities, min(sample_size, len(probabilities)))

    for probability in probabilities:
        print(f"Processing probability {probability}")
        states, state_probabilities = wallet_enumerations.enumerateStates(keyCount, probability)
        owner_states, adversary_states = wallet_enumerations.ownerAdvKeysFromStates(states)

        success_by_threshold = []
        for threshold in range(1, keyCount + 1):
            wallet = symmetric_wallet(keyCount, threshold)
            success_probability = computations.computeSuccessProbability(
                wallet, owner_states, adversary_states, state_probabilities
            )
            success_by_threshold.append(success_probability)

        for idx in range(1, keyCount - 1):
            left = success_by_threshold[idx - 1]
            middle = success_by_threshold[idx]
            right = success_by_threshold[idx + 1]
            second_difference = left - 2 * middle + right

            if second_difference > tol:
                middle_threshold = idx + 1
                print(f"Concavity failed for probability {probability}")
                print(f"At middle threshold {middle_threshold}")
                print(f"Success sequence: {success_by_threshold}")
                print(f"Second difference: {second_difference}")
                return probability, middle_threshold, success_by_threshold, second_difference

    print("No concavity counterexample found.")
    return None


def check_L_ratio_R_ratio():
    keyCount = 3
    probabilities = computations.generateKeyFaultProbabilityScenarios(step=0.02)
    probabilities = random.sample(probabilities, 1000)
    probabilities = [{SAFE: 0.2, LOST: 0.32, LEAKED: 0.48, STOLEN: 0}]
    for probability in probabilities:
        print(f"Processing probability {probability}")
        states, state_probabilities = wallet_enumerations.enumerateStates(keyCount, probability)
        owner_states, adversary_states = wallet_enumerations.ownerAdvKeysFromStates(states)
        k = optimal_symmetric_wallets.find_optimal_symmetric_wallets(keyCount, probability)[2]
        print(f"The optimal threshold is {k}")
        if k == keyCount:
            continue

        L_top = constrained_probabilities.constrain_amount_of_keys(
            owner_states, adversary_states, state_probabilities, [k + 1], range(0, k + 1)
        )
        L_bottom = constrained_probabilities.constrain_amount_of_keys(
            owner_states, adversary_states, state_probabilities, [k], range(0, k + 1)
        )
        if L_bottom == 0:
            continue
        L_ratio = L_top / L_bottom
        print(f"The ratio of L_top to L_bottom is {L_ratio}")
        R_top = constrained_probabilities.constrain_amount_of_keys(
            owner_states, adversary_states, state_probabilities, range(k + 1, keyCount + 1), [k + 1]
        )
        R_bottom = constrained_probabilities.constrain_amount_of_keys(
            owner_states, adversary_states, state_probabilities, range(k + 1, keyCount + 1), [k]
        )
        if R_bottom == 0:
            continue
        R_ratio = R_top / R_bottom
        print(f"The ratio of R_top to R_bottom is {R_ratio}")
        if L_ratio < R_ratio:
            return

def main(): 
     check_if_symmetric_wallets_are_concave()


if __name__ == "__main__":
    main()