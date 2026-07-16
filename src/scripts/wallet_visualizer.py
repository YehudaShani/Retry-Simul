"""Tkinter desktop app for visualizing wallet bitmasks and success probability."""
import json
import re
import sys
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from tkinter.simpledialog import askstring
from typing import Iterable, Literal
import random

for _src in Path(__file__).resolve().parents:
    if (_src / "helpers").is_dir() and (_src / "scripts").is_dir():
        if str(_src) not in sys.path:
            sys.path.insert(0, str(_src))
        break

from helpers.paths import SAVED_PROBABILITIES_FILE, data_path, repo_relative

from helpers import computations
from helpers.consts import KeyStateString, KeyStates, LEAKED, LOST, SAFE, STOLEN
from helpers import optimal_symmetric_wallets
from helpers import wallet_cache
from helpers.wallet_enumerations import oneBitIndices, walletStr
from helpers.wallet_state import WalletState
from helpers.symbols import (
    UI_MONOMIAL_STATE_LABELS,
    format_signed_polynomial_sum,
    format_success_probability_polynomial,
    success_probability_polynomial_coefficients,
    success_probability_polynomial_difference_coefficients,
)

NAME_TO_CONST = {"SAFE": SAFE, "LOST": LOST, "LEAKED": LEAKED, "STOLEN": STOLEN}
PROBABILITY_EPSILON = 1e-12


def _normalize_probs(probs: dict) -> dict:
    """Convert string keys like 'SAFE' to consts; leave int keys as-is."""
    return {NAME_TO_CONST.get(k, k): v for k, v in probs.items()}


def _normalize_json_item(item: dict) -> tuple[int, dict, str, list[int] | None]:
    """
    Normalize a single item from a probabilities/params JSON list.
    Returns (key_count, probabilities, extra_subtitle, wallet).
    Works with probabilities-only, or items that include keyCount, optimal_*, message,
    and an optional explicit wallet (``wallet`` or ``bitmasks``).
    """
    probs_raw = item.get("probabilities") if isinstance(item, dict) and "probabilities" in item else item
    if isinstance(probs_raw, dict):
        if not any(k in (SAFE, LOST, LEAKED, STOLEN) for k in probs_raw):
            probs = _normalize_probs(probs_raw)
        else:
            probs = probs_raw
    else:
        probs = {SAFE: 0.25, LOST: 0.25, LEAKED: 0.25, STOLEN: 0.25}
    key_count = item.get("keyCount") or item.get("key_count") or 4
    wallet = None
    if isinstance(item, dict):
        wallet_raw = item.get("wallet", item.get("bitmasks"))
        if isinstance(wallet_raw, list):
            wallet = [int(m) for m in wallet_raw]
    extra_parts = []
    if "optimal_threshold" in item:
        extra_parts.append(f"optimal_threshold: {item['optimal_threshold']}")
    if "optimal_success" in item:
        extra_parts.append(f"optimal_success: {item['optimal_success']:.6f}")
    if "message" in item:
        extra_parts.append(str(item["message"]))
    extra_subtitle = "  |  ".join(extra_parts) if extra_parts else ""
    return key_count, probs, extra_subtitle, wallet


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


def _format_probabilities(probabilities: dict[int, float]) -> str:
    return "  |  ".join(
        f"{KeyStateString[k]}: {probabilities[k]:.4f}" for k in KeyStates if k in probabilities
    )


def redistribute_probability_change(
    probabilities: dict[int, float],
    changed_state: int,
    requested_value: float,
    adjustable_states: Iterable[int],
) -> tuple[dict[int, float], bool]:
    """Return probabilities after moving one state and redistributing among checked states.

    The checked states define the adjustable group. If the moved state is not checked,
    or fewer than two states are checked, the probabilities are unchanged.
    """
    new_probabilities = dict(probabilities)
    adjustable_set = set(adjustable_states)
    adjustable = tuple(state for state in KeyStates if state in adjustable_set)
    if changed_state not in adjustable or len(adjustable) < 2:
        return new_probabilities, False

    current_value = probabilities[changed_state]
    requested_value = max(0.0, min(1.0, requested_value))
    requested_delta = requested_value - current_value
    if abs(requested_delta) <= PROBABILITY_EPSILON:
        return new_probabilities, False

    other_states = [state for state in adjustable if state != changed_state]
    other_count = len(other_states)

    if requested_delta > 0:
        max_delta = min(
            1.0 - current_value,
            *(probabilities[state] * other_count for state in other_states),
        )
        actual_delta = min(requested_delta, max(0.0, max_delta))
    else:
        max_decrease = min(
            current_value,
            *((1.0 - probabilities[state]) * other_count for state in other_states),
        )
        actual_delta = -min(-requested_delta, max(0.0, max_decrease))

    if abs(actual_delta) <= PROBABILITY_EPSILON:
        return new_probabilities, False

    new_probabilities[changed_state] = current_value + actual_delta
    per_other_delta = actual_delta / other_count
    for state in other_states:
        new_probabilities[state] = probabilities[state] - per_other_delta

    total = sum(new_probabilities[state] for state in KeyStates)
    drift = 1.0 - total
    if abs(drift) <= 1e-9:
        new_probabilities[changed_state] += drift

    for state in KeyStates:
        new_probabilities[state] = max(0.0, min(1.0, new_probabilities[state]))
    return new_probabilities, True


