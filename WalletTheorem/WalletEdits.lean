import WalletTheorem.Model

/-!
# Extreme incomplete ranks and legal batch edits

The bottom incomplete rank has no authorized sets below it, and the top
incomplete rank has every set above it authorized.  These facts make it legal
to remove the whole authorized bottom layer or fill the whole top layer while
preserving upward closure.
-/

namespace WalletTheorem

namespace Wallet

/-- `r` is an incomplete rank and no smaller rank is incomplete. -/
def IsBottomIncomplete {n : ℕ} (F : Wallet n) (r : ℕ) : Prop :=
  F.Incomplete r ∧ ∀ k < r, ¬F.Incomplete k

/-- `q` is an incomplete rank and no larger rank is incomplete. -/
def IsTopIncomplete {n : ℕ} (F : Wallet n) (q : ℕ) : Prop :=
  F.Incomplete q ∧ ∀ k, q < k → ¬F.Incomplete k

/-- The rank of every key set is at most the total number of keys. -/
theorem setCard_le {n : ℕ} (A : Finset (Fin n)) : A.card ≤ n := by
  calc
    A.card ≤ (Finset.univ : Finset (Fin n)).card :=
      Finset.card_le_card (Finset.subset_univ _)
    _ = n := by simp

/-- No authorized set lies below the bottom incomplete rank. -/
theorem no_authorized_below_of_bottom {n r : ℕ} (F : Wallet n)
    (hr : F.IsBottomIncomplete r) :
    ∀ A ∈ F.authorized, r ≤ A.card := by
  intro A hA
  by_contra hnot
  have hAr : A.card < r := Nat.lt_of_not_ge hnot
  have hcomplete : ¬F.Incomplete A.card := hr.2 A.card hAr
  obtain ⟨C, hCcard, hCnot⟩ := hr.1.2
  have hle : A.card ≤ C.card := by omega
  obtain ⟨B, hBC, hBcard⟩ := C.exists_subset_card_eq hle
  have hBauth : B ∈ F.authorized := by
    by_contra hBnot
    apply hcomplete
    exact ⟨⟨A, rfl, hA⟩, ⟨B, hBcard, hBnot⟩⟩
  exact hCnot (F.upward hBauth hBC)

/-- Every set above the top incomplete rank is authorized. -/
theorem all_authorized_above_of_top {n q : ℕ} (F : Wallet n)
    (hq : F.IsTopIncomplete q) :
    ∀ A : Finset (Fin n), q < A.card → A ∈ F.authorized := by
  intro A hqA
  by_contra hAnot
  have hcomplete : ¬F.Incomplete A.card := hq.2 A.card hqA
  obtain ⟨C, hCcard, hCauth⟩ := hq.1.1
  have hC_le : C.card ≤ A.card := by omega
  have hA_le : A.card ≤ (Finset.univ : Finset (Fin n)).card :=
    Finset.card_le_card (Finset.subset_univ _)
  obtain ⟨D, hCD, _, hDcard⟩ :=
    Finset.exists_subsuperset_card_eq (Finset.subset_univ C) hC_le hA_le
  have hDauth : D ∈ F.authorized := F.upward hCauth hCD
  apply hcomplete
  exact ⟨⟨D, hDcard, hDauth⟩, ⟨A, rfl, hAnot⟩⟩

