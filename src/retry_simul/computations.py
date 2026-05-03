import math

from .consts import SAFE, LOST, LEAKED, STOLEN
from .wallet_enumerations import enumerateStates, ownerAdvKeysFromStates, isCovered, walletStr
from .wallet_cache import get_cached_static_wallets


def computeSuccessProbability(wallet, ownerStates, advStates, probabilities):
    """Compute success probability for a wallet given pre-computed states and probabilities.

    Args:
        wallet: wallet to evaluate
        ownerStates: list of owner key combinations for each state
        advStates: list of adversary key combinations for each state
        probabilities: list of probabilities for each state

    Success is defined as: owner can access (covers at least one combination)
    AND adversary cannot access (covers none of the combinations).
    """
    terms = []
    for i in range(len(probabilities)):
        owner_ok = isCovered(ownerStates[i], wallet)
        adv_ok = isCovered(advStates[i], wallet)
        if owner_ok and not adv_ok:
            terms.append(probabilities[i])
    return math.fsum(terms)


def computeSuccessProbabilityWithForbiddenTerm(
    wallet, forbidden_term, ownerStates, advStates, probabilities
):
    """Compute success probability with a forbidden term.

    Success is defined as: owner can access AND adversary cannot access.
    If either party covers the forbidden_term, they are treated as if they
    cannot access.
    """
    if forbidden_term is None:
        return computeSuccessProbability(wallet, ownerStates, advStates, probabilities)

    terms = []
    for i in range(len(probabilities)):
        owner_forbidden = ownerStates[i] == forbidden_term
        adv_forbidden = advStates[i] == forbidden_term

        owner_ok = isCovered(ownerStates[i], wallet)
        adv_ok = isCovered(advStates[i], wallet)
        if owner_forbidden:
            owner_ok = False
        if adv_forbidden:
            adv_ok = False
        if owner_ok and not adv_ok:
            terms.append(probabilities[i])
    return math.fsum(terms)


def findOptimalWallet(wallets, keyCount, keyStateProbabilities):
    """Return (best_wallets, best_success_probability)."""
    # Compute states once for all wallets
    states, state_probabilities = enumerateStates(keyCount, keyStateProbabilities)
    ownerStates, advStates = ownerAdvKeysFromStates(states)

    best_wallets = []
    best_prob = -1.0
    for wallet in wallets:
        p = computeSuccessProbability(wallet, ownerStates, advStates, state_probabilities)
        if abs(p - best_prob) < 1e-12:  # Equal probability (within floating point tolerance)
            best_wallets.append(wallet)
        elif p > best_prob:
            best_prob = p
            best_wallets = [wallet]  # Start new list with this wallet

    return best_wallets, best_prob


def generateKeyFaultProbabilityScenarios(step=0.05, include_zero=True):
    """Generate probability scenarios on an exact integer grid that sum to 1.

    - step: grid granularity (e.g., 0.5, 0.25, 0.2, 0.1)
    - include_zero: if False, excludes scenarios where any probability is 0.0
    Constraint: SAFE probability must be strictly greater than STOLEN probability.
    """
    if step <= 0 or step > 1:
        raise ValueError("step must be in (0, 1]")
    # Use integer grid to avoid floating drift: a+b+c+d = n, probabilities = a/n, ...
    n_float = 1.0 / step
    n = int(round(n_float))
    if abs(n - n_float) > 1e-9:
        # Guard: step must evenly divide 1.0 for an exact grid
        raise ValueError("step must evenly divide 1.0 (e.g., 0.5, 0.25, 0.2, 0.1)")

    scenarios = []
    for a in range(0, n + 1):  # SAFE
        for b in range(n - a + 1):  # LOST
            for c in range(n - a - b + 1):  # LEAKED
                d = n - (a + b + c)  # STOLEN

                # Convert to exact floats via division by n
                p_safe = a / n
                p_lost = b / n
                p_leaked = c / n
                p_stolen = d / n

                # Enforce positivity constraints if requested
                if not include_zero and (
                    p_safe == 0.0 or p_lost == 0.0 or p_leaked == 0.0 or p_stolen == 0.0
                ):
                    continue

                # Constraint: only keep scenarios where SAFE > STOLEN
                if p_safe <= p_stolen:
                    continue

                scenarios.append(
                    {
                        SAFE: p_safe,
                        LOST: p_lost,
                        LEAKED: p_leaked,
                        STOLEN: p_stolen,
                    }
                )
    return scenarios


def reportOptimalWalletsForProbabilities(
    probabilities_list,
    keyCount,
    deduplicate_by_architecture=True,
    print_fn=print,
):
    """For each probabilities dict in the list, print and return the best wallet."""
    # Generate wallets once for all probability scenarios
    wallets = get_cached_static_wallets(
        keyCount, deduplicate_by_architecture=deduplicate_by_architecture
    )

    results = []
    for idx, probs in enumerate(probabilities_list):
        # Basic validation: ensure probabilities sum to ~1
        total = (
            probs.get(SAFE, 0.0)
            + probs.get(LOST, 0.0)
            + probs.get(LEAKED, 0.0)
            + probs.get(STOLEN, 0.0)
        )
        if abs(total - 1.0) > 1e-9:
            raise ValueError(f"probabilities at index {idx} must sum to 1.0 (got {total})")

        optimal_wallets, best_p = findOptimalWallet(wallets, keyCount, probs)
        # Format multiple wallets if there are ties
        if len(optimal_wallets) == 1:
            wallet_str = walletStr(optimal_wallets[0])
        else:
            wallet_strs = [walletStr(w) for w in optimal_wallets]
            wallet_str = f"[{len(optimal_wallets)} wallets: {', '.join(wallet_strs)}]"
        print_fn(
            f"Case {idx}: best_success_probability={best_p:.6f}, wallet(s)={wallet_str}, probs={probs}"
        )
        results.append((optimal_wallets, best_p, probs))
    return results


def main():
    findOptimalWallet()

