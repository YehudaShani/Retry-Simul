from math import comb

from retry_simul.consts import LEAKED, SAFE, STOLEN, LOST
from retry_simul import gain_breakdown


def binomial_cdf(n, k, p):
    return sum(comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k + 1))


def binomial_pmf(n, k, p):
    return comb(n, k) * p ** k * (1 - p) ** (n - k)


def calculate_prob_attacker_under_given_user_amount(key_count, user_amount, probabilities):
    # Calculate Pr(A <= user_amount - 1 | U = user_amount)
    alpha = probabilities[LEAKED] / (probabilities[LEAKED] + probabilities[SAFE])
    beta = probabilities[STOLEN] / (probabilities[STOLEN] + probabilities[LOST])

    probability = 0

    for amount_of_leaked_keys in range(user_amount + 1):  # amount of possible leaked keys
        for amount_of_stolen_keys in range(
            key_count - user_amount + 1
        ):  # amount of possible stolen keys
            if amount_of_leaked_keys + amount_of_stolen_keys <= user_amount - 1:
                probability += binomial_pmf(user_amount, amount_of_leaked_keys, alpha) * binomial_pmf(
                    key_count - user_amount, amount_of_stolen_keys, beta
                )
    return probability


def user_prob_under_given_attacker_amount(
    key_count, attacker_amount, probabilities, add=1, remove_prob_they_have_same_keys=False
):

    gamma = probabilities[LEAKED] / (probabilities[LEAKED] + probabilities[STOLEN])
    mu = probabilities[SAFE] / (probabilities[SAFE] + probabilities[LOST])

    probability = 0

    for amount_of_leaked_keys in range(attacker_amount + 1):  # amount of possible leaked keys
        for amount_of_safe_keys in range(
            key_count - attacker_amount + 1
        ):  # amount of possible safe keys
            if amount_of_leaked_keys + amount_of_safe_keys >= attacker_amount + add:
                probability += binomial_pmf(attacker_amount, amount_of_leaked_keys, gamma) * binomial_pmf(
                    key_count - attacker_amount, amount_of_safe_keys, mu
                )

    if remove_prob_they_have_same_keys:
        probability -= probabilities[LEAKED] ** attacker_amount * probabilities[LOST] ** (
            key_count - attacker_amount
        )
    return probability


def prob_user_has_k_keys(key_count, k, probabilities):
    return binomial_pmf(key_count, k, probabilities[SAFE] + probabilities[LEAKED])


def prob_attacker_has_k_keys(key_count, k, probabilities):
    return binomial_pmf(key_count, k, probabilities[STOLEN] + probabilities[LOST])