def _build_visualizer_content(
    parent: tk.Widget,
    key_count: int,
    probabilities: dict,
    base_wallet=None,
    orientation: Literal["rows", "columns"] = "rows",
    extra_subtitle: str = "",
):
    """Build the full visualizer UI (probability label, canvas, bitmask buttons) inside parent."""
    if base_wallet is None:
        ws = WalletState(key_count, [], probabilities)
    else:
        ws = base_wallet
        ws.probabilities = probabilities

    toplevel = parent.winfo_toplevel()
    groups = _group_bitmasks_by_key_count(key_count)

    # With many keys the button grid needs the full window height, so move the
    # textual info/controls into a scrollable side panel on the left and let the
    # bitmask canvas fill the rest of the window on the right.
    use_side_panel = key_count >= 6
    if use_side_panel:
        split_frame = ttk.Frame(parent)
        split_frame.pack(fill=tk.BOTH, expand=True)

        side_outer = ttk.Frame(split_frame)
        side_outer.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 6))
        side_canvas = tk.Canvas(side_outer, width=340, highlightthickness=0)
        side_scrollbar = ttk.Scrollbar(side_outer, orient=tk.VERTICAL, command=side_canvas.yview)
        side_canvas.configure(yscrollcommand=side_scrollbar.set)
        side_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        side_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        info_parent = ttk.Frame(side_canvas)
        side_window = side_canvas.create_window((0, 0), window=info_parent, anchor=tk.NW)

        def _on_side_configure(_event=None):
            side_canvas.configure(scrollregion=side_canvas.bbox("all"))

        def _on_side_canvas_configure(event):
            side_canvas.itemconfigure(side_window, width=event.width)

        info_parent.bind("<Configure>", _on_side_configure)
        side_canvas.bind("<Configure>", _on_side_canvas_configure)

        def _on_side_mousewheel(event):
            if event.num == 5 or (hasattr(event, "delta") and event.delta < 0):
                side_canvas.yview_scroll(1, "units")
            elif event.num == 4 or (hasattr(event, "delta") and event.delta > 0):
                side_canvas.yview_scroll(-1, "units")

        side_canvas.bind("<MouseWheel>", _on_side_mousewheel)
        side_canvas.bind("<Button-4>", _on_side_mousewheel)
        side_canvas.bind("<Button-5>", _on_side_mousewheel)

        canvas_parent = ttk.Frame(split_frame)
        canvas_parent.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    else:
        info_parent = parent
        canvas_parent = parent

    subtitle_wraplength = 320 if use_side_panel else 760

    def _pack_bottom_button(btn: tk.Widget) -> None:
        if use_side_panel:
            btn.pack(side=tk.TOP, fill=tk.X, padx=4, pady=2)
        else:
            btn.pack(side=tk.LEFT, padx=4)

    def compute_optimal_texts() -> tuple[str, str, list[int] | None]:
        opt_wallet, opt_prob, opt_threshold = optimal_symmetric_wallets.find_optimal_symmetric_wallets(
            key_count, probabilities
        )
        symmetric_text = (
            f"Symmetric optimal: {opt_threshold}-of-{key_count} (success: {opt_prob:.6f})"
            if opt_wallet
            else "Symmetric optimal: N/A"
        )
        if extra_subtitle:
            symmetric_text = symmetric_text + "  |  " + extra_subtitle

        optimal_bitmasks = None
        if key_count >= 6:
            optimal_text = "Optimal: skipped for key_count >= 6"
        elif wallet_cache.supports_wallet_cache_key_count(key_count) and wallet_cache.has_cached_wallets(
            key_count
        ):
            optimal_wallet_states = ws.return_optimal_wallet_for_probability()
            optimal_success_prob = (
                optimal_wallet_states[0].compute_success_probability() if optimal_wallet_states else 0.0
            )
            if optimal_wallet_states:
                optimal_bitmasks = list(optimal_wallet_states[0].bitmasks)
            is_unique_and_symmetric = (
                len(optimal_wallet_states) == 1
                and opt_wallet is not None
                and set(optimal_wallet_states[0].bitmasks) == set(opt_wallet)
            )
            if is_unique_and_symmetric:
                optimal_text = f"Optimal: optimal symmetric wallet (success: {optimal_success_prob:.6f})"
            elif len(optimal_wallet_states) == 1:
                optimal_text = (
                    f"Optimal: {walletStr(optimal_wallet_states[0].bitmasks)} "
                    f"(success: {optimal_success_prob:.6f})"
                )
            else:
                optimal_text = (
                    f"Optimal ({len(optimal_wallet_states)}): "
                    + "; ".join(walletStr(w.bitmasks) for w in optimal_wallet_states)
                    + f" (success: {optimal_success_prob:.6f})"
                )
        else:
            optimal_text = (
                "Optimal: N/A (missing cached wallets; avoid enumerating in visualizer)"
                if wallet_cache.supports_wallet_cache_key_count(key_count)
                else f"Optimal: N/A (key_count={key_count} outside static-wallet range 1..8)"
            )
        return symmetric_text, optimal_text, optimal_bitmasks

    symmetric_optimal_str, optimal_str, _initial_optimal_bitmasks = compute_optimal_texts()
    probabilities_text_var = tk.StringVar(value=f"Probabilities:  {_format_probabilities(probabilities)}")

    probability_controls_visible = tk.BooleanVar(value=False)
    probability_controls_toggle_text = tk.StringVar(value="Show probability controls")
    probability_controls_toggle = ttk.Button(
        info_parent,
        textvariable=probability_controls_toggle_text,
    )
    probability_controls_toggle.pack(pady=(10, 0))

    probability_controls = ttk.LabelFrame(info_parent, text="Adjust probabilities", padding=(8, 6, 8, 6))

    probability_slider_vars: dict[int, tk.DoubleVar] = {}
    probability_value_vars: dict[int, tk.StringVar] = {}
    probability_check_vars: dict[int, tk.BooleanVar] = {}
    probability_slider_widgets = {}
    probability_status_var = tk.StringVar(value="")
    syncing_probability_controls = [False]

    def checked_probability_states() -> tuple[int, ...]:
        return tuple(state for state in KeyStates if probability_check_vars[state].get())

    def sync_probability_controls() -> None:
        syncing_probability_controls[0] = True
        probabilities_text_var.set(f"Probabilities:  {_format_probabilities(probabilities)}")
        for state in KeyStates:
            value = probabilities[state]
            probability_slider_vars[state].set(value)
            probability_value_vars[state].set(f"{value:.4f}")
        syncing_probability_controls[0] = False

    def sync_probability_slider_states() -> None:
        for state, slider in probability_slider_widgets.items():
            if probability_check_vars[state].get():
                slider.state(["!disabled"])
            else:
                slider.state(["disabled"])

    def on_probability_checkbox_changed() -> None:
        checked_states = checked_probability_states()
        if len(checked_states) < 2:
            probability_status_var.set("Select at least two probabilities to redistribute.")
        else:
            probability_status_var.set("")
        sync_probability_slider_states()

    def on_probability_slider(state: int, value: str) -> None:
        if syncing_probability_controls[0]:
            return
        checked_states = checked_probability_states()
        previous_success_probability = ws.compute_success_probability()
        updated, changed = redistribute_probability_change(
            probabilities,
            state,
            float(value),
            checked_states,
        )
        if not changed:
            if state not in checked_states:
                probability_status_var.set(f"Check {KeyStateString[state]} before moving its slider.")
            elif len(checked_states) < 2:
                probability_status_var.set("Select at least two probabilities to redistribute.")
            sync_probability_controls()
            return

        probability_status_var.set("")
        probabilities.update(updated)
        sync_probability_controls()
        new_success_probability = update_probability()
        delta = new_success_probability - previous_success_probability
        if delta > 0:
            delta_var.set(f"↑ +{delta:.6f}")
        elif delta < 0:
            delta_var.set(f"↓ {delta:.6f}")
        else:
            delta_var.set("— no change")
        schedule_optimal_refresh(apply_optimal_wallet=auto_apply_optimal_wallet.get())

    for row, state in enumerate(KeyStates):
        probability_check_vars[state] = tk.BooleanVar(value=True)
        probability_slider_vars[state] = tk.DoubleVar(value=probabilities[state])
        probability_value_vars[state] = tk.StringVar(value=f"{probabilities[state]:.4f}")

        ttk.Checkbutton(
            probability_controls,
            text=KeyStateString[state],
            variable=probability_check_vars[state],
            command=on_probability_checkbox_changed,
        ).grid(row=row, column=0, sticky=tk.W, padx=(0, 8), pady=2)
        slider = ttk.Scale(
            probability_controls,
            from_=0.0,
            to=1.0,
            orient=tk.HORIZONTAL,
            variable=probability_slider_vars[state],
            command=lambda value, state=state: on_probability_slider(state, value),
        )
        slider.grid(row=row, column=1, sticky=tk.EW, padx=(0, 8), pady=2)
        probability_slider_widgets[state] = slider
        ttk.Label(
            probability_controls,
            textvariable=probability_value_vars[state],
            width=8,
        ).grid(row=row, column=2, sticky=tk.E, pady=2)

    probability_controls.columnconfigure(1, weight=1)
    ttk.Label(probability_controls, textvariable=probability_status_var).grid(
        row=len(KeyStates), column=0, columnspan=3, sticky=tk.W, pady=(4, 0)
    )

    def apply_probability_controls_visibility() -> None:
        if probability_controls_visible.get():
            probability_controls.pack(fill=tk.X, padx=10, pady=(6, 4), after=probability_controls_toggle)
            probability_controls_toggle_text.set("Hide probability controls")
        else:
            probability_controls.pack_forget()
            probability_controls_toggle_text.set("Show probability controls")

    def toggle_probability_controls() -> None:
        probability_controls_visible.set(not probability_controls_visible.get())
        apply_probability_controls_visibility()

    probability_controls_toggle.configure(command=toggle_probability_controls)
    apply_probability_controls_visibility()

    probs_label = ttk.Label(
        info_parent, textvariable=probabilities_text_var, font=("", 10), wraplength=subtitle_wraplength
    )
    probs_label.pack(pady=(10, 2))

    prob_var = tk.StringVar(value="Success probability: 0.000000")
    prob_label = ttk.Label(info_parent, textvariable=prob_var, font=("", 14))
    prob_label.pack(pady=(2, 10))

    delta_var = tk.StringVar(value="")
    delta_label = ttk.Label(info_parent, textvariable=delta_var, font=("", 10))
    delta_label.pack(pady=(0, 4))

    poly_outer = ttk.LabelFrame(
        info_parent,
        text="Symbolic success (i.i.d. keys; p_SAFE + p_LOST + p_LEAKED + p_STOLEN = 1 per key)",
        padding=(6, 4, 6, 6),
    )
    poly_text = tk.Text(
        poly_outer,
        height=1,
        wrap=tk.WORD,
        font=("Consolas", 9),
        state=tk.DISABLED,
        relief=tk.FLAT,
        borderwidth=1,
        padx=4,
        pady=4,
        highlightthickness=0,
    )
    poly_text.pack(fill=tk.X, expand=False)

    _poly_height_job: list[int | None] = [None]

    def _sync_poly_text_height() -> None:
        poly_text.update_idletasks()
        try:
            n = poly_text.count("1.0", "end", "displaylines")
            if n is None:
                nlines = 1
            else:
                nlines = int(n[0] if isinstance(n, tuple) else n)
        except (tk.TclError, TypeError, ValueError):
            try:
                nlines = int(poly_text.index("end-1c").split(".")[0])
            except (tk.TclError, ValueError):
                nlines = 1
        poly_text.config(height=max(1, nlines))

    def _schedule_poly_text_height(_event: tk.Event | None = None) -> None:
        job = _poly_height_job[0]
        if job is not None:
            toplevel.after_cancel(job)
        _poly_height_job[0] = toplevel.after(50, _run_scheduled_poly_height)

    def _run_scheduled_poly_height() -> None:
        _poly_height_job[0] = None
        _sync_poly_text_height()

    poly_outer.bind("<Configure>", _schedule_poly_text_height, add=True)

    poly_delta_outer = ttk.Frame(info_parent)
    poly_delta_box = ttk.LabelFrame(
        poly_delta_outer,
        text="Symbolic change (last edit)",
        padding=(6, 4, 6, 6),
    )
    poly_delta_box.pack(fill=tk.X)
    poly_delta_text = tk.Text(
        poly_delta_box,
        height=1,
        wrap=tk.WORD,
        font=("Consolas", 9),
        state=tk.DISABLED,
        relief=tk.FLAT,
        borderwidth=1,
        padx=4,
        pady=4,
        highlightthickness=0,
    )
    poly_delta_text.pack(fill=tk.X, expand=False)
    poly_delta_text.config(state=tk.NORMAL)
    poly_delta_text.insert("1.0", "—")
    poly_delta_text.config(state=tk.DISABLED)

    _poly_delta_height_job: list[int | None] = [None]

    def _sync_poly_delta_text_height() -> None:
        poly_delta_text.update_idletasks()
        try:
            n = poly_delta_text.count("1.0", "end", "displaylines")
            if n is None:
                nlines = 1
            else:
                nlines = int(n[0] if isinstance(n, tuple) else n)
        except (tk.TclError, TypeError, ValueError):
            try:
                nlines = int(poly_delta_text.index("end-1c").split(".")[0])
            except (tk.TclError, ValueError):
                nlines = 1
        poly_delta_text.config(height=max(1, nlines))

    def _schedule_poly_delta_text_height(_event: tk.Event | None = None) -> None:
        job = _poly_delta_height_job[0]
        if job is not None:
            toplevel.after_cancel(job)
        _poly_delta_height_job[0] = toplevel.after(50, _run_scheduled_poly_delta_height)

    def _run_scheduled_poly_delta_height() -> None:
        _poly_delta_height_job[0] = None
        _sync_poly_delta_text_height()

    poly_delta_outer.bind("<Configure>", _schedule_poly_delta_text_height, add=True)

    symmetric_optimal_var = tk.StringVar(value=symmetric_optimal_str)
    optimal_subtitle_var = tk.StringVar(value=optimal_str)

    subtitle_label = ttk.Label(
        info_parent, textvariable=symmetric_optimal_var, font=("", 10), wraplength=subtitle_wraplength
    )
    subtitle_label.pack(pady=(0, 4))

    optimal_subtitle_label = ttk.Label(
        info_parent, textvariable=optimal_subtitle_var, font=("", 10), wraplength=subtitle_wraplength
    )
    optimal_subtitle_label.pack(pady=(0, 10))

    bottom_buttons_frame = ttk.Frame(info_parent)

    auto_apply_optimal_wallet = tk.BooleanVar(value=True)
    auto_apply_optimal_toggle_text = tk.StringVar(value="Auto-apply optimal wallet: ON")

    def toggle_auto_apply_optimal() -> None:
        auto_apply_optimal_wallet.set(not auto_apply_optimal_wallet.get())
        if auto_apply_optimal_wallet.get():
            auto_apply_optimal_toggle_text.set("Auto-apply optimal wallet: ON")
            schedule_optimal_refresh(apply_optimal_wallet=True)
        else:
            auto_apply_optimal_toggle_text.set("Auto-apply optimal wallet: OFF")

    auto_apply_optimal_btn = ttk.Button(
        bottom_buttons_frame,
        textvariable=auto_apply_optimal_toggle_text,
        command=toggle_auto_apply_optimal,
    )
    _pack_bottom_button(auto_apply_optimal_btn)

    def on_save():
        message = askstring("Save probabilities", "Message (optional):", parent=toplevel)
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
                data = json.loads(SAVED_PROBABILITIES_FILE.read_text(encoding="utf-8"))
            data.append(entry)
            SAVED_PROBABILITIES_FILE.parent.mkdir(parents=True, exist_ok=True)
            SAVED_PROBABILITIES_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
            messagebox.showinfo(
                "Saved",
                f"Entry appended to\n{SAVED_PROBABILITIES_FILE}",
                parent=toplevel,
            )
        except (json.JSONDecodeError, OSError) as e:
            messagebox.showerror("Save failed", str(e), parent=toplevel)

    save_btn = ttk.Button(bottom_buttons_frame, text="Save probabilities", command=on_save)
    _pack_bottom_button(save_btn)

    symbols_visible = tk.BooleanVar(value=False)
    symbols_toggle_text = tk.StringVar(value="Show symbols")

    def _apply_symbols_visibility() -> None:
        if symbols_visible.get():
            poly_delta_outer.pack(fill=tk.X, padx=4, pady=(0, 6), before=bottom_buttons_frame)
            poly_outer.pack(fill=tk.X, padx=4, pady=(0, 6), before=bottom_buttons_frame)
            _sync_poly_delta_text_height()
            _sync_poly_text_height()
            symbols_toggle_text.set("Hide symbols")
        else:
            poly_outer.pack_forget()
            poly_delta_outer.pack_forget()
            symbols_toggle_text.set("Show symbols")

    def _toggle_symbols() -> None:
        symbols_visible.set(not symbols_visible.get())
        _apply_symbols_visibility()

    symbols_btn = ttk.Button(bottom_buttons_frame, textvariable=symbols_toggle_text, command=_toggle_symbols)
    _pack_bottom_button(symbols_btn)

    def on_shift():
        with_change(lambda: ws.shift())

    shift_btn = ttk.Button(bottom_buttons_frame, text="Shift wallet", command=on_shift)
    _pack_bottom_button(shift_btn)

    canvas_frame = ttk.Frame(canvas_parent)
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

    def update_success_polynomial():
        coeffs = success_probability_polynomial_coefficients(key_count, list(ws.bitmasks))
        text = format_success_probability_polynomial(
            coeffs,
            variable_prefix="",
            state_labels=UI_MONOMIAL_STATE_LABELS,
            multiline=True,
            use_unicode=False,
        )
        poly_text.config(state=tk.NORMAL)
        poly_text.delete("1.0", tk.END)
        poly_text.insert("1.0", text)
        poly_text.config(state=tk.DISABLED)
        _sync_poly_text_height()

    def update_probability():
        p = ws.compute_success_probability()
        prob_var.set(f"Success probability: {p:.6f}")
        probabilities_text_var.set(f"Probabilities:  {_format_probabilities(probabilities)}")
        update_success_polynomial()
        return p

    optimal_refresh_job: list[int | None] = [None]

    def refresh_optimal_labels(apply_optimal_wallet: bool = False) -> None:
        optimal_refresh_job[0] = None
        symmetric_text, optimal_text, optimal_bitmasks = compute_optimal_texts()
        symmetric_optimal_var.set(symmetric_text)
        optimal_subtitle_var.set(optimal_text)
        if apply_optimal_wallet and optimal_bitmasks is not None:
            ws.bitmasks = list(optimal_bitmasks)
            refresh_all_buttons()
            update_probability()
            delta_var.set("Showing recalculated optimal wallet")

    def schedule_optimal_refresh(apply_optimal_wallet: bool = False) -> None:
        job = optimal_refresh_job[0]
        if job is not None:
            toplevel.after_cancel(job)
        optimal_refresh_job[0] = toplevel.after(
            250,
            lambda: refresh_optimal_labels(apply_optimal_wallet=apply_optimal_wallet),
        )

    def with_change(change_fn):
        prev_coeffs = success_probability_polynomial_coefficients(key_count, list(ws.bitmasks))
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

        new_coeffs = success_probability_polynomial_coefficients(key_count, list(ws.bitmasks))
        diff = success_probability_polynomial_difference_coefficients(prev_coeffs, new_coeffs)
        delta_poly_str = format_signed_polynomial_sum(
            diff,
            variable_prefix="",
            state_labels=UI_MONOMIAL_STATE_LABELS,
            multiline=True,
            use_unicode=False,
        )
        poly_delta_text.config(state=tk.NORMAL)
        poly_delta_text.delete("1.0", tk.END)
        poly_delta_text.insert("1.0", delta_poly_str)
        poly_delta_text.config(state=tk.DISABLED)
        _sync_poly_delta_text_height()

        update_success_polynomial()

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
            ttk.Label(row_frame, text=f"{row_idx + 1}-key:", width=8).pack(
                side=tk.LEFT, padx=(0, 8)
            )

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
            header_frame.grid(
                row=0, column=col_idx, padx=10, pady=(4, 6), sticky=tk.N
            )
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

    bottom_buttons_frame.pack(fill=tk.X, padx=10, pady=(8, 10))
    _apply_symbols_visibility()

    refresh_all_buttons()
    update_probability()


