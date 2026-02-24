"""Tkinter desktop app for visualizing wallet bitmasks and success probability."""
import json
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
from tkinter import ttk
from tkinter.simpledialog import askstring
from typing import Literal

SAVED_PROBABILITIES_FILE = Path("saved_probabilities_list.json")

from consts import SAFE, LOST, LEAKED, STOLEN, KeyStates, KeyStateString
from wallet_state import WalletState
from wallet_enumerations import oneBitIndices, walletStr
import optimal_symmetric_wallets


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


def run_visualizer(
    key_count: int = 4,
    probabilities: dict | None = None,
    base_wallet=None,
    orientation: Literal["rows", "columns"] = "rows",
):
    if orientation not in {"rows", "columns"}:
        raise ValueError(f"orientation must be 'rows' or 'columns', got: {orientation!r}")

    if probabilities is None:
        probabilities = {
            SAFE: 0.25,
            LOST: 0.25,
            LEAKED: 0.25,
            STOLEN: 0.25,
        }

    if base_wallet is None:
        ws = WalletState(key_count, [], probabilities)
    else:
        ws = base_wallet

    groups = _group_bitmasks_by_key_count(key_count)

    opt_wallet, opt_prob, opt_threshold = optimal_symmetric_wallets.find_optimal_symmetric_wallets(
        key_count, probabilities
    )
    symmetric_optimal_str = f"Symmetric optimal: {opt_threshold}-of-{key_count}" if opt_wallet else "Symmetric optimal: N/A"

    optimal_wallet_states = ws.return_optimal_wallet_for_probability()
    optimal_success_prob = optimal_wallet_states[0].compute_success_probability() if optimal_wallet_states else 0.0
    is_unique_and_symmetric = (
        len(optimal_wallet_states) == 1
        and opt_wallet is not None
        and set(optimal_wallet_states[0].bitmasks) == set(opt_wallet)
    )
    if is_unique_and_symmetric:
        optimal_str = f"Optimal: optimal symmetric wallet (success: {optimal_success_prob:.6f})"
    elif len(optimal_wallet_states) == 1:
        optimal_str = f"Optimal: {walletStr(optimal_wallet_states[0].bitmasks)} (success: {optimal_success_prob:.6f})"
    else:
        optimal_str = f"Optimal ({len(optimal_wallet_states)}): " + "; ".join(
            walletStr(w.bitmasks) for w in optimal_wallet_states
        ) + f" (success: {optimal_success_prob:.6f})"

    root = tk.Tk()
    root.title("Wallet Bitmask Visualizer")
    root.geometry("800x600")

    probs_str = "  |  ".join(
        f"{KeyStateString[k]}: {probabilities[k]:.4f}"
        for k in KeyStates
        if k in probabilities
    )
    probs_label = ttk.Label(root, text=f"Probabilities:  {probs_str}", font=("", 10))
    probs_label.pack(pady=(10, 2))

    prob_var = tk.StringVar(value="Success probability: 0.000000")
    prob_label = ttk.Label(root, textvariable=prob_var, font=("", 14))
    prob_label.pack(pady=(2, 10))

    delta_var = tk.StringVar(value="")
    delta_label = ttk.Label(root, textvariable=delta_var, font=("", 10))
    delta_label.pack(pady=(0, 4))

    subtitle_label = ttk.Label(root, text=symmetric_optimal_str, font=("", 10), wraplength=760)
    subtitle_label.pack(pady=(0, 4))

    optimal_subtitle_label = ttk.Label(root, text=optimal_str, font=("", 10), wraplength=760)
    optimal_subtitle_label.pack(pady=(0, 10))

    def on_save():
        message = askstring("Save probabilities", "Message (optional):", parent=root)
        if message is None:
            return  # user cancelled
        probs_dict = {KeyStateString[k]: probabilities[k] for k in KeyStates if k in probabilities}
        entry = {
            "key_count": key_count,
            "probabilities": probs_dict,
            "message": message,
        }
        try:
            data = []
            if SAVED_PROBABILITIES_FILE.exists():
                data = json.loads(SAVED_PROBABILITIES_FILE.read_text())
            data.append(entry)
            SAVED_PROBABILITIES_FILE.write_text(json.dumps(data, indent=2))
        except (json.JSONDecodeError, OSError) as e:
            messagebox.showerror("Save failed", str(e), parent=root)

    save_btn = ttk.Button(root, text="Save probabilities", command=on_save)
    save_btn.pack(pady=(0, 8))

    canvas_frame = ttk.Frame(root)
    canvas_frame.pack(fill=tk.BOTH, expand=True)

    canvas = tk.Canvas(canvas_frame)
    v_scrollbar = ttk.Scrollbar(canvas_frame)
    h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)

    v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    canvas.configure(yscrollcommand=v_scrollbar.set)
    v_scrollbar.configure(command=canvas.yview)
    canvas.configure(xscrollcommand=h_scrollbar.set)
    h_scrollbar.configure(command=canvas.xview)

    inner_frame = ttk.Frame(canvas)
    canvas_window = canvas.create_window(0, 0, window=inner_frame, anchor=tk.NW)

    def _on_frame_configure(_event=None):
        canvas.configure(scrollregion=canvas.bbox("all"))

    def _on_mousewheel(event):
        if event.num == 5 or (hasattr(event, "delta") and event.delta < 0):
            canvas.yview_scroll(1, "units")
        elif event.num == 4 or (hasattr(event, "delta") and event.delta > 0):
            canvas.yview_scroll(-1, "units")

    def _on_shift_mousewheel(event):
        if event.num == 5 or (hasattr(event, "delta") and event.delta < 0):
            canvas.xview_scroll(1, "units")
        elif event.num == 4 or (hasattr(event, "delta") and event.delta > 0):
            canvas.xview_scroll(-1, "units")

    inner_frame.bind("<Configure>", _on_frame_configure)
    canvas.bind("<MouseWheel>", _on_mousewheel)
    canvas.bind("<Shift-MouseWheel>", _on_shift_mousewheel)
    canvas.bind("<Button-4>", _on_mousewheel)
    canvas.bind("<Button-5>", _on_mousewheel)
    canvas.bind("<Shift-Button-4>", _on_shift_mousewheel)
    canvas.bind("<Shift-Button-5>", _on_shift_mousewheel)

    def update_probability():
        p = ws.compute_success_probability()
        prob_var.set(f"Success probability: {p:.6f}")

    def with_change(change_fn):
        prev = ws.compute_success_probability()
        change_fn()
        refresh_all_buttons()
        new_prob = ws.compute_success_probability()
        prob_var.set(f"Success probability: {new_prob:.6f}")
        delta = new_prob - prev
        if delta > 0:
            delta_var.set(f"↑ +{delta:.6f}")
        elif delta < 0:
            delta_var.set(f"↓ {delta:.6f}")
        else:
            delta_var.set("— no change")

    buttons = {}

    PRESSED_BG = "#b0b0b0"
    UNPRESSED_BG = "#e8e8e8"

    def refresh_all_buttons():
        for m, btn in buttons.items():
            in_wallet = ws.bitmask_is_in_wallet(m)
            btn.config(
                relief=tk.SUNKEN if in_wallet else tk.RAISED,
                bg=PRESSED_BG if in_wallet else UNPRESSED_BG,
            )

    def make_toggle(bitmask: int, parent_frame):
        def on_click():
            def change():
                if ws.bitmask_is_in_wallet(bitmask):
                    ws.remove_bitmask_and_subsets(bitmask)
                else:
                    ws.add_bitmask(bitmask)
            with_change(change)

        label = _bitmask_label(bitmask)
        btn = tk.Button(
            parent_frame,
            text=label,
            command=on_click,
            width=12,
            relief=tk.RAISED,
            cursor="hand2",
            bg=UNPRESSED_BG,
        )
        return btn

    if orientation == "rows":
        for row_idx, bitmasks_in_row in enumerate(groups):
            row_frame = ttk.Frame(inner_frame)
            row_frame.pack(fill=tk.X, padx=10, pady=4)
            ttk.Label(row_frame, text=f"{row_idx + 1}-key:", width=8).pack(side=tk.LEFT, padx=(0, 8))

            def add_all_in_layer(bitmasks=bitmasks_in_row):
                def change():
                    for m in bitmasks:
                        if not ws.bitmask_is_in_wallet(m):
                            ws.add_bitmask(m)

                with_change(change)

            add_all_btn = ttk.Button(row_frame, text="Add all", command=add_all_in_layer)
            add_all_btn.pack(side=tk.LEFT, padx=(0, 8))
            inner = ttk.Frame(row_frame)
            inner.pack(side=tk.LEFT, fill=tk.X, expand=True)
            for m in bitmasks_in_row:
                btn = make_toggle(m, inner)
                btn.pack(side=tk.LEFT, padx=2, pady=2)
                buttons[m] = btn
    else:
        for col_idx, bitmasks_in_col in enumerate(groups):
            header_frame = ttk.Frame(inner_frame)
            header_frame.grid(row=0, column=col_idx, padx=10, pady=(4, 6), sticky=tk.N)
            ttk.Label(header_frame, text=f"{col_idx + 1}-key:").pack()

            def add_all_in_layer(bitmasks=bitmasks_in_col):
                def change():
                    for m in bitmasks:
                        if not ws.bitmask_is_in_wallet(m):
                            ws.add_bitmask(m)

                with_change(change)

            add_all_btn = ttk.Button(header_frame, text="Add all", command=add_all_in_layer)
            add_all_btn.pack(pady=(2, 0))

        for col_idx, bitmasks_in_col in enumerate(groups):
            for row_idx, m in enumerate(bitmasks_in_col, start=1):
                btn = make_toggle(m, inner_frame)
                btn.grid(row=row_idx, column=col_idx, padx=4, pady=2, sticky=tk.EW)
                buttons[m] = btn

    inner_frame.update_idletasks()
    canvas.configure(scrollregion=canvas.bbox("all"))

    refresh_all_buttons()
    update_probability()
    root.mainloop()


if __name__ == "__main__":
    # Check these probabilities with previous symmetric, then with normal symmetric
    run_visualizer(key_count=5, probabilities={1: 0.36, 2: 0.12, 3: 0.22, 4: 0.3}, orientation="columns")
