import Mathlib

/-!
# Finite wallet model

This file gives a literal finite model of the four possible states of each
key.  Probabilities are finite sums of products of real parameters, so later
proofs do not need measure-theoretic machinery.
-/

namespace WalletTheorem

/-- The four mutually exclusive states of one key. -/
inductive KeyState where
  | safe
  | stolen
  | leaked
  | lost
  deriving DecidableEq, Fintype

namespace KeyState

/-- Whether the owner holds a key in this state. -/
def ownerHas : KeyState → Bool
  | safe | leaked => true
  | stolen | lost => false

/-- Whether the attacker holds a key in this state. -/
def attackerHas : KeyState → Bool
  | stolen | leaked => true
  | safe | lost => false

/-- The coordinate transformation induced by wallet duality. -/
def dual : KeyState → KeyState
  | safe => safe
  | stolen => stolen
  | leaked => lost
  | lost => leaked

@[simp] theorem dual_dual (x : KeyState) : dual (dual x) = x := by
  cases x <;> rfl

@[simp] theorem ownerHas_dual (x : KeyState) :
    ownerHas (dual x) = !attackerHas x := by
  cases x <;> rfl

@[simp] theorem attackerHas_dual (x : KeyState) :
    attackerHas (dual x) = !ownerHas x := by
  cases x <;> rfl

end KeyState

/-- Admissible probabilities for the four states of one key. -/
structure Parameters where
  safe : ℝ
  stolen : ℝ
  leaked : ℝ
  lost : ℝ
  safe_nonneg : 0 ≤ safe
  stolen_nonneg : 0 ≤ stolen
  leaked_nonneg : 0 ≤ leaked
  lost_nonneg : 0 ≤ lost
  sum_eq_one : safe + stolen + leaked + lost = 1
  safe_gt_half : (1 : ℝ) / 2 < safe

namespace Parameters

/-- Probability mass of a single key state. -/
def mass (p : Parameters) : KeyState → ℝ
  | .safe => p.safe
  | .stolen => p.stolen
  | .leaked => p.leaked
  | .lost => p.lost

theorem mass_nonneg (p : Parameters) (x : KeyState) : 0 ≤ p.mass x := by
  cases x <;> simp only [mass]
  · exact p.safe_nonneg
  · exact p.stolen_nonneg
  · exact p.leaked_nonneg
  · exact p.lost_nonneg

theorem sum_mass (p : Parameters) : ∑ x : KeyState, p.mass x = 1 := by
  rw [show (Finset.univ : Finset KeyState) =
      {.safe, .stolen, .leaked, .lost} by native_decide]
  simp [mass]
  linarith [p.sum_eq_one]

/-- Slack in the majority-safe hypothesis, equal to `2*safe-1`. -/
def eta (p : Parameters) : ℝ :=
  p.safe - (p.stolen + p.leaked + p.lost)

theorem eta_eq (p : Parameters) : p.eta = 2 * p.safe - 1 := by
  dsimp [eta]
  linarith [p.sum_eq_one]

theorem eta_pos (p : Parameters) : 0 < p.eta := by
  rw [p.eta_eq]
  linarith [p.safe_gt_half]

theorem safe_eq_toggle_sum (p : Parameters) :
    p.safe = p.stolen + p.leaked + p.lost + p.eta := by
  simp [eta]

/-- Duality exchanges the leaked and lost probabilities. -/
def dual (p : Parameters) : Parameters where
  safe := p.safe
  stolen := p.stolen
  leaked := p.lost
  lost := p.leaked
  safe_nonneg := p.safe_nonneg
  stolen_nonneg := p.stolen_nonneg
  leaked_nonneg := p.lost_nonneg
  lost_nonneg := p.leaked_nonneg
  sum_eq_one := by linarith [p.sum_eq_one]
  safe_gt_half := p.safe_gt_half

@[simp] theorem dual_dual (p : Parameters) : p.dual.dual = p := by
  cases p
  rfl

@[simp] theorem dual_mass_dual (p : Parameters) (x : KeyState) :
    p.dual.mass x.dual = p.mass x := by
  cases x <;> rfl

end Parameters

/-- A complete state assignment for `n` keys. -/
abbrev Assignment (n : ℕ) := Fin n → KeyState

/-- The set of keys held by the owner. -/
def ownerSet {n : ℕ} (ω : Assignment n) : Finset (Fin n) :=
  Finset.univ.filter fun i => (ω i).ownerHas