def run_visualizer(
    key_count: int = 4,
    probabilities: dict | None = None,
    base_wallet=None,
    orientation: Literal["rows", "columns"] = "rows",
):
    """Run the wallet visualizer in a new window."""
    if orientation not in {"rows", "columns"}:
        raise ValueError(f"orientation must be 'rows' or 'columns', got: {orientation!r}")
    if probabilities is None:
        probabilities = {
            SAFE: 0.25,
            LOST: 0.25,
            LEAKED: 0.25,
            STOLEN: 0.25,
        }
    root = tk.Tk()
    root.title("Wallet Bitmask Visualizer")
    root.geometry("800x600")
    _build_visualizer_content(root, key_count, probabilities, base_wallet, orientation)
    root.mainloop()


def _initial_wallet_for_case(key_count: int, probabilities: dict) -> WalletState:
    if (
        key_count < 6
        and wallet_cache.supports_wallet_cache_key_count(key_count)
        and wallet_cache.has_cached_wallets(key_count)
    ):
        empty_wallet = WalletState(key_count, [], probabilities)
        optimal_wallets = empty_wallet.return_optimal_wallet_for_probability()
        if optimal_wallets:
            return optimal_wallets[0]

    symmetric_wallet, _success_probability, _threshold = (
        optimal_symmetric_wallets.find_optimal_symmetric_wallets(key_count, probabilities)
    )
    return WalletState(key_count, list(symmetric_wallet or []), probabilities)


