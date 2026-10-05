import WalletTheorem.WalletEdits
import WalletTheorem.KernelProbability

/-!
# Pointwise probability bounds for batch edits

The finite probability inequalities can be proved assignment by assignment.
This file starts that bridge with the remove-bottom edit.  The abstract
indicator lemma isolates the Boolean bookkeeping from the wallet facts.
-/

namespace WalletTheorem

/-- Weighted success indicator for one complete assignment. -/
noncomputable def successTerm {n : ℕ} (p : Parameters) (F : Wallet n)
    (ω : Assignment n) : ℝ := by
  classical
  exact if IsSuccess F ω then assignmentWeight p ω else 0

theorem successProbability_eq_sum_successTerm {n : ℕ}
    (p : Parameters) (F : Wallet n) :
    successProbability p F = ∑ ω : Assignment n, successTerm p F ω := by
  classical
  unfold successProbability successTerm
  rfl

/--
Boolean bookkeeping behind the remove-bottom bound.  `OF` and `DF` mean
that the owner and attacker sets are authorized; `OR` and `DR` mean that
their ranks equal the removed rank.  `OT` is the guaranteed-authorized owner
tail, and `DB` is the attacker lower tail containing every possible lost
success.
-/
private theorem remove_indicator_bound
    {w : ℝ} (hw : 0 ≤ w)
    (OF DF OR DR OT DB : Prop)
    [Decidable OF] [Decidable DF] [Decidable OR]
    [Decidable DR] [Decidable OT] [Decidable DB]
    (hOTauth : OT → OF)
    (hOTnotRank : OT → ¬OR)
    (hnotDFbelow : ¬DF → DB) :
    (if OT ∧ DF ∧ DR then w else 0) -
          (if OF ∧ OR ∧ DB then w else 0) ≤
      (if OF ∧ ¬OR ∧ ¬(DF ∧ ¬DR) then w else 0) -
        (if OF ∧ ¬DF then w else 0) := by
  by_cases hnegative : OF ∧ OR ∧ DB
  · have hpositive : ¬(OT ∧ DF ∧ DR) := by
      rintro ⟨hOT, _, _⟩
      exact hOTnotRank hOT hnegative.2.1
    simp only [if_neg hpositive, if_pos hnegative, zero_sub]
    split_ifs <;> linarith
  · by_cases hpositive : OT ∧ DF ∧ DR
    · have hafter : OF ∧ ¬OR ∧ ¬(DF ∧ ¬DR) := by
        refine ⟨hOTauth hpositive.1, hOTnotRank hpositive.1, ?_⟩
        exact fun h => h.2 hpositive.2.2
      have hbefore : ¬(OF ∧ ¬DF) := by
        exact fun h => h.2 hpositive.2.1
      simp [hnegative, hpositive, hafter, hbefore]
    · by_cases hbefore : OF ∧ ¬DF
      · have hDB : DB := hnotDFbelow hbefore.2
        have hnotOR : ¬OR := by
          intro hOR
          exact hnegative ⟨hbefore.1, hOR, hDB⟩
        have hafter : OF ∧ ¬OR ∧ ¬(DF ∧ ¬DR) :=
          ⟨hbefore.1, hnotOR, fun h => hbefore.2 h.1⟩
        simp [hnegative, hpositive, hbefore, hafter]
      · simp only [if_neg hnegative, if_neg hpositive,
          if_neg hbefore, sub_zero]
        split_ifs <;> linarith

/--
The per-assignment kernel contribution used to lower-bound removal of the
authorized part of rank `r`.
-/
noncomputable def removeKernelTerm {n : ℕ} (p : Parameters)
    (F : Wallet n) (r q : ℕ) (ω : Assignment n) : ℝ :=
  (if q + 1 ≤ (ownerSet ω).card ∧
        attackerSet ω ∈ F.layer r then assignmentWeight p ω else 0) -
    (if ownerSet ω ∈ F.layer r ∧
        (attackerSet ω).card < q + 1 then assignmentWeight p ω else 0)

/--
Assignmentwise lower bound for removing the bottom authorized layer.

The only facts used are that rank `r` can legally be removed, every rank
above `q` is authorized, and `r < q`.
-/
theorem removeKernelTerm_le_gain {n r q : ℕ}
    (p : Parameters) (F : Wallet n)
    (hmin : ∀ A ∈ F.authorized, r ≤ A.card)
    (hmax : ∀ A : Finset (Fin n), q < A.card → A ∈ F.authorized)
    (hrq : r < q) (ω : Assignment n) :
    removeKernelTerm p F r q ω ≤
      successTerm p (F.removeRank hmin) ω - successTerm p F ω := by
  classical
  unfold removeKernelTerm successTerm
  simp only [IsSuccess, Wallet.mem_removeRank, Wallet.layer,
    Finset.mem_filter]
  simp only [and_assoc]
  apply remove_indicator_bound (assignmentWeight_nonneg p ω)
  · intro htail
    apply hmax
    omega
  · intro htail heq
    omega
  · intro hnot
    by_contra hbelow
    apply hnot
    apply hmax
    omega

end WalletTheorem
