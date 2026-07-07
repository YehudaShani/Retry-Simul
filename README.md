# Retry-Simul

## Setup

```bash
python -m pip install -r requirements.txt
```

## Tests

Run the full test suite with:

```bash
python -m pytest
```

## Repo layout

- `src/helpers/`: importable library code (what tests target)
- `src/scripts/`: runnable utilities and experiments
- `tests/`: pytest tests
- `data/saved_lists/`: curated probability-case JSON files
- `src/helpers/data/wallet_cache/`: precomputed static-wallet cache (authoritative)

Run scripts from the repo root (set `PYTHONPATH` so Python finds `src/`):

```bash
# PowerShell
$env:PYTHONPATH = "src"
python -m scripts.main
python -m scripts.wallet_visualizer
python -m scripts.paper_experiments
```

Or run a script file directly (each script bootstraps `src/` on its own):

```bash
python src/scripts/wallet_visualizer.py
```

## Data paths

Shared path helpers live in `src/helpers/paths.py`:

- `data/saved_lists/saved_probabilities_list.json` — cases saved from the visualizer
- `data/saved_lists/probabilities_list_exchange_leak_with_loss.json` — generated LEAKED/LOST swap cases
- `src/helpers/data/wallet_cache/wallets_{n}.json` — static-wallet cache used by `wallet_cache.py`

Generated outputs (rankings, random cases, etc.) are written under `data/` at the repo root.

## Running `helpers/*` modules

Modules under `src/helpers/` use relative imports, so run them with `-m` from the repo root:

```powershell
$env:PYTHONPATH = "src"
python -m helpers.joint_probabilities
```
