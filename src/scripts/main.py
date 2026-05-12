import random

from helpers import computations
from helpers.consts import SAFE, LOST, LEAKED, STOLEN

from scripts import experiments
from scripts.plot_utils import plot_key_count_distributions
from scripts.wallet_visualizer import run_visualizer
from helpers.wallet_state import WalletState


def main():
    # Dictator-set counterexample search + launch the visualizer on the first hit.
    keyCount = 8
    out = experiments.check_dictator_sets(keyCount=keyCount, step=0.02, sample_size=500, seed=0)
    if out is None:
        return

    probability = out["probability"]
    wallet_prev = out["wallet_prev"]
    wallet_curr = out["wallet_curr"]
    print("Dictator-set improvement found:")
    print(f"keyCount={out['keyCount']}, k_prev={out['k_prev']}, k_curr={out['k_curr']}")
    print(f"p_prev={out['p_prev']:.12f}, p_curr={out['p_curr']:.12f}")
    print(f"wallet_prev={wallet_prev}")
    print(f"wallet_curr={wallet_curr}")

    # Open the visualizer with the improved wallet preloaded.
    base_wallet = WalletState(out["keyCount"], list(wallet_curr), probability)
    run_visualizer(key_count=out["keyCount"], probabilities=probability, base_wallet=base_wallet, orientation="rows")


if __name__ == "__main__":
    main()

