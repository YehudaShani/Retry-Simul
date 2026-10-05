import WalletTheorem.RankEmbedding
import Mathlib.Tactic

/-!
# Arithmetic side conditions in the coefficient injections

Sections 6 and 7 of the paper use rank-raising injections.  The easy-looking
side conditions are subtraction-heavy on paper, so they are worth checking
independently.  The statements below use subtraction-free cardinality
equations; `omega` verifies the two deductions in Presburger arithmetic.
-/

namespace WalletTheorem

/--
The rank-raising condition in the `L`-case.

`T, b, L, d, δ, k₀` are the outside-block parameters, `j` is the size
of the selected outside `L`-set, `s` is the positive shift, `k` is the
source `T`-rank, and `aE` is the selected `E`-rank.
-/
theorem lCase_raising_condition
    {T b L d δ k₀ j s k aE : ℕ}
    (hblocks : 2 * k₀ + b + d + δ = T + L)
    (hk : k + j = k₀)
    (hAE : aE + δ + j = L + s)
    (hAE_le : aE ≤ b) :
    k + (k + s) ≤ T := by
  omega

/-- The actual Boolean-rank embedding justified by `lCase_raising_condition`. -/
noncomputable def lCase_rankEmbedding
    {T b L d δ k₀ j s k aE : ℕ}
    (hblocks : 2 * k₀ + b + d + δ = T + L)
    (hk : k + j = k₀)
    (hAE : aE + δ + j = L + s)
    (hAE_le : aE ≤ b) :
    Set.powersetCard (Fin T) k ↪ Set.powersetCard (Fin T) (k + s) :=
  rankEmbedding (Nat.le_add_right k s)
    (by
      simpa using
        (lCase_raising_condition (T := T) (b := b) (L := L) (d := d)
          (δ := δ) (k₀ := k₀) (j := j) (s := s) (k := k) (aE := aE)
          hblocks hk hAE hAE_le))

/--
The output-cardinality equations in the `L`-case injection.

The image has `T`-rank `k+s`; the canonical lost set has size
`L-j+s-1`.  The latter equation is supplied without subtraction as
`w+j+1 = L+s`.
-/
theorem lCase_output_conditions
    {L δ k₀ j s k aE k' w : ℕ}
    (hk : k + j = k₀)
    (hAE : aE + δ + j = L + s)
    (hk' : k' = k + s)
    (hw : w + j + 1 = L + s) :
    aE + δ + k₀ = L + k' ∧ w + k₀ + 1 = L + k' := by
  omega

/--
The rank-raising condition in the `E`-case.

Here `aE + δ + j = c` records the chosen outside `E`-set, while
`s ≤ j+1` records the nonempty outside `L`-choice.  The injection raises
rank by `s-1`, represented by the equation `shift+1=s`.
-/
theorem eCase_raising_condition
    {T E c d δ k₀ j s shift k aE : ℕ}
    (hblocks : 2 * k₀ + E + d + δ = T + c)
    (hk : k + j = k₀)
    (hAE : aE + δ + j = c)
    (hAE_le : aE ≤ E)
    (hs : s ≤ j + 1)
    (hshift : shift + 1 = s) :
    k + (k + shift) ≤ T := by
  omega

/-- The actual Boolean-rank embedding justified by `eCase_raising_condition`. -/
noncomputable def eCase_rankEmbedding
    {T E c d δ k₀ j s shift k aE : ℕ}
    (hblocks : 2 * k₀ + E + d + δ = T + c)
    (hk : k + j = k₀)
    (hAE : aE + δ + j = c)
    (hAE_le : aE ≤ E)
    (hs : s ≤ j + 1)
    (hshift : shift + 1 = s) :
    Set.powersetCard (Fin T) k ↪ Set.powersetCard (Fin T) (k + shift) :=
  rankEmbedding (Nat.le_add_right k shift)
    (by
      simpa using
        (eCase_raising_condition (T := T) (E := E) (c := c) (d := d)
          (δ := δ) (k₀ := k₀) (j := j) (s := s) (shift := shift)
          (k := k) (aE := aE) hblocks hk hAE hAE_le hs hshift))

/--
The output-cardinality equation in the `E`-case: extending the `E`-set
and raising the `T`-set by the same shift changes the summation index from
`j` to `j-shift`.
-/
theorem eCase_output_condition
    {c δ k₀ j shift k aE k' aE' : ℕ}
    (hk : k + j = k₀)
    (hAE : aE + δ + j = c)
    (hk' : k' = k + shift)
    (hAE' : aE' = aE + shift) :
    aE' + δ + k₀ = c + k' := by
  omega

end WalletTheorem
