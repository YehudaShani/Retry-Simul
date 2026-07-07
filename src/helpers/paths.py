"""Repo-root and data-path helpers shared by scripts and library code."""

from __future__ import annotations

from pathlib import Path

# helpers/paths.py lives at src/helpers/paths.py
_SRC = Path(__file__).resolve().parents[1]
REPO_ROOT = _SRC.parent


def repo_root() -> Path:
    return REPO_ROOT


def data_path(*parts: str) -> Path:
    return REPO_ROOT / "data" / Path(*parts)


def repo_relative(path: str | Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else REPO_ROOT / path


SAVED_PROBABILITIES_FILE = data_path("saved_lists", "saved_probabilities_list.json")
PROBABILITIES_EXCHANGE_LEAK_WITH_LOSS_FILE = data_path(
    "saved_lists", "probabilities_list_exchange_leak_with_loss.json"
)