/-- The set of keys held by the attacker. -/
def attackerSet {n : ℕ} (ω : Assignment n) : Finset (Fin n) :=
  Finset.univ.filter fun i => (ω i).attackerHas

/-- Product weight of an assignment under the independent-key model. -/
def assignmentWeight {n : ℕ} (p : Parameters) (ω : Assignment n) : ℝ :=
  ∏ i, p.mass (ω i)

theorem assignmentWeight_nonneg {n : ℕ} (p : Parameters) (ω : Assignment n) :
    0 ≤ assignmentWeight p ω :=
  Finset.prod_nonneg fun i _ => p.mass_nonneg (ω i)

/-- The product weights of all assignments sum to one. -/
theorem sum_assignmentWeight {n : ℕ} (p : Parameters) :
    ∑ ω : Assignment n, assignmentWeight p ω = 1 := by
  simp only [assignmentWeight]
  rw [← Fintype.prod_sum]
  simp [p.sum_mass]

/-- An upward-closed authorization family. -/
structure Wallet (n : ℕ) where
  authorized : Finset (Finset (Fin n))
  upward' : ∀ ⦃A B : Finset (Fin n)⦄, A ∈ authorized → A ⊆ B → B ∈ authorized

namespace Wallet

theorem upward {n : ℕ} (F : Wallet n) {A B : Finset (Fin n)}
    (hA : A ∈ F.authorized) (hAB : A ⊆ B) : B ∈ F.authorized :=
  F.upward' hA hAB

/-- The members of a wallet in rank `k`. -/
def layer {n : ℕ} (F : Wallet n) (k : ℕ) : Finset (Finset (Fin n)) :=
  F.authorized.filter fun A => A.card = k

/-- All `k`-subsets of the key set. -/
def fullLayer (n k : ℕ) : Finset (Finset (Fin n)) :=
  (Finset.univ : Finset (Fin n)).powersetCard k

/-- A rank is incomplete when the wallet contains some but not all sets in it. -/
def Incomplete {n : ℕ} (F : Wallet n) (k : ℕ) : Prop :=
  (∃ A : Finset (Fin n), A.card = k ∧ A ∈ F.authorized) ∧
    ∃ B : Finset (Fin n), B.card = k ∧ B ∉ F.authorized

/-- The finite set of incomplete ranks. -/
noncomputable def incompleteRanks {n : ℕ} (F : Wallet n) : Finset ℕ := by
  classical
  exact (Finset.range (n + 1)).filter F.Incomplete

end Wallet

/-- The successful assignments for a wallet. -/
def IsSuccess {n : ℕ} (F : Wallet n) (ω : Assignment n) : Prop :=
  ownerSet ω ∈ F.authorized ∧ attackerSet ω ∉ F.authorized

/-- Exact success probability, expressed as a finite sum. -/
noncomputable def successProbability {n : ℕ} (p : Parameters) (F : Wallet n) : ℝ :=
  by
    classical
    exact ∑ ω : Assignment n, if IsSuccess F ω then assignmentWeight p ω else 0

theorem successProbability_nonneg {n : ℕ} (p : Parameters) (F : Wallet n) :
    0 ≤ successProbability p F := by
  classical
  unfold successProbability
  exact Finset.sum_nonneg fun ω _ => by
    split_ifs
    · exact assignmentWeight_nonneg p ω
    · exact le_rfl

theorem successProbability_le_one {n : ℕ} (p : Parameters) (F : Wallet n) :
    successProbability p F ≤ 1 := by
  classical
  unfold successProbability
  calc
    (∑ ω : Assignment n,
        if IsSuccess F ω then assignmentWeight p ω else 0)
        ≤ ∑ ω : Assignment n, assignmentWeight p ω := by
          apply Finset.sum_le_sum
          intro ω _
          split_ifs
          · exact le_rfl
          · exact assignmentWeight_nonneg p ω
    _ = 1 := sum_assignmentWeight p

/-- The exact proposition stated as Theorem 1 in the paper. -/
def CanonicalizationStatement : Prop :=
  ∀ (n : ℕ) (p : Parameters) (F : Wallet n),
    ∃ Fstar : Wallet n,
      successProbability p F ≤ successProbability p Fstar ∧
        Fstar.incompleteRanks.card ≤ 1

end WalletTheorem
