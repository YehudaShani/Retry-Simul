import WalletTheorem.Model

/-!
# Finite termination of batch improvements

Once one non-worsening edit removes at least one incomplete layer, the main
canonicalization statement follows by strong induction.  This file isolates
and verifies that final argument.
-/

namespace WalletTheorem

/--
Any score function with a strictly layer-reducing, non-worsening step above
one incomplete layer admits a canonical representative.
-/
theorem canonicalization_of_step {n : ℕ} (score : Wallet n → ℝ)
    (step :
      ∀ F : Wallet n, 1 < F.incompleteRanks.card →
        ∃ F' : Wallet n,
          score F ≤ score F' ∧
            F'.incompleteRanks.card < F.incompleteRanks.card) :
  ∀ F : Wallet n,
      ∃ Fstar : Wallet n,
        score F ≤ score Fstar ∧ Fstar.incompleteRanks.card ≤ 1 := by
  intro F
  induction hcard : F.incompleteRanks.card using Nat.strong_induction_on generalizing F with
  | h m ih =>
      subst hcard
      by_cases hsmall : F.incompleteRanks.card ≤ 1
      · exact ⟨F, le_rfl, hsmall⟩
      · have hlarge : 1 < F.incompleteRanks.card := by
          exact Nat.lt_of_not_ge hsmall
        obtain ⟨F', hscore, hcard⟩ := step F hlarge
        obtain ⟨Fstar, hscore', hcanonical⟩ :=
          ih F'.incompleteRanks.card hcard F' rfl
        exact ⟨Fstar, hscore.trans hscore', hcanonical⟩

/--
Specialization showing the exact remaining obligation for the wallet theorem:
construct one layer-reducing batch edit whenever two incomplete layers remain.
-/
theorem canonicalization_from_wallet_step {n : ℕ} (p : Parameters)
    (step :
      ∀ F : Wallet n, 1 < F.incompleteRanks.card →
        ∃ F' : Wallet n,
          successProbability p F ≤ successProbability p F' ∧
            F'.incompleteRanks.card < F.incompleteRanks.card) :
    ∀ F : Wallet n,
      ∃ Fstar : Wallet n,
        successProbability p F ≤ successProbability p Fstar ∧
          Fstar.incompleteRanks.card ≤ 1 :=
  canonicalization_of_step (successProbability p) step

end WalletTheorem
