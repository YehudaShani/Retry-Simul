import json
from helpers import computations
from helpers.types_of_wallets import symmetric_wallet, generate_single_bitmask
from helpers import wallet_state
from helpers import optimal_symmetric_wallets
from helpers import constrained_probabilities
from helpers import wallet_enumerations
from helpers.wallet_cache import get_cached_static_wallets
import random
from helpers.consts import SAFE, LOST, LEAKED, STOLEN


def build_symmetric_success_and_expected_keys(keyCount: int, probability: dict) -> dict:
    """Compute symmetric-wallet success by threshold and expected user/attacker keys.

    Returns a dictionary with the per-threshold success curve plus expectation
    values derived from the same enumerated state space.
    """
    states, state_probabilities = wallet_enumerations.enumerateStates(keyCount, probability)
    owner_states, adversary_states = wallet_enumerations.ownerAdvKeysFromStates(states)

    success_by_threshold = [0.0]
    for threshold in range(1, keyCount + 1):
        wallet = symmetric_wallet(keyCount, threshold)
        success_probability = computations.computeSuccessProbability(
            wallet, owner_states, adversary_states, state_probabilities
        )
        success_by_threshold.append(success_probability)

    expected_user_keys = sum(
        probability * owner_state.bit_count()
        for probability, owner_state in zip(state_probabilities, owner_states)
    )
    expected_attacker_keys = sum(
        probability * adversary_state.bit_count()
        for probability, adversary_state in zip(state_probabilities, adversary_states)
    )

    optimal_success = max(success_by_threshold)
    optimal_threshold = success_by_threshold.index(optimal_success)

    return {
        "thresholds": list(range(keyCount + 1)),
        "success_by_threshold": success_by_threshold,
        "expected_user_keys": expected_user_keys,
        "expected_attacker_keys": expected_attacker_keys,
        "optimal_threshold": optimal_threshold,
        "optimal_success": optimal_success,
        "probabilities": probability,
    }


def build_key_count_distributions_with_optimal_threshold(keyCount: int, probability: dict) -> dict:
    """Compute user/attacker key-count distributions and the optimal threshold."""
    states, state_probabilities = wallet_enumerations.enumerateStates(keyCount, probability)
    owner_states, adversary_states = wallet_enumerations.ownerAdvKeysFromStates(states)

    user_key_count_probabilities = [0.0] * (keyCount + 1)
    attacker_key_count_probabilities = [0.0] * (keyCount + 1)
    for state_probability, owner_state, adversary_state in zip(
        state_probabilities, owner_states, adversary_states
    ):
        user_key_count_probabilities[owner_state.bit_count()] += state_probability
        attacker_key_count_probabilities[adversary_state.bit_count()] += state_probability

    success_by_threshold = [0.0]
    for threshold in range(1, keyCount + 1):
        wallet = symmetric_wallet(keyCount, threshold)
        success_probability = computations.computeSuccessProbability(
            wallet, owner_states, adversary_states, state_probabilities
        )
        success_by_threshold.append(success_probability)

    _optimal_wallet, optimal_success, optimal_threshold = optimal_symmetric_wallets.find_optimal_symmetric_wallets(
        keyCount, probability
    )

    return {
        "key_counts": list(range(keyCount + 1)),
        "user_key_count_probabilities": user_key_count_probabilities,
        "attacker_key_count_probabilities": attacker_key_count_probabilities,
        "success_by_threshold": success_by_threshold,
        "optimal_threshold": optimal_threshold,
        "optimal_success": optimal_success,
        "probabilities": probability,
    }


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

    keyCount = 4
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


