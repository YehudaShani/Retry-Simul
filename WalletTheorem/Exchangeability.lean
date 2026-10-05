import WalletTheorem.Model

/-!
# Exchangeability of the finite product model

Relabeling the key coordinates does not change an assignment's product
weight.  Consequently, events carried to one another by a coordinate
permutation have exactly the same probability.  This is the probabilistic
symmetry needed to turn rank-level kernel estimates into batch-edit bounds.
-/

namespace WalletTheorem

/-- Relabel an assignment by a permutation of the key coordinates. -/
def permuteAssignment {n : ℕ} (σ : Equiv.Perm (Fin n))
    (ω : Assignment n) : Assignment n :=
  fun i => ω (σ.symm i)

@[simp] theorem permuteAssignment_apply {n : ℕ} (σ : Equiv.Perm (Fin n))
    (ω : Assignment n) (i : Fin n) :
    permuteAssignment σ ω i = ω (σ.symm i) := rfl

@[simp] theorem permuteAssignment_symm {n : ℕ} (σ : Equiv.Perm (Fin n))
    (ω : Assignment n) :
    permuteAssignment σ.symm (permuteAssignment σ ω) = ω := by
  funext i
  simp [permuteAssignment]

/-- Coordinate relabeling is an equivalence on complete assignments. -/
def permuteAssignmentEquiv {n : ℕ} (σ : Equiv.Perm (Fin n)) :
    Assignment n ≃ Assignment n where
  toFun := permuteAssignment σ
  invFun := permuteAssignment σ.symm
  left_inv := permuteAssignment_symm σ
  right_inv := permuteAssignment_symm σ.symm

@[simp] theorem ownerSet_permuteAssignment {n : ℕ}
    (σ : Equiv.Perm (Fin n)) (ω : Assignment n) :
    ownerSet (permuteAssignment σ ω) =
      (ownerSet ω).map σ.toEmbedding := by
  ext i
  simp [ownerSet, permuteAssignment]

@[simp] theorem attackerSet_permuteAssignment {n : ℕ}
    (σ : Equiv.Perm (Fin n)) (ω : Assignment n) :
    attackerSet (permuteAssignment σ ω) =
      (attackerSet ω).map σ.toEmbedding := by
  ext i
  simp [attackerSet, permuteAssignment]

@[simp] theorem ownerCard_permuteAssignment {n : ℕ}
    (σ : Equiv.Perm (Fin n)) (ω : Assignment n) :
    (ownerSet (permuteAssignment σ ω)).card = (ownerSet ω).card := by
  simp

@[simp] theorem attackerCard_permuteAssignment {n : ℕ}
    (σ : Equiv.Perm (Fin n)) (ω : Assignment n) :
    (attackerSet (permuteAssignment σ ω)).card = (attackerSet ω).card := by
  simp

/-- Product weights are invariant under coordinate relabeling. -/
@[simp] theorem assignmentWeight_permuteAssignment {n : ℕ}
    (p : Parameters) (σ : Equiv.Perm (Fin n)) (ω : Assignment n) :
    assignmentWeight p (permuteAssignment σ ω) = assignmentWeight p ω := by
  unfold assignmentWeight permuteAssignment
  exact σ.symm.prod_comp (fun i => p.mass (ω i))

/-- Exact finite mass of an event in the assignment space. -/
noncomputable def eventMass {n : ℕ} (p : Parameters)
    (E : Assignment n → Prop) : ℝ := by
  classical
  exact ∑ ω : Assignment n, if E ω then assignmentWeight p ω else 0

theorem eventMass_nonneg {n : ℕ} (p : Parameters)
    (E : Assignment n → Prop) :
    0 ≤ eventMass p E := by
  classical
  unfold eventMass
  exact Finset.sum_nonneg fun ω _ => by
    split_ifs
    · exact assignmentWeight_nonneg p ω
    · exact le_rfl

