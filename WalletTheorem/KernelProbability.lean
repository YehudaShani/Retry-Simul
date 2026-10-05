import WalletTheorem.RankProbability
import WalletTheorem.Kernel

/-!
# Probabilistic interpretation of the rank kernel

For a fixed set `A` of rank `k`, the rank kernel is the binomial multiple of
the difference between:

* assignments whose attacker set is exactly `A` and whose owner rank is at
  least `m`; and
* assignments whose owner set is exactly `A` and whose attacker rank is
  below `m`.

This is the exchangeability normalization used in every batch-edit bound.
-/

namespace WalletTheorem

/-- Mass with a fixed attacker set and owner rank at least `m`. -/
noncomputable def attackerTailMass {n : ℕ} (p : Parameters)
    (A : Finset (Fin n)) (m : ℕ) : ℝ :=
  eventMass p fun ω => m ≤ (ownerSet ω).card ∧ attackerSet ω = A

/-- Mass with a fixed owner set and attacker rank below `m`. -/
noncomputable def ownerBelowMass {n : ℕ} (p : Parameters)
    (A : Finset (Fin n)) (m : ℕ) : ℝ :=
  eventMass p fun ω => ownerSet ω = A ∧ (attackerSet ω).card < m

theorem attackerTailMass_nonneg {n : ℕ} (p : Parameters)
    (A : Finset (Fin n)) (m : ℕ) :
    0 ≤ attackerTailMass p A m :=
  eventMass_nonneg p _

theorem ownerBelowMass_nonneg {n : ℕ} (p : Parameters)
    (A : Finset (Fin n)) (m : ℕ) :
    0 ≤ ownerBelowMass p A m :=
  eventMass_nonneg p _

private theorem ownerCard_le {n : ℕ} (ω : Assignment n) :
    (ownerSet ω).card ≤ n := by
  calc
    (ownerSet ω).card ≤ (Finset.univ : Finset (Fin n)).card :=
      Finset.card_le_card (Finset.subset_univ _)
    _ = n := by simp

/-- Split a fixed-attacker tail according to the exact owner rank. -/
theorem attackerTailMass_eq_sum {n : ℕ} (p : Parameters)
    (A : Finset (Fin n)) (m : ℕ) :
    attackerTailMass p A m =
      ∑ i ∈ Finset.Ico m (n + 1), attackerFiberMass p A i := by
  classical
  unfold attackerTailMass attackerFiberMass eventMass
  rw [Finset.sum_comm]
  apply Finset.sum_congr rfl
  intro ω _
  by_cases hω : m ≤ (ownerSet ω).card ∧ attackerSet ω = A
  · rw [if_pos hω]
    have hmem : (ownerSet ω).card ∈ Finset.Ico m (n + 1) := by
      simp only [Finset.mem_Ico]
      exact ⟨hω.1, Nat.lt_succ_iff.mpr (ownerCard_le ω)⟩
    simp [hω.2, hmem]
  · rw [if_neg hω]
    symm
    apply Finset.sum_eq_zero
    intro i hi
    have hnot :
        ¬((ownerSet ω).card = i ∧ attackerSet ω = A) := by
      intro h
      apply hω
      have him : m ≤ i := (Finset.mem_Ico.mp hi).1
      exact ⟨h.1.symm ▸ him, h.2⟩
    simp [hnot]

/-- Split a fixed-owner lower tail according to the exact attacker rank. -/
theorem ownerBelowMass_eq_sum {n : ℕ} (p : Parameters)
    (A : Finset (Fin n)) (m : ℕ) :
    ownerBelowMass p A m =
      ∑ j ∈ Finset.range m, ownerFiberMass p A j := by
  classical
  unfold ownerBelowMass ownerFiberMass eventMass
  rw [Finset.sum_comm]
  apply Finset.sum_congr rfl
  intro ω _
  by_cases hω : ownerSet ω = A ∧ (attackerSet ω).card < m
  · rw [if_pos hω]
    have hmem : (attackerSet ω).card ∈ Finset.range m := by
      simpa using hω.2
    simp [hω.1, hmem]
  · rw [if_neg hω]
    symm
    apply Finset.sum_eq_zero
    intro j hj
    have hnot :
        ¬(ownerSet ω = A ∧ (attackerSet ω).card = j) := by
      intro h
      apply hω
      exact ⟨h.1, h.2.symm ▸ Finset.mem_range.mp hj⟩
    simp [hnot]

/-- The fixed-set form of the paper's kernel. -/
noncomputable def fixedSetKernel {n : ℕ} (p : Parameters)
    (A : Finset (Fin n)) (m : ℕ) : ℝ :=
  attackerTailMass p A m - ownerBelowMass p A m

/--
Exchangeability identifies the rank kernel with `choose n k` times the
fixed-set kernel for every set of rank `k`.
-/
theorem choose_mul_fixedSetKernel_eq_rankKernel {n : ℕ}
    (p : Parameters) (A : Finset (Fin n)) (k m : ℕ)
    (hA : A.card = k) :
    (n.choose k : ℝ) * fixedSetKernel p A m =
      rankKernel n (rankMass n p) k m := by
  rw [fixedSetKernel, attackerTailMass_eq_sum, ownerBelowMass_eq_sum]
  unfold rankKernel
  rw [mul_sub, Finset.mul_sum, Finset.mul_sum]
  congr 1
  · apply Finset.sum_congr rfl
    intro i _
    exact choose_mul_attackerFiberMass p A i k hA
  · apply Finset.sum_congr rfl
    intro j _
    exact choose_mul_ownerFiberMass p A k j hA

end WalletTheorem
