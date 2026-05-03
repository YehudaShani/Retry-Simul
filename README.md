"# Retry-Simul"

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

- `src/retry_simul/`: importable library code (what tests target)
- `tests/`: pytest tests
- `scripts/`: runnable utilities / experiments

## Scripts

From the repo root:

```bash
python -m scripts.main
```

Other entrypoints:

```bash
python -m scripts.wallet_visualizer
python -m scripts.paper_experiments
```
