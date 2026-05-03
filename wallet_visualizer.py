from scripts.wallet_visualizer import *  # noqa: F403


if __name__ == "__main__":
    # Keep backward-compatible behavior for running from repo root:
    # `python wallet_visualizer.py`
    from scripts.wallet_visualizer import run_visualizer

    run_visualizer(
        key_count=3,
        probabilities={1: 1 / 30, 2: 1 / 30, 3: 1 / 5, 4: 11 / 15},
        orientation="columns",
    )
