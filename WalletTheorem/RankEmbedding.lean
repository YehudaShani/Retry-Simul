import Mathlib.Data.Set.PowersetCard
import Mathlib.Data.Nat.Choose.Basic

/-!
# Rank-raising embeddings in a Boolean lattice

The paper invokes a symmetric-chain decomposition only to obtain an injection
from the `k`-subsets of an `n`-set into its `j`-subsets when
`k ≤ j ≤ n - k`.  For the wallet proof, no structural property of that
injection is used.  We therefore derive the required embedding directly from
the binomial-cardinality inequality.
-/

namespace WalletTheorem

/--
Binomial coefficients are nondecreasing between ranks `k` and `j` whenever
both ranks lie between `k` and its complementary rank `n - k`.
-/
theorem choose_le_choose_rank {n k j : ℕ} (hkj : k ≤ j) (hcomp : k + j ≤ n) :
    n.choose k ≤ n.choose j := by
  have hjn : j ≤ n - k := by omega
  have hsmall :
      j.choose k ≤ (n - k).choose (j - k) := by
    rw [← Nat.choose_symm hkj]
    exact Nat.choose_le_choose (j - k) hjn
  have hmul :
      n.choose k * j.choose k ≤ n.choose j * j.choose k := by
    calc
      n.choose k * j.choose k
          ≤ n.choose k * (n - k).choose (j - k) :=
            Nat.mul_le_mul_left _ hsmall
      _ = n.choose j * j.choose k := (Nat.choose_mul hkj).symm
  exact Nat.le_of_mul_le_mul_right hmul (Nat.choose_pos hkj)

/--
An abstract rank-raising injection.  This is exactly the consequence of a
symmetric-chain decomposition needed in the coefficient proof.
-/
noncomputable def rankEmbedding
    {α : Type*} [Fintype α] {k j : ℕ}
    (hkj : k ≤ j) (hcomp : k + j ≤ Fintype.card α) :
    Set.powersetCard α k ↪ Set.powersetCard α j :=
  (Function.Embedding.nonempty_of_card_le (by
    simpa only [← Nat.card_eq_fintype_card, Set.powersetCard.card] using
      choose_le_choose_rank hkj hcomp)).some

end WalletTheorem
