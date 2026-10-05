# The pairwise safe bound does not suffice

## Proposed hypothesis

Write the four one-key probabilities as

\[
s=p_{\mathrm{SAFE}},\qquad
t=p_{\mathrm{STOLEN}},\qquad
e=p_{\mathrm{LEAKED}},\qquad
\ell=p_{\mathrm{LOST}},
\]

with \(s+t+e+\ell=1\).  Consider the proposed replacement for
\(s>1/2\):

\[
s>t+e,\qquad s>t+\ell.
\tag{1}
\]

The canonicalization theorem is false under (1), already for three
keys.

## A counterexample family arbitrarily close to \(s=1/2\)

Let

\[
0<\varepsilon<\frac{2}{71}
\]

and set

\[
s=\frac12-\varepsilon,\qquad
t=\frac12-4\varepsilon,\qquad
e=\ell=\frac52\varepsilon.
\tag{2}
\]

These are nonnegative and sum to one.  Moreover,

\[
s-(t+e)=s-(t+\ell)=\frac{\varepsilon}{2}>0,
\]

so both inequalities in (1) hold strictly.  Nevertheless \(s<1/2\),
and \(s\) can be made arbitrarily close to \(1/2\).

On three keys, take the dictator wallet

\[
\mathcal D=\{X\subseteq[3]:1\in X\}.
\]

Its first layer contains only \(\{1\}\), and its second layer contains
only \(\{1,2\}\) and \(\{1,3\}\).  Thus both ranks 1 and 2 are
incomplete.  Its success probability is simply

\[
\Phi(\mathcal D)=s=\frac12-\varepsilon,
\tag{3}
\]

because success depends only on key 1 being safe.

## Exhausting all three-key wallets

Up to permutation of the keys, the nonconstant upward-closed families
on three keys have the following minimal generators.  Families paired
in one row have the same score here because \(e=\ell\).

\[
\begin{array}{c|c}
\text{minimal generators}&\text{success probability}\\
\hline
\{1\}&D=\frac12-\varepsilon\\[2mm]
\{1\},\{2\}\quad\text{or}\quad\{1,2\}
  &P=\frac14+\frac32\varepsilon-4\varepsilon^2\\[2mm]
\{1\},\{2\},\{3\}\quad\text{or}\quad\{1,2,3\}
  &E=\frac18+\frac98\varepsilon+\frac{27}{8}\varepsilon^2
      -\frac{49}{4}\varepsilon^3\\[2mm]
\{1\},\{2,3\}\quad\text{or}\quad\{1,2\},\{1,3\}
  &M=\frac38+\frac58\varepsilon+\frac98\varepsilon^2
      -\frac{31}{4}\varepsilon^3\\[2mm]
\{1,2\},\{1,3\},\{2,3\}
  &Q=\frac12-\frac32\varepsilon+\frac{75}{4}\varepsilon^2
      -\frac{71}{2}\varepsilon^3.
\end{array}
\]

The two constant families have success probability zero.  The exact
gaps from the dictator are

\[
\begin{aligned}
D-P&=4\left(\frac18-\varepsilon\right)
       \left(\frac12-\varepsilon\right),\\
D-E&=\frac18(1-2\varepsilon)
       (3-11\varepsilon-49\varepsilon^2),\\
D-M&=\frac18(1-2\varepsilon)
       (1-11\varepsilon-31\varepsilon^2),\\
D-Q&=\varepsilon
       \left(\frac12-\varepsilon\right)(2-71\varepsilon).
\end{aligned}
\tag{4}
\]

Every expression in (4) is strictly positive for
\(0<\varepsilon<2/71\).  Hence the dictator is the unique optimal
isomorphism class (with three labeled choices), and every optimal
wallet has two incomplete layers.

The majority wallet \(Q\) is the best wallet having at most one
incomplete layer.  For completeness,

\[
\begin{aligned}
Q-P&=\frac14(1-2\varepsilon)
       (1-10\varepsilon+71\varepsilon^2),\\
Q-E&=\frac18(1-2\varepsilon)
       (3-15\varepsilon+93\varepsilon^2),\\
Q-M&=\frac18(1-2\varepsilon)
       (1-15\varepsilon+111\varepsilon^2).
\end{aligned}
\]

The three quadratics are positive (their discriminants are negative),
so these differences are positive throughout the relevant interval.

## The three batch edits also fail

For the dictator, the lowest and highest incomplete ranks are
\(r=1\) and \(q=2\).  The three boundary edits are:

\[
\begin{array}{c|c}
\text{edit}&\text{minimal generators afterward}\\
\hline
\text{remove rank 1}&\{1,2\},\{1,3\}\\
\text{fill rank 2}&\{1\},\{2,3\}\\
\text{both}&\{1,2\},\{1,3\},\{2,3\}.
\end{array}
\]

Their scores are \(M,M,Q\), respectively.  By (4), all three edits
strictly decrease success probability.  Thus the obstruction is not
only a failure of the existing rank-kernel certificate: the batch
lemma itself is false under (1).

## Concrete rational instance

Taking \(\varepsilon=1/50\) gives

\[
(s,t,e,\ell)
=\left(\frac{12}{25},\frac{21}{50},\frac1{20},\frac1{20}\right).
\]

Both slacks in (1) equal \(1/100\).  The dictator has score

\[
\frac{12}{25}=0.48,
\]

whereas the best wallet with at most one incomplete layer is the
two-out-of-three majority wallet, with score

\[
\frac{14913}{31250}=0.477216.
\]

The exact optimality gap is

\[
\frac{87}{31250}=0.002784.
\]

Consequently, the boundary value \(1/2\) in the current sufficient
condition is sharp from below: no uniform hypothesis that admits
probabilities from (2) below \(1/2\) can imply that some optimal wallet
has at most one incomplete layer.

## Support-relative caveat

This counterexample uses a wallet that ignores keys 2 and 3.  Under
the theorem's current definition, incompleteness is measured in the
full Boolean lattice on all three available keys, so the dictator
really does have two incomplete ranks.

If instead every wallet were first restricted to the union of the
keys appearing in its minimal generators, the dictator would be a
one-key wallet with no incomplete rank.  Therefore this example does
not disprove a separately formulated **support-relative**
canonicalization theorem under (1).  Such a result would be different
from the theorem currently formalized and proved in this repository.
