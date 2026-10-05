import WalletTheorem.Batch
import WalletTheorem.RankEmbedding
import Mathlib.Order.Interval.Finset.Nat

/-!
# Rank kernel

This file formalizes the discrete kernel identities used between the
probabilistic batch bounds and the kernel certificate.
-/

namespace WalletTheorem

/--
The rank kernel of a joint mass function `P`.

The first sum is `P(I ≥ m, J = k)` and the second is
`P(I = k, J < m)`.  Values of `P` need not be normalized for the algebraic
identities below.
-/
def rankKernel (n : ℕ) (P : ℕ → ℕ → ℝ) (k m : ℕ) : ℝ :=
  (∑ i ∈ Finset.Ico m (n + 1), P i k) -
    ∑ j ∈ Finset.range m, P k j

/-- The elementary discrete derivative of the rank kernel. -/
theorem rankKernel_succ {n : ℕ} (P : ℕ → ℕ → ℝ) {k m : ℕ} (hm : m ≤ n) :
    rankKernel n P k (m + 1) - rankKernel n P k m =
      -P m k - P k m := by
  have hlt : m < n + 1 := Nat.lt_succ_iff.mpr hm
  have htail :
      (∑ i ∈ Finset.Ico m (n + 1), P i k) =
        P m k + ∑ i ∈ Finset.Ico (m + 1) (n + 1), P i k := by
    rw [← Finset.insert_Ico_succ_left_eq_Ico hlt]
    simp
  simp only [rankKernel, Finset.sum_range_succ]
  rw [htail]
  ring

/--
At ranks `r < q`, the two kernel values used in the certificate have the
same jump `P(q,r)+P(r,q)`.
-/
theorem rankKernel_common_jump {n : ℕ} (P : ℕ → ℕ → ℝ)
    {r q : ℕ} (hr : r ≤ n) (hq : q ≤ n) :
    rankKernel n P r (q + 1) =
        rankKernel n P r q - (P q r + P r q) ∧
      rankKernel n P q (r + 1) =
        rankKernel n P q r - (P q r + P r q) := by
  constructor
  · have h := rankKernel_succ P (k := r) hq
    linarith
  · have h := rankKernel_succ P (k := q) hr
    linarith

/--
The raw binomial kernel certificate implies that one of the four batch lower
bounds is nonnegative.  This is the paper's complete low-sum sign argument,
now connected to the literal finite-sum definition of `g`.
-/
theorem lowSum_four_bounds_of_certificate
    {n r q : ℕ} (P : ℕ → ℕ → ℝ) {a b : ℝ}
    (hrq : r < q) (hsum : r + q ≤ n)
    (ha : 0 < a) (hb : 0 < b)
    (hcertificate :
      (n.choose r : ℝ) * rankKernel n P q (r + 1) ≤
        (n.choose q : ℝ) * rankKernel n P r (q + 1)) :
    0 ≤ a * rankKernel n P r (q + 1) ∨
      0 ≤ -b * rankKernel n P q r ∨
      0 ≤ a * rankKernel n P r q - b * rankKernel n P q r ∨
      0 ≤ a * rankKernel n P r (q + 1) -
        b * rankKernel n P q (r + 1) := by
  have hrn : r ≤ n := by omega
  have hqn : q ≤ n := by omega
  have hrqle : r ≤ q := Nat.le_of_lt hrq
  have hchoose : n.choose r ≤ n.choose q :=
    choose_le_choose_rank hrqle hsum
  have hdenNat : 0 < n.choose r := Nat.choose_pos hrn
  have hden : (0 : ℝ) < n.choose r := by exact_mod_cast hdenNat
  let ρ : ℝ := (n.choose q : ℝ) / n.choose r
  have hρ : 1 ≤ ρ := by
    dsimp [ρ]
    apply (le_div_iff₀ hden).2
    simpa only [one_mul] using
      (show (n.choose r : ℝ) ≤ n.choose q by exact_mod_cast hchoose)
  have hnormalized :
      rankKernel n P q (r + 1) ≤
        ρ * rankKernel n P r (q + 1) := by
    calc
      rankKernel n P q (r + 1)
          ≤ ((n.choose q : ℝ) * rankKernel n P r (q + 1)) /
              (n.choose r : ℝ) := by
            apply (le_div_iff₀ hden).2
            simpa only [mul_comm] using hcertificate
      _ = ρ * rankKernel n P r (q + 1) := by
            dsimp [ρ]
            ring
  obtain ⟨hx, hy⟩ := rankKernel_common_jump P hrn hqn
  exact exists_nonworsening_batch ha hb hρ hx hy hnormalized

end WalletTheorem