def check_if_adding_combs_to_symmetric_wallet_relative_to_optimal_symmetric_extra(symmetric_layer_from_optimal=1,
                                                                            layer_from_optimal_to_start_checking_combs=1):
    # Finds the k symmetric optimal, generates a new symmetric wallet with threshold t above the optimal. Removes
    # combinations of sizes k+2, k+3, ... and their subsets, then checks if adding them increases the success
    # probability.

    keyCount = 6
    probabilities = computations.generateKeyFaultProbabilityScenarios(step=0.005)
    probabilities = random.sample(probabilities, 2000)
    probabilities = [{1: 0.125, 2: 0.405, 3: 0.4, 4: 0.07}]
    for probability in probabilities:
        print(f"Processing probability {probability}")
        optimal_symmetric_wallet, optimal_success_probability, optimal_threshold = optimal_symmetric_wallets.find_optimal_symmetric_wallets(
            keyCount, probability)
        if optimal_threshold + symmetric_layer_from_optimal >= keyCount:
            continue

        symmetric_wallet_from_optimal = symmetric_wallet(keyCount, optimal_threshold + symmetric_layer_from_optimal)
        minimum_layer_to_check = min(keyCount, optimal_threshold + layer_from_optimal_to_start_checking_combs)

        for layer in range(minimum_layer_to_check, minimum_layer_to_check + 1):
            #Calculate probability both have the last bitmask, layer^leak * (keyCount-layer)^lost
            both_have_last_bitmask_probability = probability[LEAKED] ** layer * (probability[LOST]) ** (keyCount - layer)
            
            base_wallet = wallet_state.WalletState(keyCount, symmetric_wallet_from_optimal, probability)
            bitmask_to_remove = generate_single_bitmask(layer)
            base_wallet.remove_bitmask_and_subsets(bitmask_to_remove)
            success_probability_without_bitmask = base_wallet.compute_success_probability()
            base_wallet.add_bitmask(bitmask_to_remove)
            success_probability_with_bitmask = base_wallet.compute_success_probability()
            print(f"The difference in success probability is {success_probability_with_bitmask - success_probability_without_bitmask}")
            if success_probability_with_bitmask < success_probability_without_bitmask + both_have_last_bitmask_probability:
                print("The optimal symmetric threshold is", optimal_threshold, " with bitmasks ", )
                print("with success probability: ", optimal_success_probability)
                print("The layer we are checking is: ", layer)
                print("The bitmask is: ", bitmask_to_remove)
                print("The success probability without the bitmask is: ", success_probability_without_bitmask)
                print("The success probability with the bitmask is: ", success_probability_with_bitmask)
                print("--------------------------------")
                print("--------------------------------")
                return keyCount, probability, base_wallet


def check_adding_combs_to_one_key_wallet():
    """Compare success prob: one fixed single-key conjunction plus full layer vs same minus one layer term.

    Base wallet uses a **single** bitmask ``[1]`` (key 1 only) — not ``symmetric_wallet(keyCount, 1)``
    (OR over all keys). For each layer in ``range(keyCount, optimal_threshold, -1)``, merge that
    with all ``C(n, layer)`` terms; then remove **one** layer mask that does **not** include key 1
    (bit ``1``), using ``WalletState.remove_bitmask`` only — not ``remove_bitmask_and_subsets``,
    which first expands the wallet via supersets and would break this comparison.
    """
    keyCount = 7
    probabilities = computations.generateKeyFaultProbabilityScenarios(step=0.01)
    probabilities = random.sample(probabilities, 200)
    for probability in probabilities:
        print(f"Processing probability {probability}")
        _opt_sw, optimal_success_probability, optimal_threshold = (
            optimal_symmetric_wallets.find_optimal_symmetric_wallets(keyCount, probability)
        )
        key1_bit = 1
        one_key_bitmasks = [key1_bit]

        print(f"The optimal threshold is {optimal_threshold}")
        if optimal_threshold == keyCount:
            continue

        for layer in range(keyCount - 1, optimal_threshold, -1):
            layer_masks = symmetric_wallet(keyCount, layer)
            removed = (2 ** layer - 1) << 1
            if removed is None:
                continue

            full_bitmasks = list(dict.fromkeys(one_key_bitmasks + layer_masks))
            wallet_full = wallet_state.WalletState(keyCount, full_bitmasks, probability)
            p_full = wallet_full.compute_success_probability()

            w_minus = wallet_state.WalletState(keyCount, list(full_bitmasks), probability)
            n_before = len(w_minus.bitmasks)
            w_minus.remove_bitmask_and_subsets(removed)
            n_after = len(w_minus.bitmasks)
            if w_minus.bitmask_is_in_wallet(removed):
                raise RuntimeError("The bitmask is still in the wallet")
            p_minus = w_minus.compute_success_probability()
            if p_full < p_minus:
                print("Counterexample: full layer union has lower success than minus one term.")
                print("optimal_threshold", optimal_threshold, "optimal_success", optimal_success_probability)
                print("layer", layer, "removed_mask", removed)
                print("p_full", p_full, "p_minus", p_minus)
                print("full_bitmasks count", len(full_bitmasks))
                print("--------------------------------")
                return keyCount, probability, wallet_full, removed

    return None


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


