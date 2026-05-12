"""Plot helpers for symmetric wallet success curves."""

import json
import sys
from pathlib import Path
from typing import Mapping, Sequence

# Running this file directly does not put ``src/`` on sys.path; add it so ``helpers`` resolves.
_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import matplotlib.pyplot as plt

from helpers.consts import LOST, LEAKED, SAFE, STOLEN


def plot_symmetric_success_wallets(
    success_wallets: Sequence[float] | Mapping[str, Sequence[float]],
    title: str = "Symmetric Wallet Success by Threshold",
    show: bool = True,
    save_path: str | None = None,
):
    """Plot one or more symmetric-wallet success curves."""
    if isinstance(success_wallets, Mapping):
        curves = [(label, list(values)) for label, values in success_wallets.items()]
    else:
        curves = [("success", list(success_wallets))]

    fig, ax = plt.subplots(figsize=(8, 5))

    for label, values in curves:
        thresholds = list(range(1, len(values) + 1))
        ax.plot(thresholds, values, marker="o", label=label)

    ax.set_xlabel("Threshold")
    ax.set_ylabel("Success probability")
    ax.set_title(title)
    ax.grid(True, alpha=0.3)

    if len(curves) > 1:
        ax.legend()

    if save_path:
        fig.savefig(Path(save_path), bbox_inches="tight")

    if show:
        plt.show()

    return fig, ax


def plot_symmetric_success_with_expected_keys(
    success_by_threshold: Sequence[float],
    expected_user_keys: float,
    expected_attacker_keys: float,
    title: str = "Symmetric Wallet Success With Expected Keys",
    show: bool = True,
    save_path: str | None = None,
    optimal_threshold: int | None = None,
    optimal_success: float | None = None,
):
    """Plot symmetric-wallet success with expected key-count references."""
    thresholds = list(range(len(success_by_threshold)))

    fig, ax = plt.subplots(figsize=(9, 5))
    success_line = ax.plot(
        thresholds,
        list(success_by_threshold),
        marker="o",
        color="tab:blue",
        label="success probability",
    )[0]
    ax.set_xlabel("Threshold")
    ax.set_ylabel("Success probability")
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, len(thresholds) + 0.5)

    if optimal_threshold is not None:
        marker_kwargs = {
            "color": "tab:blue",
            "s": 60,
            "zorder": 3,
            "label": "optimal threshold",
        }
        if optimal_success is None:
            optimal_success = success_by_threshold[optimal_threshold]
        optimal_marker = ax.scatter([optimal_threshold], [optimal_success], **marker_kwargs)
    else:
        optimal_marker = None

    user_line = ax.axvline(
        expected_user_keys,
        color="tab:green",
        linestyle="--",
        label="expected user keys",
    )
    attacker_line = ax.axvline(
        expected_attacker_keys,
        color="tab:red",
        linestyle=":",
        label="expected attacker keys",
    )

    legend_handles = [success_line, user_line, attacker_line]
    if optimal_marker is not None:
        legend_handles.append(optimal_marker)
    ax.legend(legend_handles, [handle.get_label() for handle in legend_handles], loc="best")

    if save_path:
        fig.savefig(Path(save_path), bbox_inches="tight")

    if show:
        plt.show()

    return fig, ax


def plot_key_count_distributions(
    user_key_count_probabilities: Sequence[float],
    attacker_key_count_probabilities: Sequence[float],
    success_by_threshold: Sequence[float],
    optimal_threshold: int,
    title: str = "User And Attacker Key-Count Distributions",
    show: bool = True,
    save_path: str | None = None,
):
    """Plot key-count distributions together with threshold success values."""
    key_counts = list(range(len(user_key_count_probabilities)))
    thresholds = list(range(len(success_by_threshold)))

    fig, ax = plt.subplots(figsize=(9, 5))
    user_line = ax.plot(
        key_counts,
        list(user_key_count_probabilities),
        marker="o",
        color="tab:green",
        label="user key-count probability",
    )[0]
    attacker_line = ax.plot(
        key_counts,
        list(attacker_key_count_probabilities),
        marker="o",
        color="tab:red",
        label="attacker key-count probability",
    )[0]
    success_line = ax.plot(
        thresholds,
        list(success_by_threshold),
        marker="o",
        color="tab:blue",
        label="threshold success probability",
    )[0]
    threshold_line = ax.axvline(
        optimal_threshold,
        color="tab:purple",
        linestyle="--",
        label="optimal threshold",
    )

    ax.set_xlabel("Number of keys")
    ax.set_ylabel("Probability")
    ax.set_title(title)
    ax.set_xticks(key_counts)
    ax.set_xlim(min(key_counts), max(key_counts))
    ax.grid(True, alpha=0.3)
    legend_handles = [user_line, attacker_line, success_line, threshold_line]
    ax.legend(legend_handles, [h.get_label() for h in legend_handles], loc="best")

    if save_path:
        fig.savefig(Path(save_path), bbox_inches="tight")

    if show:
        plt.show()

    return fig, ax


if __name__ == "__main__":
    # plot the distriuitions for saved probabilities
    probabilities = json.load(open("data/saved_probabilities_list.json"))
    for probability in probabilities:
        plot_key_count_distributions(
            probability["user_key_count_probabilities"],
            probability["attacker_key_count_probabilities"],
            probability["success_by_threshold"],
            probability["optimal_threshold"],
        )
