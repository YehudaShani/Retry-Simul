from tracemalloc import stop
import random

from scripts import paper_calculations
from retry_simul import optimal_symmetric_wallets
from retry_simul import computations


def calculate_attacker_conditional_ratios(key_count, probabilities, optimal_threshold):
    prob_under_k = paper_calculations.calculate_prob_attacker_under_given_user_amount(
        key_count, optimal_threshold, probabilities
    )

    prob_under_k_plus_1 = paper_calculations.calculate_prob_attacker_under_given_user_amount(
        key_count, optimal_threshold + 1, probabilities
    )

    return prob_under_k_plus_1 / prob_under_k


def calculate_user_conditional_ratios(key_count, probabilities, optimal_threshold):
    prob_under_k = paper_calculations.user_prob_under_given_attacker_amount(
        key_count, optimal_threshold, probabilities, add=1
    )
    prob_under_k_plus_1 = paper_calculations.user_prob_under_given_attacker_amount(
        key_count,
        optimal_threshold + 1,
        probabilities,
        add=0,
        remove_prob_they_have_same_keys=True,
    )

    return prob_under_k_plus_1 / prob_under_k


def calculate_user_amount_of_keys_ratio(key_count, probabilities, optimal_threshold):
    prob_user_has_k_keys = paper_calculations.prob_user_has_k_keys(
        key_count, optimal_threshold, probabilities
    )
    prob_user_has_k_plus_1_keys = paper_calculations.prob_user_has_k_keys(
        key_count, optimal_threshold + 1, probabilities
    )

    return prob_user_has_k_plus_1_keys / prob_user_has_k_keys


def calculate_attacker_amount_of_keys_ratio(key_count, probabilities, optimal_threshold):
    prob_attacker_has_k_keys = paper_calculations.prob_attacker_has_k_keys(
        key_count, optimal_threshold, probabilities
    )
    prob_attacker_has_k_plus_1_keys = paper_calculations.prob_attacker_has_k_keys(
        key_count, optimal_threshold + 1, probabilities
    )

    return prob_attacker_has_k_plus_1_keys / prob_attacker_has_k_keys


def main():
    key_count = 3
    # generate probabilities
    probabilities = computations.generateKeyFaultProbabilityScenarios(step=0.005)
    probabilities = random.sample(probabilities, 1000)
    stop = False
    for probability in probabilities:
        if stop:
            break
        optimal_threshold = optimal_symmetric_wallets.find_optimal_symmetric_wallets(
            key_count, probability
        )[2]
        if optimal_threshold == key_count:
            # Skip degenerate case
            continue
        print(f"Processing probability {probability}")
        attacker_ratio = 1 / calculate_attacker_conditional_ratios(
            key_count, probability, optimal_threshold
        )
        user_ratio = calculate_user_conditional_ratios(
            key_count, probability, optimal_threshold
        )

        user_amount_of_keys_ratio = calculate_user_amount_of_keys_ratio(
            key_count, probability, optimal_threshold
        )
        attacker_amount_of_keys_ratio = 1 / calculate_attacker_amount_of_keys_ratio(
            key_count, probability, optimal_threshold
        )

        total_ratio = (
            attacker_ratio * user_ratio * user_amount_of_keys_ratio * attacker_amount_of_keys_ratio
        )

        if total_ratio < 1:
            print(f"The probability {probability} is a counterexample")
            print(f"The total ratio is {total_ratio}")


if __name__ == "__main__":
    main()