/--
Pulling an event back along a coordinate permutation preserves its exact
finite mass.
-/
theorem eventMass_permuteAssignment {n : ℕ} (p : Parameters)
    (σ : Equiv.Perm (Fin n)) (E : Assignment n → Prop) :
    eventMass p E = eventMass p (fun ω => E (permuteAssignment σ ω)) := by
  classical
  unfold eventMass
  apply Fintype.sum_equiv (permuteAssignmentEquiv σ.symm)
  intro ω
  change
    (if E ω then assignmentWeight p ω else 0) =
      if E (permuteAssignment σ (permuteAssignment σ.symm ω)) then
        assignmentWeight p (permuteAssignment σ.symm ω) else 0
  rw [assignmentWeight_permuteAssignment]
  rw [show permuteAssignment σ (permuteAssignment σ.symm ω) = ω by
    simpa using permuteAssignment_symm σ.symm ω]

/--
Any two equal-cardinality key sets are carried to one another by a coordinate
permutation.
-/
theorem exists_keyPermutation {n : ℕ} (A B : Finset (Fin n))
    (hcard : A.card = B.card) :
    ∃ σ : Equiv.Perm (Fin n), A.map σ.toEmbedding = B :=
  Equiv.Perm.exists_map_finset_eq A B hcard

/--
Mass of the fiber with a fixed attacker set and a prescribed owner rank.
-/
noncomputable def attackerFiberMass {n : ℕ} (p : Parameters)
    (A : Finset (Fin n)) (i : ℕ) : ℝ :=
  eventMass p fun ω => (ownerSet ω).card = i ∧ attackerSet ω = A

/--
Mass of the fiber with a fixed owner set and a prescribed attacker rank.
-/
noncomputable def ownerFiberMass {n : ℕ} (p : Parameters)
    (A : Finset (Fin n)) (j : ℕ) : ℝ :=
  eventMass p fun ω => ownerSet ω = A ∧ (attackerSet ω).card = j

theorem attackerFiberMass_nonneg {n : ℕ} (p : Parameters)
    (A : Finset (Fin n)) (i : ℕ) :
    0 ≤ attackerFiberMass p A i :=
  eventMass_nonneg p _

theorem ownerFiberMass_nonneg {n : ℕ} (p : Parameters)
    (A : Finset (Fin n)) (j : ℕ) :
    0 ≤ ownerFiberMass p A j :=
  eventMass_nonneg p _

/--
Exchangeability: the fixed-attacker-set fiber mass depends only on the
cardinality of that set.
-/
theorem attackerFiberMass_eq_of_card_eq {n : ℕ} (p : Parameters)
    (A B : Finset (Fin n)) (i : ℕ) (hcard : A.card = B.card) :
    attackerFiberMass p A i = attackerFiberMass p B i := by
  classical
  obtain ⟨σ, hσ⟩ := exists_keyPermutation B A hcard.symm
  rw [attackerFiberMass, attackerFiberMass,
    eventMass_permuteAssignment p σ]
  apply congr_arg (eventMass p)
  funext ω
  apply propext
  simp only [ownerCard_permuteAssignment, attackerSet_permuteAssignment]
  constructor
  · rintro ⟨hi, hA⟩
    refine ⟨hi, ?_⟩
    apply Finset.map_injective σ.toEmbedding
    simpa [hσ] using hA
  · rintro ⟨hi, hB⟩
    refine ⟨hi, ?_⟩
    simpa [hB] using hσ

/--
Exchangeability: the fixed-owner-set fiber mass depends only on the
cardinality of that set.
-/
theorem ownerFiberMass_eq_of_card_eq {n : ℕ} (p : Parameters)
    (A B : Finset (Fin n)) (j : ℕ) (hcard : A.card = B.card) :
    ownerFiberMass p A j = ownerFiberMass p B j := by
  classical
  obtain ⟨σ, hσ⟩ := exists_keyPermutation B A hcard.symm
  rw [ownerFiberMass, ownerFiberMass,
    eventMass_permuteAssignment p σ]
  apply congr_arg (eventMass p)
  funext ω
  apply propext
  simp only [ownerSet_permuteAssignment, attackerCard_permuteAssignment]
  constructor
  · rintro ⟨hA, hj⟩
    refine ⟨?_, hj⟩
    apply Finset.map_injective σ.toEmbedding
    simpa [hσ] using hA
  · rintro ⟨hB, hj⟩
    refine ⟨?_, hj⟩
    simpa [hB] using hσ

end WalletTheorem