def check_optimal_success_equal_odd_to_even_wallets(
    *,
    trials: int = 500,
    min_key_count: int = 1,
    max_key_count: int = 5,
    tol: float = 1e-12,
    seed: int | None = None,
):
    """Randomly sample psafe>0.5 with ploss=pleak=0 and check odd→even optimal success equality.

    For each trial:
      - Sample p_SAFE uniformly from (0.5, 1.0]
      - Set p_STOLEN = 1 - p_SAFE
      - Set p_LOST = p_LEAKED = 0

    For keyCount in [min_key_count..max_key_count], compute the optimal static-wallet success probability.
    Then assert that for each odd k with k+1 in range, optimal_success(k) == optimal_success(k+1)
    within ``tol``.

    Returns:
        None if no counterexample is found.
        Otherwise returns a dict describing the first counterexample.
    """
    if min_key_count < 1:
        raise ValueError("min_key_count must be >= 1")
    if max_key_count < min_key_count:
        raise ValueError("max_key_count must be >= min_key_count")
    if trials <= 0:
        raise ValueError("trials must be > 0")

    if seed is not None:
        random.seed(seed)

    wallets_by_k = {}
    for k in range(min_key_count, max_key_count + 1):
        wallets_by_k[k] = get_cached_static_wallets(k, deduplicate_by_architecture=True)

    odd_starts = [k for k in range(min_key_count, max_key_count) if (k % 2 == 1 and k + 1 <= max_key_count)]
    if not odd_starts:
        raise ValueError("No odd→even pairs exist in the requested key-count range.")

    for t in range(trials):
        p_safe = 0.5 + 0.5 * random.random()
        probability = {SAFE: p_safe, LOST: 0.0, LEAKED: 0.0, STOLEN: 1.0 - p_safe}

        best_prob_by_k = {}
        best_wallets_by_k = {}
        for k in range(min_key_count, max_key_count + 1):
            best_wallets, best_prob = computations.findOptimalWallet(wallets_by_k[k], k, probability)
            best_prob_by_k[k] = best_prob
            best_wallets_by_k[k] = best_wallets

        for k in odd_starts:
            a = best_prob_by_k[k]
            b = best_prob_by_k[k + 1]
            if abs(a - b) > tol:
                out = {
                    "trial": t,
                    "tol": tol,
                    "probability": probability,
                    "k_odd": k,
                    "k_even": k + 1,
                    "best_prob_odd": a,
                    "best_prob_even": b,
                    "best_wallets_odd": best_wallets_by_k[k],
                    "best_wallets_even": best_wallets_by_k[k + 1],
                }
                print("Counterexample found.")
                print(out)
                return out

    print(f"No counterexample found in {trials} trials (range {min_key_count}..{max_key_count}).")
    return None

def check_dictator_sets(
    *,
    keyCount: int = 8,
    step: float = 0.02,
    sample_size: int = 500,
    tol: float = 1e-12,
    seed: int | None = None,
):
    """Check dictator-set wallets {1}, {1,2}, ..., {1..n} and stop on first improvement.

    For a fixed ``keyCount = n``, consider the n wallets:
        W_k = {1..k}  for k=1..n
    Each wallet has a single bitmask term (a conjunction of the first k keys):
        mask_k = (1<<k) - 1

    For each sampled probability scenario, compute success probabilities
    p_k = P(success | wallet=[mask_k]) and stop if any step improves:
        p_k > p_{k-1} + tol

    Returns:
        None if no improvement is found in the sample.
        Otherwise returns a dict describing the first counterexample.
    """
    if keyCount < 1:
        raise ValueError("keyCount must be >= 1")
    if sample_size <= 0:
        raise ValueError("sample_size must be > 0")
    if seed is not None:
        random.seed(seed)

    probabilities = computations.generateKeyFaultProbabilityScenarios(step=step)
    probabilities = random.sample(probabilities, min(sample_size, len(probabilities)))

    dictator_wallets = [[(1 << k) - 1] for k in range(1, keyCount + 1)]

    for idx, probability in enumerate(probabilities):
        print(f"Processing probability {idx + 1} of {len(probabilities)}: {probability}")
        states, state_probabilities = wallet_enumerations.enumerateStates(keyCount, probability)
        owner_states, adversary_states = wallet_enumerations.ownerAdvKeysFromStates(states)

        prev_p: float | None = None
        prev_k: int | None = None
        for k, wallet in enumerate(dictator_wallets, start=1):
            p = computations.computeSuccessProbability(
                wallet, owner_states, adversary_states, state_probabilities
            )
            if prev_p is not None and p > prev_p + tol:
                out = {
                    "keyCount": keyCount,
                    "tol": tol,
                    "probability": probability,
                    "k_prev": prev_k,
                    "k_curr": k,
                    "wallet_prev": dictator_wallets[prev_k - 1],
                    "wallet_curr": wallet,
                    "p_prev": prev_p,
                    "p_curr": p,
                }
                print("Improvement found (counterexample).")
                print(out)
                return out
            prev_p = p
            prev_k = k

    print(f"No dictator-set improvement found in {len(probabilities)} sampled scenarios.")
    return None


def main(): 
     check_dictator_sets()


if __name__ == "__main__":
    main()

