import Mathlib

/-!
# The batch-edit argument for the wallet theorem

This file formalizes the algebraic heart of Sections 2--3 of
`COMPLETE_PROOF_INCOMPLETE_LAYERS.tex`.

The probabilistic part of the paper supplies four lower bounds for the changes
caused by removing the bottom incomplete layer, filling the top incomplete
layer, or doing both.  The kernel certificate then forces at least one of
those lower bounds to be nonnegative.  `exists_nonworsening_batch` verifies
that implication without any hidden division or informal sign argument.
-/

namespace WalletTheorem

/--
Algebraic form of the low-sum batch-improvement lemma.

Here `a` and `b` are the densities `α` and `β`; `x₀ = g_r(q)`,
`x₁ = g_r(q+1)`, `y₀ = g_q(r)`, and `y₁ = g_q(r+1)`.
The two equations encode the common jump `w`, and
`ρ * x₁ ≥ y₁` is the normalized kernel certificate.
-/
theorem exists_nonworsening_batch
    {a b ρ x₀ x₁ y₀ y₁ w : ℝ}
    (ha : 0 < a) (hb : 0 < b) (hρ : 1 ≤ ρ)
    (hx : x₁ = x₀ - w) (hy : y₁ = y₀ - w)
    (hcertificate : y₁ ≤ ρ * x₁) :
    0 ≤ a * x₁ ∨
      0 ≤ -b * y₀ ∨
      0 ≤ a * x₀ - b * y₀ ∨
      0 ≤ a * x₁ - b * y₁ := by
  by_cases hx₁ : 0 ≤ x₁
  · exact Or.inl (mul_nonneg (le_of_lt ha) hx₁)
  right
  by_cases hy₀ : y₀ ≤ 0
  · exact Or.inl
      (mul_nonneg_of_nonpos_of_nonpos (neg_nonpos.mpr (le_of_lt hb)) hy₀)
  right

  have hx₁neg : x₁ < 0 := lt_of_not_ge hx₁
  have hy₀pos : 0 < y₀ := lt_of_not_ge hy₀
  have hρx : ρ * x₁ ≤ x₁ := by
    simpa only [one_mul] using
      (mul_le_mul_of_nonpos_right hρ (le_of_lt hx₁neg))
  have horder₁ : y₁ ≤ x₁ := hcertificate.trans hρx
  have horder₀ : y₀ ≤ x₀ := by
    calc
      y₀ = y₁ + w := by linarith [hy]
      _ ≤ x₁ + w := by
        simpa only [add_comm] using add_le_add_right horder₁ w
      _ = x₀ := by linarith [hx]

  by_cases hjoint₁ : 0 ≤ a * x₀ - b * y₀
  · exact Or.inl hjoint₁
  right

  have hx₀pos : 0 < x₀ := lt_of_lt_of_le hy₀pos horder₀
  have hab : a < b := by
    by_contra h
    have hba : b ≤ a := le_of_not_gt h
    have hmul : b * y₀ ≤ a * x₀ :=
      (mul_le_mul_of_nonneg_right hba (le_of_lt hy₀pos)).trans
        (mul_le_mul_of_nonneg_left horder₀ (le_of_lt ha))
    exact (not_lt_of_ge hmul) (sub_neg.mp (lt_of_not_ge hjoint₁))
  have hby : b * y₁ ≤ b * x₁ :=
    mul_le_mul_of_nonneg_left horder₁ (le_of_lt hb)
  have hbxa : b * x₁ < a * x₁ :=
    mul_lt_mul_of_neg_right hab hx₁neg
  exact le_of_lt (sub_pos.mpr (hby.trans_lt hbxa))

end WalletTheorem
