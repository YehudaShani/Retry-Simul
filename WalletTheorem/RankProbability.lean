import WalletTheorem.Exchangeability

/-!
# Rank masses and fixed-set fibers

This file connects the exchangeability lemmas to the joint distribution of
the owner and attacker ranks.  The key conclusion is that a rank mass is the
number of sets in that rank times the mass of any one fixed-set fiber.
-/

namespace WalletTheorem

/-- Joint mass of owner rank `i` and attacker rank `j`. -/
noncomputable def rankMass (n : ℕ) (p : Parameters) (i j : ℕ) : ℝ :=
  eventMass p fun ω : Assignment n =>
    (ownerSet ω).card = i ∧ (attackerSet ω).card = j

theorem rankMass_nonneg {n : ℕ} (p : Parameters) (i j : ℕ) :
    0 ≤ rankMass n p i j :=
  eventMass_nonneg p _

/-- Partition a joint rank event by its exact attacker set. -/
theorem rankMass_eq_sum_attackerFibers {n : ℕ} (p : Parameters)
    (i j : ℕ) :
    rankMass n p i j =
      ∑ A ∈ Wallet.fullLayer n j, attackerFiberMass p A i := by
  classical
  unfold rankMass attackerFiberMass eventMass
  rw [Finset.sum_comm]
  apply Finset.sum_congr rfl
  intro ω _
  by_cases hω :
      (ownerSet ω).card = i ∧ (attackerSet ω).card = j
  · rw [if_pos hω]
    have hmem : attackerSet ω ∈ Wallet.fullLayer n j := by
      simpa [Wallet.fullLayer] using hω.2
    simp [hω.1, hmem]
  · rw [if_neg hω]
    symm
    apply Finset.sum_eq_zero
    intro A hA
    have hnot :
        ¬((ownerSet ω).card = i ∧ attackerSet ω = A) := by
      intro h
      apply hω
      refine ⟨h.1, ?_⟩
      rw [h.2]
      simpa [Wallet.fullLayer] using hA
    simp [hnot]

/-- Partition a joint rank event by its exact owner set. -/
theorem rankMass_eq_sum_ownerFibers {n : ℕ} (p : Parameters)
    (i j : ℕ) :
    rankMass n p i j =
      ∑ A ∈ Wallet.fullLayer n i, ownerFiberMass p A j := by
  classical
  unfold rankMass ownerFiberMass eventMass
  rw [Finset.sum_comm]
  apply Finset.sum_congr rfl
  intro ω _
  by_cases hω :
      (ownerSet ω).card = i ∧ (attackerSet ω).card = j
  · rw [if_pos hω]
    have hmem : ownerSet ω ∈ Wallet.fullLayer n i := by
      simpa [Wallet.fullLayer] using hω.1
    simp [hω.2, hmem]
  · rw [if_neg hω]
    symm
    apply Finset.sum_eq_zero
    intro A hA
    have hnot :
        ¬(ownerSet ω = A ∧ (attackerSet ω).card = j) := by
      intro h
      apply hω
      refine ⟨?_, h.2⟩
      rw [h.1]
      simpa [Wallet.fullLayer] using hA
    simp [hnot]

/--
For a fixed attacker set of rank `j`, the total rank mass is
`choose n j` times that fiber's mass.
-/
theorem choose_mul_attackerFiberMass {n : ℕ} (p : Parameters)
    (A : Finset (Fin n)) (i j : ℕ) (hA : A.card = j) :
    (n.choose j : ℝ) * attackerFiberMass p A i = rankMass n p i j := by
  rw [rankMass_eq_sum_attackerFibers]
  calc
    (n.choose j : ℝ) * attackerFiberMass p A i =
        ∑ B ∈ Wallet.fullLayer n j, attackerFiberMass p A i := by
          simp [Wallet.fullLayer]
    _ = ∑ B ∈ Wallet.fullLayer n j, attackerFiberMass p B i := by
          apply Finset.sum_congr rfl
          intro B hB
          apply attackerFiberMass_eq_of_card_eq
          have hBcard : B.card = j := by
            simpa [Wallet.fullLayer] using hB
          exact hA.trans hBcard.symm

/--
For a fixed owner set of rank `i`, the total rank mass is
`choose n i` times that fiber's mass.
-/
theorem choose_mul_ownerFiberMass {n : ℕ} (p : Parameters)
    (A : Finset (Fin n)) (i j : ℕ) (hA : A.card = i) :
    (n.choose i : ℝ) * ownerFiberMass p A j = rankMass n p i j := by
  rw [rankMass_eq_sum_ownerFibers]
  calc
    (n.choose i : ℝ) * ownerFiberMass p A j =
        ∑ B ∈ Wallet.fullLayer n i, ownerFiberMass p A j := by
          simp [Wallet.fullLayer]
    _ = ∑ B ∈ Wallet.fullLayer n i, ownerFiberMass p B j := by
          apply Finset.sum_congr rfl
          intro B hB
          apply ownerFiberMass_eq_of_card_eq
          have hBcard : B.card = i := by
            simpa [Wallet.fullLayer] using hB
          exact hA.trans hBcard.symm

end WalletTheorem
