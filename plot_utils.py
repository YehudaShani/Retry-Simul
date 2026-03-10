"""Plot helpers for symmetric wallet success curves."""
from pathlib import Path
from typing import Mapping, Sequence

import matplotlib.pyplot as plt


def plot_symmetric_success_wallets(
    success_wallets: Sequence[float] | Mapping[str, Sequence[float]],
    title: str = "Symmetric Wallet Success by Threshold",
    show: bool = True,
    save_path: str | None = None,
):
    """Plot one or more symmetric-wallet success curves.

    Args:
        success_wallets: Either a single sequence of success values indexed by
            threshold 1..n, or a mapping of label -> sequence for plotting
            multiple curves on the same axes.
        title: Plot title.
        show: Whether to call ``plt.show()``.
        save_path: Optional file path to save the figure.

    Returns:
        The ``(fig, ax)`` tuple for further customization.
    """
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
