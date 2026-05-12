import json
import sys
from pathlib import Path
import random
from datetime import datetime

# Allow running `python scripts/new_experiments.py` from repo root.
_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from helpers import computations
from helpers.types_of_wallets import (
    symmetric_wallet,
    symmetric_wallet_threshold,
    generate_single_bitmask,
)
from helpers import wallet_state
from helpers import optimal_symmetric_wallets
from helpers import constrained_probabilities
from helpers import wallet_enumerations
from helpers.consts import SAFE, LOST, LEAKED, STOLEN, KeyStateString
from helpers.wallet_cache import get_cached_static_wallets


def check_adding_comb_two_keys_under_optimal_symmetric_wallet(key_count = 5, quantity_of_cases = 50):
    probabilities = computations.generateKeyFaultProbabilityScenarios(step=0.01)
    probabilities = random.sample(probabilities, quantity_of_cases)
    for probability in probabilities:
        print(f"Processing probability {probability}")
        optimal_symmetric_wallet, optimal_success_probability, optimal_threshold = optimal_symmetric_wallets.find_optimal_symmetric_wallets(
            key_count, probability)
        if optimal_threshold <= 2:
            continue
        dictator_two_comb_lower = generate_single_bitmask(optimal_threshold - 2)
        dictator_wallet = wallet_state.WalletState(key_count, [dictator_two_comb_lower], probability)
        dictator_success_probability = dictator_wallet.compute_success_probability()

        dictator_wallet.remove_bitmask_and_subsets(dictator_two_comb_lower)
        dictator_success_probability_minus = dictator_wallet.compute_success_probability()

        if dictator_success_probability_minus < dictator_success_probability:
            print(f"The probability {probability} is a counterexample")

def make_list_of_probabilities():
    all_probabilities = computations.generateKeyFaultProbabilityScenarios(step=0.01)
    sampled_probabilities = random.sample(all_probabilities, 50)

    probability_cases = []
    for probabilities in sampled_probabilities:
        probabilities_by_name = {
            KeyStateString[state]: probability
            for state, probability in probabilities.items()
        }

        for key_count in range(3, 7):
            probability_cases.append({
                "key_count": key_count,
                "probabilities": probabilities_by_name,
                "message": "",
            })

            swapped_probabilities = {
                **probabilities_by_name,
                KeyStateString[LEAKED]: probabilities[LOST],
                KeyStateString[LOST]: probabilities[LEAKED],
            }
            probability_cases.append({
                "key_count": key_count,
                "probabilities": swapped_probabilities,
                "message": "LEAKED and LOST probabilities swapped",
            })

    output_path = _REPO_ROOT / "data" / "probabilities_list_exchange_leak_with_loss.json"
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(probability_cases, f, indent=2)

    return sampled_probabilities

def save_probabilities_and_every_wallet_performance(num_of_cases = 5000, key_count = 5):
    probabilities = computations.generateKeyFaultProbabilityScenarios(step=0.002)
    probabilities = random.sample(probabilities, num_of_cases)
    wallets = get_cached_static_wallets(key_count, deduplicate_by_architecture=True)
    results = []
    for probability in probabilities:
        print(f"Processing probability {probability}")
        optimal_symmetric_wallet, optimal_success_probability, optimal_threshold = optimal_symmetric_wallets.find_optimal_symmetric_wallets(
            key_count, probability)
        
        results.append({
            "probability": probability,
            "optimal_symmetric_threshold": optimal_threshold,
            "wallets": []
        })
        for wallet in wallets:
            wallet_state_object = wallet_state.WalletState(key_count, wallet, probability)
            success_probability = wallet_state_object.compute_success_probability()
            results[-1]["wallets"].append({
                "wallet": wallet,
                "success_probability": success_probability
            })
    with open(f"data/probabilities_and_every_wallet_performance_{key_count}_keys_{num_of_cases}_cases.json", "w") as f:
        json.dump(results, f, indent=2)

def _repo_path(path):
    path = Path(path)
    return path if path.is_absolute() else _REPO_ROOT / path


def _key_count_from_filename(input_path):
    stem_before_keys = input_path.stem.split("_keys_")[0]
    return stem_before_keys.rsplit("_", 1)[-1]


def _split_output_path(output_dir, input_path):
    key_count = _key_count_from_filename(input_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"{key_count}_keys_{timestamp}"

    suffix = 2
    while output_path.exists():
        output_path = output_dir / f"{key_count}_keys_{timestamp}_{suffix}"
        suffix += 1

    return output_path


def _optimal_symmetric_threshold(result, input_path):
    threshold = result.get("optimal_symmetric_threshold")
    if threshold is not None:
        return threshold

    optimal_wallet = result.get("optimal_symmetric_wallet")
    if optimal_wallet is None:
        raise ValueError(
            f"Missing optimal_symmetric_threshold in case from {input_path}"
        )

    return symmetric_wallet_threshold(optimal_wallet)


def separate_by_optimal_symmetric_threshold(path, output_dir="rankings"):
    input_path = _repo_path(path)
    rankings_path = _repo_path(output_dir)
    output_path = _split_output_path(rankings_path, input_path)
    output_path.mkdir(parents=True, exist_ok=True)

    with input_path.open("r", encoding="utf-8") as f:
        results = json.load(f)

    unpartitioned_path = output_path / input_path.name
    with unpartitioned_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    results_by_threshold = {}
    for result in results:
        optimal_threshold = _optimal_symmetric_threshold(result, input_path)
        result["optimal_symmetric_threshold"] = optimal_threshold
        result.pop("optimal_symmetric_wallet", None)
        results_by_threshold.setdefault(optimal_threshold, []).append(result)

    for optimal_threshold, cases in sorted(results_by_threshold.items()):
        group_path = (
            output_path
            / f"{input_path.stem}_optimal_symmetric_threshold_{optimal_threshold}_{len(cases)}_cases.json"
        )
        with group_path.open("w", encoding="utf-8") as f:
            json.dump(cases, f, indent=2)


def separate_by_optimal_symmetric_wallet(path, output_dir="rankings"):
    separate_by_optimal_symmetric_threshold(path, output_dir)

def main():
    separate_by_optimal_symmetric_wallet(
        "data/probabilities_and_every_wallet_performance_5_keys_5000_cases.json"
    )
    
if __name__ == "__main__":
    main()