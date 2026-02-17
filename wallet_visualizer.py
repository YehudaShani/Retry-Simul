"""Tkinter desktop app for visualizing wallet bitmasks and success probability."""
import tkinter as tk
from tkinter import ttk

from consts import SAFE, LOST, LEAKED, STOLEN
from wallet_state import WalletState
from wallet_enumerations import oneBitIndices


def _bitmask_label(bitmask: int) -> str:
    """Human-readable label for a bitmask, e.g. (1 ∧ 2)."""
    indices = oneBitIndices(bitmask)
    return "(" + " ∧ ".join(indices) + ")" if indices else "0"


def _group_bitmasks_by_key_count(key_count: int):
    """Return list of lists: [row0_bitmasks, row1_bitmasks, ...] by popcount (1..key_count)."""
    groups = [[] for _ in range(key_count)]
    for m in range(1, 2 ** key_count):  # exclude 0
        pop = m.bit_count()
        if 1 <= pop <= key_count:
            groups[pop - 1].append(m)
    for row in groups:
        row.sort()
    return groups


def run_visualizer(key_count: int = 4, probabilities: dict | None = None):
    if probabilities is None:
        probabilities = {
            SAFE: 0.25,
            LOST: 0.25,
            LEAKED: 0.25,
            STOLEN: 0.25,
        }

    ws = WalletState(key_count, [], probabilities)
    groups = _group_bitmasks_by_key_count(key_count)

    root = tk.Tk()
    root.title("Wallet Bitmask Visualizer")

    prob_var = tk.StringVar(value="Success probability: 0.000000")
    prob_label = ttk.Label(root, textvariable=prob_var, font=("", 14))
    prob_label.pack(pady=10)

    def update_probability():
        p = ws.compute_success_probability()
        prob_var.set(f"Success probability: {p:.6f}")

    buttons = {}

    def refresh_all_buttons():
        for m, btn in buttons.items():
            btn.config(relief=tk.SUNKEN if ws.bitmask_is_in_wallet(m) else tk.RAISED)

    def make_toggle(bitmask: int, parent_frame):
        def on_click():
            if ws.bitmask_is_in_wallet(bitmask):
                ws.remove_bitmask_and_subsets(bitmask)
                print(f"self.remove_bitmask_and_subsets({bitmask})")
            else:
                ws.add_bitmask(bitmask)
                print(f"self.add_bitmask({bitmask})")
            refresh_all_buttons()
            update_probability()

        label = _bitmask_label(bitmask)
        btn = tk.Button(
            parent_frame,
            text=label,
            command=on_click,
            width=12,
            relief=tk.RAISED,
            cursor="hand2",
        )
        return btn

    for row_idx, bitmasks_in_row in enumerate(groups):
        row_frame = ttk.Frame(root)
        row_frame.pack(fill=tk.X, padx=10, pady=4)
        ttk.Label(row_frame, text=f"{row_idx + 1}-key:", width=8).pack(side=tk.LEFT, padx=(0, 8))
        inner = ttk.Frame(row_frame)
        inner.pack(side=tk.LEFT, fill=tk.X, expand=True)
        for m in bitmasks_in_row:
            btn = make_toggle(m, inner)
            btn.pack(side=tk.LEFT, padx=2, pady=2)
            buttons[m] = btn

    refresh_all_buttons()
    update_probability()
    root.mainloop()


if __name__ == "__main__":
    # Check these probabilities with previous symmetric, then with normal symmetric
    run_visualizer(key_count=8, probabilities={1: 0.29, 2: 0.35, 3: 0.1, 4: 0.26})
