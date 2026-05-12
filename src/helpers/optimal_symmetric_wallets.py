from .consts import SAFE, LOST, LEAKED, STOLEN
from . import computations
from . import wallet_enumerations
from .types_of_wallets import symmetric_wallet


def find_optimal_symmetric_wallets(keyCount, keyStateProbabilities, verbose=False):
    optimal_wallet = None
    optimal_success_probability = -1.0
    optimal_threshold = 0

    states, state_probabilities = wallet_enumerations.enumerateStates(
        keyCount, keyStateProbabilities
    )
    ownerStates, advStates = wallet_enumerations.ownerAdvKeysFromStates(states)

    for threshold in range(1, keyCount + 1):
        wallet = symmetric_wallet(keyCount, threshold)
        successProbability = computations.computeSuccessProbability(
            wallet, ownerStates, advStates, state_probabilities
        )
        if verbose:
            print(f"Threshold: {threshold}, Success probability: {successProbability}")
        if successProbability > optimal_success_probability:
            optimal_success_probability = successProbability
            optimal_wallet = wallet
            optimal_threshold = threshold

    return optimal_wallet, optimal_success_probability, optimal_threshold


def main():
    keyCount = 5
    probabilities = {SAFE: 0.425, LOST: 0.025, LEAKED: 0.15, STOLEN: 0.4}
    optimal_wallet, optimal_success_probability, optimal_threshold = (
        find_optimal_symmetric_wallets(keyCount, probabilities, verbose=True)
    )


if __name__ == "__main__":
    main()

