import WalletTheorem.Model

/-!
# Wallet duality

The high-sum part of the paper reduces to the low-sum part by complementing
authorization sets and exchanging leaked with lost key states.  This file
checks the transformation and the exact equality of success probabilities.
-/

namespace WalletTheorem

/-- Apply the leaked/lost involution coordinatewise. -/
def dualAssignment {n : ℕ} (ω : Assignment n) : Assignment n :=
  fun i => (ω i).dual

@[simp] theorem dualAssignment_dualAssignment {n : ℕ} (ω : Assignment n) :
    dualAssignment (dualAssignment ω) = ω := by
  funext i
  exact KeyState.dual_dual (ω i)

/-- Coordinatewise duality is an equivalence on assignments. -/
def dualAssignmentEquiv (n : ℕ) : Assignment n ≃ Assignment n where
  toFun := dualAssignment
  invFun := dualAssignment
  left_inv := dualAssignment_dualAssignment
  right_inv := dualAssignment_dualAssignment

@[simp] theorem ownerSet_dualAssignment {n : ℕ} (ω : Assignment n) :
    ownerSet (dualAssignment ω) = Finset.univ \ attackerSet ω := by
  ext i
  simp [ownerSet, attackerSet, dualAssignment]

@[simp] theorem attackerSet_dualAssignment {n : ℕ} (ω : Assignment n) :
    attackerSet (dualAssignment ω) = Finset.univ \ ownerSet ω := by
  ext i
  simp [ownerSet, attackerSet, dualAssignment]

@[simp] theorem assignmentWeight_dualAssignment {n : ℕ}
    (p : Parameters) (ω : Assignment n) :
    assignmentWeight p.dual (dualAssignment ω) = assignmentWeight p ω := by
  simp [assignmentWeight, dualAssignment]

namespace Wallet

/-- Complement authorization and negate membership. -/
noncomputable def dual {n : ℕ} (F : Wallet n) : Wallet n := by
  classical
  refine
    { authorized :=
        (Finset.univ : Finset (Finset (Fin n))).filter fun A =>
          Finset.univ \ A ∉ F.authorized
      upward' := ?_ }
  intro A B hA hAB
  simp only [Finset.mem_filter, Finset.mem_univ, true_and] at hA ⊢
  intro hcompB
  apply hA
  apply F.upward hcompB
  intro i hi
  simp only [Finset.mem_sdiff, Finset.mem_univ, true_and] at hi ⊢
  exact fun hiA => hi (hAB hiA)

@[simp] theorem mem_dual {n : ℕ} (F : Wallet n) (A : Finset (Fin n)) :
    A ∈ F.dual.authorized ↔ Finset.univ \ A ∉ F.authorized := by
  classical
  simp [dual]

/-- Cardinality of a complement in the `n`-key universe. -/
theorem card_compl {n : ℕ} (A : Finset (Fin n)) :
    (Finset.univ \ A).card = n - A.card := by
  rw [Finset.card_sdiff]
  simp

/-- Incomplete ranks are reflected about the middle rank by duality. -/
theorem incomplete_dual_iff {n k : ℕ} (F : Wallet n) (hk : k ≤ n) :
    F.dual.Incomplete (n - k) ↔ F.Incomplete k := by
  classical
  constructor
  · rintro ⟨⟨C, hCcard, hCmem⟩, ⟨D, hDcard, hDnot⟩⟩
    constructor
    · refine ⟨Finset.univ \ D, ?_, ?_⟩
      · rw [card_compl, hDcard, Nat.sub_sub_self hk]
      · by_contra hcompD
        exact hDnot ((mem_dual F D).2 (by simpa using hcompD))
    · refine ⟨Finset.univ \ C, ?_, ?_⟩
      · rw [card_compl, hCcard, Nat.sub_sub_self hk]
      · simpa using (mem_dual F C).1 hCmem
  · rintro ⟨⟨A, hAcard, hAmem⟩, ⟨B, hBcard, hBnot⟩⟩
    constructor
    · refine ⟨Finset.univ \ B, ?_, ?_⟩
      · simp [card_compl, hBcard]
      · apply (mem_dual F _).2
        simpa using hBnot
    · refine ⟨Finset.univ \ A, ?_, ?_⟩
      · simp [card_compl, hAcard]
      · intro hdual
        exact (mem_dual F _).1 hdual (by simpa using hAmem)

end Wallet

@[simp] theorem isSuccess_dual {n : ℕ} (F : Wallet n) (ω : Assignment n) :
    IsSuccess F.dual (dualAssignment ω) ↔ IsSuccess F ω := by
  classical
  simp [IsSuccess, and_comm]

/-- Wallet duality preserves the exact success probability. -/
theorem successProbability_dual {n : ℕ} (p : Parameters) (F : Wallet n) :
    successProbability p.dual F.dual = successProbability p F := by
  classical
  unfold successProbability
  symm
  apply Fintype.sum_equiv (dualAssignmentEquiv n)
  intro ω
  change
    (if IsSuccess F ω then assignmentWeight p ω else 0) =
      (if IsSuccess F.dual (dualAssignment ω) then
        assignmentWeight p.dual (dualAssignment ω) else 0)
  simp

end WalletTheorem
