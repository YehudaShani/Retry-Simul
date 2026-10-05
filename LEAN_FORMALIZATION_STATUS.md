# Lean formalization status

The Lean project in this repository uses Lean `v4.32.1` and Mathlib
`v4.32.1`.  The paper's exact four-state finite model and target proposition
are defined in `WalletTheorem/Model.lean`.

## Kernel-checked so far

All declarations listed here compile without `sorry`, `admit`, or axioms.

- `Model.lean`
  - the four key states and independent product weights;
  - nonnegativity and normalization of the finite probability distribution;
  - upward-closed wallets, incomplete ranks, and the exact
    canonicalization proposition.
- `Duality.lean`
  - leaked/lost state duality;
  - complementation of authorization families;
  - preservation of success probability;
  - reflection of incomplete ranks about the middle layer.
- `RankEmbedding.lean`
  - the binomial inequality
    `choose n k ≤ choose n j` when `k ≤ j` and `k+j ≤ n`;
  - the rank-raising injection needed in place of the paper's
    symmetric-chain decomposition.
- `CoefficientArithmetic.lean`
  - both subtraction-heavy rank-raising conditions in the `L`- and
    `E`-case injections;
  - construction of the corresponding Boolean-rank embeddings;
  - the output cardinality identities.
- `Kernel.lean` and `Batch.lean`
  - the discrete derivative of the finite rank kernel;
  - the common-jump identity;
  - normalization of the boxed binomial certificate;
  - the complete four-way sign argument that selects a non-worsening
    remove, fill, or joint batch edit.
- `Termination.lean`
  - strong-induction termination once each non-worsening step removes an
    incomplete layer.
- `ToggleCheck.lean`
  - an executable, exact integer implementation of every coefficient in
    the boxed kernel certificate;
  - exhaustive kernel-certified verification of all such coefficients for
    `n ≤ 8`.

## What remains for a complete proof

Two general combinatorial bridges are not yet formalized:

1. derive the four batch-edit probability bounds from exchangeability of the
   finite product model; and
2. assemble the fixed-`M` maps in the paper's `L` and `E` cases into a single
   all-`n` injection proving every toggle coefficient nonnegative.

Accordingly, the repository currently contains a substantial checked
formalization and an exact bounded coefficient verification, but not yet a
Lean proof of `CanonicalizationStatement` for arbitrary `n`.

## Build

With `elan`/Lean available:

```text
lake update
lake exe cache get
lake build
```