/-- Remove every authorized set in rank `r`. -/
noncomputable def removeRank {n r : ℕ} (F : Wallet n)
    (hmin : ∀ A ∈ F.authorized, r ≤ A.card) : Wallet n := by
  classical
  refine
    { authorized := F.authorized.filter fun A => A.card ≠ r
      upward' := ?_ }
  intro A B hA hAB
  simp only [Finset.mem_filter] at hA ⊢
  refine ⟨F.upward hA.1 hAB, ?_⟩
  intro hBcard
  apply hA.2
  apply Nat.le_antisymm
  · have := Finset.card_le_card hAB
    omega
  · exact hmin A hA.1

@[simp] theorem mem_removeRank {n r : ℕ} (F : Wallet n)
    (hmin : ∀ A ∈ F.authorized, r ≤ A.card)
    (A : Finset (Fin n)) :
    A ∈ (F.removeRank hmin).authorized ↔
      A ∈ F.authorized ∧ A.card ≠ r := by
  classical
  simp [removeRank]

/-- Fill every set in rank `q`. -/
noncomputable def fillRank {n q : ℕ} (F : Wallet n)
    (hmax : ∀ A : Finset (Fin n), q < A.card → A ∈ F.authorized) :
    Wallet n := by
  classical
  refine
    { authorized := F.authorized ∪ Wallet.fullLayer n q
      upward' := ?_ }
  intro A B hA hAB
  simp only [Finset.mem_union] at hA ⊢
  rcases hA with hA | hA
  · exact Or.inl (F.upward hA hAB)
  · have hAcard : A.card = q := by
      simpa [Wallet.fullLayer] using hA
    by_cases hBcard : B.card = q
    · exact Or.inr (by simpa [Wallet.fullLayer] using hBcard)
    · apply Or.inl
      apply hmax B
      have hle := Finset.card_le_card hAB
      omega

@[simp] theorem mem_fillRank {n q : ℕ} (F : Wallet n)
    (hmax : ∀ A : Finset (Fin n), q < A.card → A ∈ F.authorized)
    (A : Finset (Fin n)) :
    A ∈ (F.fillRank hmax).authorized ↔
      A ∈ F.authorized ∨ A.card = q := by
  classical
  simp [fillRank, Wallet.fullLayer]

theorem not_incomplete_removeRank {n r : ℕ} (F : Wallet n)
    (hmin : ∀ A ∈ F.authorized, r ≤ A.card) :
    ¬(F.removeRank hmin).Incomplete r := by
  rintro ⟨⟨A, hAcard, hAmem⟩, _⟩
  exact (mem_removeRank F hmin A).1 hAmem |>.2 hAcard

theorem not_incomplete_fillRank {n q : ℕ} (F : Wallet n)
    (hmax : ∀ A : Finset (Fin n), q < A.card → A ∈ F.authorized) :
    ¬(F.fillRank hmax).Incomplete q := by
  rintro ⟨_, ⟨A, hAcard, hAnot⟩⟩
  exact hAnot ((mem_fillRank F hmax A).2 (Or.inr hAcard))

/-- Removing rank `r` changes no other rank. -/
theorem incomplete_removeRank_iff {n r k : ℕ} (F : Wallet n)
    (hmin : ∀ A ∈ F.authorized, r ≤ A.card) (hkr : k ≠ r) :
    (F.removeRank hmin).Incomplete k ↔ F.Incomplete k := by
  constructor
  · rintro ⟨⟨A, hAcard, hAmem⟩, ⟨B, hBcard, hBnot⟩⟩
    refine ⟨⟨A, hAcard, (mem_removeRank F hmin A).1 hAmem |>.1⟩,
      ⟨B, hBcard, ?_⟩⟩
    intro hBmem
    apply hBnot
    exact (mem_removeRank F hmin B).2 ⟨hBmem, hBcard.trans_ne hkr⟩
  · rintro ⟨⟨A, hAcard, hAmem⟩, ⟨B, hBcard, hBnot⟩⟩
    refine ⟨⟨A, hAcard, (mem_removeRank F hmin A).2
      ⟨hAmem, hAcard.trans_ne hkr⟩⟩, ⟨B, hBcard, ?_⟩⟩
    intro hBmem
    exact hBnot ((mem_removeRank F hmin B).1 hBmem |>.1)

/-- Filling rank `q` changes no other rank. -/
theorem incomplete_fillRank_iff {n q k : ℕ} (F : Wallet n)
    (hmax : ∀ A : Finset (Fin n), q < A.card → A ∈ F.authorized)
    (hkq : k ≠ q) :
    (F.fillRank hmax).Incomplete k ↔ F.Incomplete k := by
  constructor
  · rintro ⟨⟨A, hAcard, hAmem⟩, ⟨B, hBcard, hBnot⟩⟩
    refine ⟨⟨A, hAcard, ?_⟩, ⟨B, hBcard, ?_⟩⟩
    · rcases (mem_fillRank F hmax A).1 hAmem with hAmem | hAq
      · exact hAmem
      · exact (hkq (hAcard.symm.trans hAq)).elim
    · intro hBmem
      exact hBnot ((mem_fillRank F hmax B).2 (Or.inl hBmem))
  · rintro ⟨⟨A, hAcard, hAmem⟩, ⟨B, hBcard, hBnot⟩⟩
    refine ⟨⟨A, hAcard, (mem_fillRank F hmax A).2 (Or.inl hAmem)⟩,
      ⟨B, hBcard, ?_⟩⟩
    intro hBmem
    rcases (mem_fillRank F hmax B).1 hBmem with hBmem | hBq
    · exact hBnot hBmem
    · exact (hkq (hBcard.symm.trans hBq)).elim

end Wallet

end WalletTheorem
