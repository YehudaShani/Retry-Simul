import Mathlib

/-!
# Executable coefficient checks

The general kernel certificate is proved in the paper by expanding
`safe = stolen + leaked + lost + η` and injecting the negative toggle
assignments into positive ones.  This file implements those integer
coefficients literally and lets Lean's trusted kernel certify an exhaustive
check through eight keys.  It is supplementary evidence, not a replacement
for the still-to-be-formalized general injection.
-/

namespace WalletTheorem

/-- Count toggle assignments in blocks of sizes `a`, `b`, and `c`. -/
def toggleCount (a b c : ℕ) (accept : ℕ → ℕ → ℕ → Bool) : ℕ :=
  ∑ x ∈ Finset.range (a + 1),
    ∑ y ∈ Finset.range (b + 1),
      ∑ z ∈ Finset.range (c + 1),
        if accept x y z then a.choose x * b.choose y * c.choose z else 0

/-- Integer coefficient version of the rank kernel for one labelled partition. -/
def toggleKernel (n a b c k m : ℕ) : ℤ :=
  toggleCount a b c (fun x y z =>
      decide (x + y = k ∧ x + z ≤ n - m)) -
    toggleCount a b c (fun x y z =>
      decide (x + z = n - k ∧ x + y < m))

/-- The coefficient inequality corresponding to the boxed kernel certificate. -/
def toggleCertificateHolds (n a b c r q : ℕ) : Prop :=
  (n.choose r : ℤ) * toggleKernel n a b c q (r + 1) ≤
    (n.choose q : ℤ) * toggleKernel n a b c r (q + 1)

instance (n a b c r q : ℕ) : Decidable (toggleCertificateHolds n a b c r q) :=
  by
    unfold toggleCertificateHolds
    infer_instance

/--
Exact exhaustive verification of every labelled-partition coefficient through
eight keys and every rank pair in the low-sum range.
-/
theorem toggle_certificate_up_to_eight :
    ∀ a b c d r q : Fin 9,
      let n := a.val + b.val + c.val + d.val
      n ≤ 8 →
      1 ≤ r.val →
      r.val < q.val →
      q.val < n →
      r.val + q.val ≤ n →
      toggleCertificateHolds n a.val b.val c.val r.val q.val := by
  native_decide

end WalletTheorem