def _load_normalized_json_list(path: Path) -> list[tuple[int, dict, str, list[int] | None]]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        data = [data]
    return [_normalize_json_item(item) for item in data]


_LAYER_EDIT_RE = re.compile(r"^layer_edit_(?P<cat>.+?)(?:_(?P<n>\d+)keys)?\.json$")

# Preferred display order for layer-edit list categories.
_CATEGORY_ORDER = [
    "remove_first",
    "complete_last",
    "both",
    "none",
    "only_remove_first",
    "only_complete_last",
    "only_both",
]


def _parse_list_filename(name: str) -> tuple[str, str]:
    """Return (key_group, label) for a list file.

    layer_edit_<cat>[_<n>keys].json -> (key group = str(n) or "5", label = <cat>).
    Anything else -> ("other", filename).
    """
    m = _LAYER_EDIT_RE.match(name)
    if m:
        n = m.group("n")
        return (n if n is not None else "5"), m.group("cat")
    return "other", name


def _order_labels(labels: Iterable[str]) -> list[str]:
    def rank(label: str) -> tuple[int, str]:
        return (
            _CATEGORY_ORDER.index(label) if label in _CATEGORY_ORDER else len(_CATEGORY_ORDER),
            label,
        )

    return sorted(labels, key=rank)


def run_visualizer_from_json(json_path: str):
    """
    Load a JSON file of probability/parameter entries (list of objects) and run the visualizer
    with Prev/Next buttons to step through the list one by one.
    Each entry can have: probabilities, keyCount/key_count, optimal_threshold, optimal_success,
    message, and an optional wallet/bitmasks.

    Two dropdowns at the top let you switch lists: "Keys:" selects the key-count group
    (parsed from the *_Nkeys.json file name; unsuffixed layer_edit files are treated as 5
    keys) and "List:" selects the category within that group.
    """
    resolved_path = repo_relative(json_path)

    # Discover sibling JSON lists and group them by parsed key count.
    list_dir = resolved_path.parent
    available = sorted(list_dir.glob("*.json"))
    if resolved_path not in available:
        available = [resolved_path, *available]

    groups: dict[str, dict[str, Path]] = {}
    for p in available:
        key_group, label = _parse_list_filename(p.name)
        groups.setdefault(key_group, {})[label] = p

    def _key_group_sort(g: str) -> tuple[int, object]:
        return (0, int(g)) if g.isdigit() else (1, g)

    key_group_labels = sorted(groups.keys(), key=_key_group_sort)
    init_group, init_label = _parse_list_filename(resolved_path.name)

    normalized = _load_normalized_json_list(resolved_path)
    if not normalized:
        raise ValueError("JSON file must contain a non-empty list of entries")

    root = tk.Tk()
    root.geometry("840x700")

    nav_frame = ttk.Frame(root)
    nav_frame.pack(fill=tk.X, padx=10, pady=8)

    current_index = tk.IntVar(value=0)
    current_path = [resolved_path]

    def update_title():
        root.title(f"Wallet Visualizer — {current_path[0].name}")

    def go_prev():
        i = current_index.get()
        if i > 0:
            current_index.set(i - 1)
            show_current()

    def go_next():
        i = current_index.get()
        if i < len(normalized) - 1:
            current_index.set(i + 1)
            show_current()

    def load_path(path: Path):
        nonlocal normalized
        loaded = _load_normalized_json_list(path)
        if not loaded:
            index_label.config(text="(empty list)")
            return
        normalized = loaded
        current_path[0] = path
        current_index.set(0)
        update_title()
        show_current()

    # Key-count picker.
    ttk.Label(nav_frame, text="Keys:").pack(side=tk.LEFT, padx=(0, 4))
    key_group_var = tk.StringVar(value=init_group)
    keys_picker = ttk.Combobox(
        nav_frame,
        textvariable=key_group_var,
        values=key_group_labels,
        state="readonly",
        width=7,
    )
    keys_picker.pack(side=tk.LEFT, padx=(0, 12))

    # List (category) picker.
    ttk.Label(nav_frame, text="List:").pack(side=tk.LEFT, padx=(0, 4))
    list_var = tk.StringVar(value=init_label)
    list_picker = ttk.Combobox(
        nav_frame,
        textvariable=list_var,
        values=_order_labels(groups[init_group].keys()),
        state="readonly",
        width=26,
    )
    list_picker.pack(side=tk.LEFT, padx=(0, 16))

    def on_pick_list(_event=None):
        grp = groups.get(key_group_var.get(), {})
        path = grp.get(list_var.get())
        if path is not None:
            load_path(path)

    def on_pick_keys(_event=None):
        grp = groups.get(key_group_var.get(), {})
        labels = _order_labels(grp.keys())
        list_picker.config(values=labels)
        if labels:
            list_var.set(labels[0])
            load_path(grp[labels[0]])

    keys_picker.bind("<<ComboboxSelected>>", on_pick_keys)
    list_picker.bind("<<ComboboxSelected>>", on_pick_list)

    index_label = ttk.Label(nav_frame, text="", font=("", 11))

    ttk.Button(nav_frame, text="← Prev", command=go_prev).pack(side=tk.LEFT, padx=2)
    ttk.Button(nav_frame, text="Next →", command=go_next).pack(side=tk.LEFT, padx=2)
    index_label.pack(side=tk.LEFT, padx=(20, 0))

    def update_index_label():
        index_label.config(text=f"Item {current_index.get() + 1} / {len(normalized)}")

    content_frame = ttk.Frame(root)
    content_frame.pack(fill=tk.BOTH, expand=True)

    def show_current():
        for w in content_frame.winfo_children():
            w.destroy()
        i = current_index.get()
        key_count, probs, extra_subtitle, wallet = normalized[i]
        if wallet is not None:
            initial_wallet = WalletState(key_count, list(wallet), probs)
        else:
            initial_wallet = _initial_wallet_for_case(key_count, probs)
        _build_visualizer_content(
            content_frame,
            key_count,
            probs,
            base_wallet=initial_wallet,
            extra_subtitle=extra_subtitle,
            orientation="columns",
        )
        update_index_label()

    update_title()
    update_index_label()
    show_current()
    root.mainloop()

def generate_random_cases(num_of_keys = 5, num_of_cases: int = 50):
    probabilities = computations.generateKeyFaultProbabilityScenarios(step=0.01)
    probabilities = random.sample(probabilities, num_of_cases)
    # save list in json file
    out_path = data_path(f"random_cases_{num_of_keys}_keys_{num_of_cases}_cases.json")
    items = [
        {
            "key_count": num_of_keys,
            "probabilities": {
                "SAFE": p.get(SAFE, 0.0),
                "LOST": p.get(LOST, 0.0),
                "LEAKED": p.get(LEAKED, 0.0),
                "STOLEN": p.get(STOLEN, 0.0),
            },
            "message": "",
        }
        for p in probabilities
    ]
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2)
    run_visualizer_from_json(str(out_path))

if __name__ == "__main__":
    #Check these probabilities with previo us symmetric, then with normal symmetric
    #run_visualizer(
    #    key_count=5,
    #    probabilities={1: 0.52, 2: 0, 3: 0.14, 4: 0.34},
    #    orientation="columns",
    #)

    run_visualizer_from_json(str(SAVED_PROBABILITIES_FILE))
    #generate_random_cases(num_of_keys=5, num_of_cases=50)

