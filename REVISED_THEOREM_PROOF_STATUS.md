# Revised incomplete-layer theorem: proof status

## 1. Model and proposed statement

For one key, write

\[
s=p_{\rm safe},\qquad t=p_{\rm theft},\qquad
e=p_{\rm leak},\qquad \ell=p_{\rm loss},
\qquad s+t+e+\ell=1.
\]

For an upward-closed wallet \(\mathcal F\subseteq 2^{[n]}\), let

\[
\Phi(\mathcal F)=\Pr(O\in\mathcal F,\ D\notin\mathcal F).
\]

The revised conjecture is:

> If
> \[
> s>t+e,\qquad s>t+\ell,
> \tag{C}
> \]
> then some optimal wallet either has at most one incomplete layer or
> is a one-key dictator
> \[
> \mathcal D_i=\{X:i\in X\}.
> \]

The word "some" is essential. For example, at degenerate parameter
points there can be many structurally different tied optimizers.

No complete proof of this conjecture is currently known. The results
below isolate the missing inequality, prove the theorem on several
substantial parameter regions, and show that a natural weakening of
(C) is false.

## 2. Regions where the conclusion is proved

### 2.1 The half-safe region

If

\[
s\geq \frac12,
\]

the existing batch-edit proof gives the stronger conclusion: from
every wallet one can reach a wallet of at least the same score having
at most one incomplete layer. No dictator exception is needed.

Thus only the region \(s<1/2\) is new in (C).

### 2.2 The no-theft face

If \(t=0\), a pure rank threshold is optimal, with no assumptions on
the relative sizes of \(s,e,\ell\).

Condition on the numbers \(J,S,L\) of leaked, safe, and lost keys, and
choose an independent uniform permutation \(\pi\) of \([n]\). If
\(P_k(\pi)\) is its first \(k\) elements, then

\[
D=P_J(\pi),\qquad O=P_{J+S}(\pi)
\]

has exactly the iid key-state distribution. In particular \(D\subseteq
O\).

For an up-family \(\mathcal F\), define its transition point on the
chain by

\[
\tau(\pi)=\min\{k:P_k(\pi)\in\mathcal F\}.
\]

Then

\[
O\in\mathcal F,\ D\notin\mathcal F
\quad\Longleftrightarrow\quad
J<\tau(\pi)\leq J+S.
\]

The counts are independent of \(\pi\), so, with \(I=J+S\),

\[
\Phi(\mathcal F)
=\mathbb E_\pi h_{\tau(\pi)},\qquad
h_k=\Pr(J<k\leq I).
\tag{1}
\]

Consequently,

\[
\Phi(\mathcal F)\leq\max_k h_k.
\]

Equality is attained by the pure threshold

\[
\mathcal T_k=\{X:|X|\geq k\}
\]

for any maximizing \(k\). Hence an optimal wallet with zero incomplete
layers exists.

There is also an exact batch-edit proof on this face. Since \(J\leq I\),

\[
h_k=\Pr(I\geq k)-\Pr(J\geq k),
\]

where \(I\sim{\rm Bin}(n,1-\ell)\) and
\(J\sim{\rm Bin}(n,e)\). Therefore

\[
h_{k+1}-h_k=\Pr(J=k)-\Pr(I=k).
\]

For \(s>0\), the likelihood ratio

\[
\frac{\Pr(J=k)}{\Pr(I=k)}
=
\left(\frac{1-e}{\ell}\right)^n
\left(\frac{e\ell}{(1-\ell)(1-e)}\right)^k
\]

is decreasing in \(k\). Thus \(h_k\) is unimodal. If \(r<q\) are the
extreme incomplete ranks, removing rank \(r\) has gain

\[
\Pr_\pi(\tau=r)\,[h_{r+1}-h_r],
\]

and filling rank \(q\) has gain

\[
\Pr_\pi(\tau=q+1)\,[h_q-h_{q+1}].
\]

Unimodality makes at least one of these two gains nonnegative.

### 2.3 An explicit small-theft neighborhood

The no-theft result persists quantitatively for fixed \(n\). Let
\(E_0\) be the event that no key is stolen, so
\(\Pr(E_0)=(1-t)^n\), and form the conditional \(t=0\) quantities
\(h_k\) from (1), using the normalized probabilities

\[
\bar s=\frac{s}{1-t},\qquad
\bar e=\frac{e}{1-t},\qquad
\bar\ell=\frac{\ell}{1-t}.
\]

Let

\[
h^\star=\max_k h_k,\qquad
\gamma=\min_{h_k<h^\star}(h^\star-h_k).
\]

Away from the all-safe corner, the maximizing ranks are one rank or
two adjacent ranks, and \(\gamma>0\). A wallet with at least two
incomplete layers has \(\tau(\pi)\) outside the maximizing ranks on at
least one of the \(n!\) chains. Hence a conditional-optimal threshold
\(\mathcal T_{k^\star}\) satisfies

\[
\Phi(\mathcal T_{k^\star})-\Phi(\mathcal F)
\geq
(1-t)^n\frac{\gamma}{n!}
-\bigl[1-(1-t)^n\bigr].
\]

Therefore the desired conclusion holds whenever

\[
\boxed{\quad
(1-t)^n\frac{\gamma}{n!}>1-(1-t)^n.
\quad}
\tag{2}
\]

This bound is conservative, but it is a rigorous open positive-\(t\)
extension around every fixed nondegenerate point of the \(t=0\) face.

### 2.4 An explicit neighborhood below \(s=1/2\)

There is also a rigorous dictator-optimal neighborhood on the other
side of the new region. Fix \(n\) and constants

\[
a,b>0,\qquad c,d\geq0,\qquad c+d=a+b,
\]

such that

\[
b>a+c,\qquad b>a+d.
\]

Put

\[
s=\frac12-a\varepsilon,\qquad
t=\frac12-b\varepsilon,\qquad
e=c\varepsilon,\qquad
\ell=d\varepsilon.
\tag{3}
\]

The two strict inequalities above are exactly what makes (C) hold
along this path. If

\[
0<\varepsilon<
\min\left\{
\frac1{2b},
\frac{2^{1-n}a}{4n^2(a+b)^2}
\right\},
\tag{4}
\]

then the only optimal nonconstant monotone wallets are the coordinate
dictators.

Here is the proof. Write \(X=O\), \(Z=D^c\), and
\(f^\ast(z)=1-f(z^c)\). Then

\[
\Phi_\varepsilon(f)=\mathbb E[f(X)f^\ast(Z)].
\]

At \(\varepsilon=0\), \(X=Z\) is uniform. A non-self-dual monotone
\(f\) misses at least one complementary pair and therefore has
\(\Phi_0(f)\leq1/2-2^{-n}\). The per-coordinate total-variation
distance from the base law is \((a+b)\varepsilon\), so

\[
\Phi_\varepsilon(f)
\leq \frac12-2^{-n}+n(a+b)\varepsilon<s
\]

under (4).

If \(f\) is self-dual, then \(f^\ast=f\), and expansion of the
one-coordinate law gives

\[
\Phi_\varepsilon(f)
=\frac12-a I(f)\varepsilon+R,
\]

where \(I(f)\) is total uniform influence and

\[
|R|\leq[2n(a+b)\varepsilon]^2.
\]

A monotone self-dual function is balanced. Edge isoperimetry gives
\(I(f)\geq1\), with equality only for a dictator; integrality of the
edge boundary strengthens every non-dictator to

\[
I(f)\geq1+2^{1-n}.
\]

Condition (4) makes the remainder smaller than the extra first-order
loss. Thus every non-dictator scores below \(s\), while every
coordinate dictator scores exactly \(s\).

For the concrete family

\[
(s,t,e,\ell)
=
\left(\frac12-\varepsilon,\frac12-4\varepsilon,
\frac52\varepsilon,\frac52\varepsilon\right),
\]

the pairwise slacks are \(\varepsilon/2\), and the simpler sufficient
bound

\[
\varepsilon<\frac{2^{1-n}}{100n^2}
\]

works.

### 2.5 The determinant-zero surface

The full conclusion is also proved whenever

\[
st=e\ell.
\]

Indeed, the one-coordinate joint law of \(O_i,D_i\) is

\[
\begin{pmatrix}
\ell&t\\
s&e
\end{pmatrix}.
\]

The determinant condition says exactly that \(O_i\) and \(D_i\) are
independent.  Put

\[
p=\Pr(O_i=1)=s+e,\qquad d=\Pr(D_i=1)=t+e.
\]

The pairwise hypotheses imply

\[
p>\frac12,\qquad d<\frac12.
\tag{4a}
\]

For an up-family \(\mathcal F\),

\[
\Phi(\mathcal F)=\mu_p(\mathcal F)
\bigl[1-\mu_d(\mathcal F)\bigr].
\tag{4b}
\]

Suppose that \(\mathcal F\) has lowest and highest incomplete ranks
\(r<q\).  Choose \(A\in\mathcal F_r\) and a missing
\(B\in\binom{[n]}q\setminus\mathcal F_q\), and put

\[
\mathcal F'=(\mathcal F\setminus\{A\})\cup\{B\}.
\]

This remains an up-family: every proper subset of \(A\) is rejected
because \(r\) is the lowest incomplete rank, and every proper
superset of \(B\) is accepted because \(q\) is the highest incomplete
rank.

If \(p<1\), the probability of an individual \(k\)-set under
\(\mu_p\) is \(p^k(1-p)^{n-k}\), which strictly increases with \(k\)
by (4a).  If \(d>0\), the probability under \(\mu_d\) strictly
decreases with \(k\).  Consequently, except at the all-safe point,

\[
\mu_p(\mathcal F')\geq\mu_p(\mathcal F),\qquad
\mu_d(\mathcal F')\leq\mu_d(\mathcal F),
\]

with at least one inequality strict.  (If \(p=1\), then \(d>0\)
unless all keys are safe; if \(d=0\), then \(p<1\) unless all keys
are safe.)

Equation (4b) gives

\[
\Phi(\mathcal F')>\Phi(\mathcal F).
\]

Thus no optimal wallet has two incomplete layers on \(st=e\ell\),
apart from the harmless all-safe degeneracy.  At the all-safe point
every nonconstant wallet ties with score one, and a pure threshold is
an optimal wallet with no incomplete layer.  Hence the existential
conclusion, with no dictator exception needed, holds on the entire
determinant-zero surface.

## 3. Exact reduction of the proposed proof

The weak version of (C) has the exact cone representation

\[
\begin{aligned}
s&=a+b+c+d+f,&t&=b,\\
e&=c+f,&\ell&=d+f,
\end{aligned}
\qquad a,b,c,d,f\geq0.
\]

Indeed, the two slacks are

\[
s-(t+e)=a+d,\qquad s-(t+\ell)=a+c.
\]

The first four rays, obtained by setting \(f=0\), are the colors
already handled coefficientwise by the \(s\geq1/2\) proof. The new
hard ray is

\[
(s,t,e,\ell)=(1,0,1,1)
\]

before normalization: a coordinate can be safe, leaked, or lost.
The \(t=0\) proof handles a product consisting entirely of such
nested-coordinate colors, but a mixture of this ray with the
safe/stolen ray is the unresolved case.

Let \(r<q\) be the lowest and highest incomplete ranks of
\(\mathcal F\), and put

\[
A=\mathcal F_r,\qquad
B=\binom{[n]}q\setminus\mathcal F_q,\qquad
H=\mathcal F\setminus A,\qquad
C=\mathcal F^c\setminus B.
\]

For families \(P,Q\), write

\[
W(P,Q)=\Pr(O\in P,D\in Q).
\]

Set

\[
\begin{array}{llll}
x=W(A,B),&y=W(B,A),&p=W(A,C),&z=W(B,C),\\
h=W(H,A),&k=W(H,B),&K_0=W(H,C).
\end{array}
\]

The original, remove, fill, and joint-edit scores are exactly

\[
\begin{aligned}
\Phi(\mathcal F)&=K_0+k+x+p,\\
\Phi(\mathcal F_R)&=K_0+h+k,\\
\Phi(\mathcal F_Q)&=K_0+p+z,\\
\Phi(\mathcal F_{RQ})&=K_0+h+y+z.
\end{aligned}
\tag{5}
\]

For \(t>0\), fixed ranks give

\[
y=\left(\frac{s}{t}\right)^{q-r}x.
\tag{6}
\]

Thus all three edits strictly lose exactly when

\[
\begin{aligned}
x+p&>h,\\
x+k&>z,\\
p+k&>h+z+
\left[\left(\frac{s}{t}\right)^{q-r}-1\right]x.
\end{aligned}
\tag{7}
\]

Every coordinate dictator has score \(s\), and

\[
s=\frac1n\sum_{X,Y}|X\setminus Y|\,w(X,Y),
\tag{8}
\]

where

\[
w(X,Y)=
s^{|X\setminus Y|}
t^{|Y\setminus X|}
e^{|X\cap Y|}
\ell^{n-|X\cup Y|}.
\]

Equation (8) is simply the expected number of safe keys divided by
\(n\).

Consequently, the natural four-way batch proof reduces to the
following single weighted isoperimetric claim:

> For the four-block partition induced by the extreme incomplete
> layers of an up-family, (7) implies
> \[
> K_0+k+x+p\leq
> \frac1n\sum_{X,Y}|X\setminus Y|w(X,Y)=s.
> \tag{9}
> \]

If (9) holds under (C), then either a batch edit is non-worsening or a
dictator is at least as good. Iteration proves the revised theorem.

Abstract nonnegative variables satisfying (7) do not imply (9).
Any proof must use both the up-family structure and the product form
of \(w\).

The simpler statement that one of the three edits always works is
false even under (C). For example, at

\[
(s,t,e,\ell)=\frac{(39,35,3,3)}{80},
\]

the five-key wallet with minimal terms

\[
[3,5,9,17,30]
\]

in bit-mask notation is a non-dictator with incomplete ranks \(2,3\),
and all three edits strictly lower its score. The dictator has the
higher score, so this example is consistent with (9).

## 4. Why the obvious looser condition is false

Adding the two inequalities in (C) suggests the weaker symmetric
condition

\[
s>t+\frac{e+\ell}{2}
\quad\Longleftrightarrow\quad
3s>1+t.
\tag{10}
\]

This is not sufficient, even with a dictator exception.

Take

\[
(s,t,e,\ell)=\frac{(4435,3025,1,2539)}{10000}.
\]

Then

\[
\frac{s-t}{e+\ell}
=\frac{141}{254}>\frac12,
\]

so (10) holds strictly. On six keys, the globally winning isomorphism
class has minimal terms

\[
[3,5,6,25,26,28,41,42,44,49,50,52].
\tag{11}
\]

Equivalently, split the keys into
\(U=\{1,2,3\}\) and \(V=\{4,5,6\}\). Its minimal terms are

\[
\binom U2
\ \cup\
\{\{u\}\cup Q:u\in U,\ Q\in\binom V2\}.
\]

It has two incomplete ranks, \(2\) and \(3\), and is not a dictator.
Its exact score numerator, over denominator \(10000^6\), is

\[
497132051797720624387840.
\]

The best dictator-or-at-most-one-incomplete-layer wallet has numerator

\[
497130865741076380750075.
\]

The forbidden wallet therefore wins by the exact positive gap

\[
\frac{1186056644243637765}{10000^6}.
\tag{12}
\]

Thus replacing the maximum in (C) by the average of \(e\) and
\(\ell\) loses too much information about the leak/loss asymmetry.

### Empirical coefficient candidates

The exact data suggest that the original coefficient \(1\) in

\[
s-t>\max(e,\ell)
\]

may not be sharp. The smallest tidy candidate surviving a complete
denominator-\(60\), \(n\leq6\) scan for the **global revised theorem**
was

\[
s-t>\frac9{16}\max(e,\ell).
\tag{13}
\]

This is a computational conjecture, not a theorem. The stronger local
edit-or-dictator implication appears to need more room: coefficient
\(9/16\) already has an exact four-way failure at

\[
(s,t,e,\ell)=\frac{(25,18,5,12)}{60},
\]

whereas

\[
s-t>\frac35\max(e,\ell)
\tag{14}
\]

survived the corresponding exact scans.

There is very little numerical room below (13). A global six-key
failure occurs at

\[
(s,t,e,\ell)=\frac{(4440,3023,0,2537)}{10000},
\]

for which

\[
\frac{s-t}{\max(e,\ell)}
=\frac{1417}{2537}\approx0.558534.
\]

A numerical phase-boundary calculation for that architecture gives
approximately \(0.5611412\), while \(9/16=0.5625\). The phase-boundary
number is only an estimate.

## 5. Computational evidence for the original pairwise conditions

The revised conjecture under (C) was checked exactly on all
permutation classes of nonconstant wallets through \(n=6\). For
\(n=6\), this is \(16{,}351\) classes. Common-denominator grids
\(20,40,60,80\) produced no counterexample; the denominator-\(80\)
scan checked all \(15{,}302\) admissible strict parameter points.

For larger \(n\), exact searches covered every two-block-symmetric
monotone family through \(n=12\) on the denominator-\(20\) grid and
through \(n=11\) on denominator \(40\). A further \(410{,}000\)
rational structured/random trials through \(n=13\) included weighted
thresholds, block rules, and full-support nested near-dictators. None
both beat the dictator and lost all three boundary edits. This is
evidence, not a proof.

The exact search implementation and a reproducible evaluation of
(11)--(12) are in `output/revised_bound_search.cs`. From the repository
root:

```powershell
Add-Type -Path output\revised_bound_search.cs
[RevisedBoundSearch]::Main(
  @('6','10000','point','4435','3025','1','2539')
)
```

## 6. Current conclusion

The strongest justified picture is:

1. \(s\geq1/2\): proved, with no dictator exception.
2. \(t=0\): proved, and a pure threshold is optimal.
3. Fixed \(n\), sufficiently small \(t>0\): proved by (2).
4. Fixed \(n\), sufficiently close to \(s=t=1/2\) from inside (C):
   proved, and dictators are the only optimizers.
5. The determinant-zero surface \(st=e\ell\): proved, with no dictator
   exception needed.
6. The full pairwise region (C): strongly supported, but the weighted
   isoperimetric implication (7) \(\Rightarrow\) (9) remains open.
7. The simpler averaged weakening (10): false by the exact six-key
   counterexample above.
8. Coefficients \(9/16\) for the global theorem and \(3/5\) for the
   local lemma are plausible empirical targets only.

## 7. Further reduction of the full interior problem

A second proof attempt narrows the unresolved part to two lemmas.

### 7.1 Off-center rank lemma

Let

\[
g_k(m)=\Pr(I\geq m,J=k)-\Pr(I=k,J<m).
\]

For extreme incomplete ranks \(r<q\) with \(r+q<n\), the only hard
sign regime is

\[
g_r(q+1)<0<g_q(r).
\]

It would suffice to prove

\[
\boxed{\quad g_r(q)\geq g_q(r).\quad}
\tag{15}
\]

The common-jump identity would then give

\[
g_q(r+1)\leq g_r(q+1)<0,
\]

and the existing two-density argument would make one of the two joint
batch-edit bounds nonnegative. Duality would handle \(r+q>n\).

There is an exact one-dimensional formulation of (15). Put

\[
h=n-r-q,\qquad K=n-J,\qquad M=\min(I,K-h).
\]

Then

\[
g_r(q)-g_q(r)=\Pr(M=q)-\Pr(M=r).
\tag{16}
\]

Conditioned on \(I=k\), write

\[
p=s+e,\qquad a=\frac e{s+e},\qquad
b=\frac t{t+\ell},\qquad \lambda=\frac st.
\]

Then

\[
J_k\sim{\rm Bin}(k,a)+{\rm Bin}(n-k,b),
\]

and, for \(U_k=k+J_k\) and \(N=n-h\),

\[
\frac{g_k(N-k+1)}{\Pr(I=k)}
=
\mathbb E\!\left[
\lambda^{U_k-2k}\mathbf1_{\{U_k>N\}}
-\mathbf1_{\{U_k\leq N\}}
\right].
\tag{17}
\]

The coupling

\[
U_{k+1}=U_k+1+A-B,
\qquad A\sim{\rm Bernoulli}(a),\quad
B\sim{\rm Bernoulli}(b),
\]

turns (15) into a sharp single-crossing inequality for two
Poisson-binomial tails. This inequality remains unproved.

### 7.2 Centered isoperimetric lemma

When \(r+q=n\), the remaining target is:

> If all three exact extreme-layer edits decrease the score, then
> \(\Phi(\mathcal F)\leq s\).

Writing

\[
X=O,\qquad Y=[n]\setminus D,\qquad
\mathcal F^\dagger=\{B:B^c\notin\mathcal F\},
\]

gives the exact reformulation

\[
\Phi(\mathcal F)
=\Pr(X\in\mathcal F,Y\in\mathcal F^\dagger).
\]

The two increasing families \(\mathcal F,\mathcal F^\dagger\) are
cross-intersecting, and the one-coordinate law is

\[
\begin{pmatrix}
t&\ell\\
e&s
\end{pmatrix}.
\]

Thus the centered target is a correlated weighted
cross-intersection inequality. A common star is precisely a
dictator, while rank separation corresponds to concentrating all
nontrivial geometry in one complementary layer pair.

A uniform shifting proof cannot work because the determinant

\[
st-e\ell
\]

can have either sign under (C). For example,

\[
(s,t,e,\ell)
=\left(\frac25,\frac1{20},\frac{11}{40},\frac{11}{40}\right)
\]

satisfies (C), but \(st-e\ell=-89/1600\). On four keys, compressing
the wallet with minimal generators

\[
\{1,2\},\quad\{1,3\},\quad\{2,4\}
\]

in the \((1,2)\) direction changes its exact score from

\[
\frac{21429}{40000}
\quad\text{to}\quad
\frac{1067}{2000},
\]

a decrease of \(89/40000\). This wallet already has only one
incomplete layer, so it is not a theorem counterexample; it is an
exact obstruction to sign-independent compression.

Consequently, a complete proof must establish both (15) and the
centered correlated cross-intersection lemma, with separate treatment
of the \(st\geq e\ell\) and \(st<e\ell\) regimes.

### 7.3 A sharper determinant split

The determinant division appears to be stronger than the last
paragraph suggests.

For the off-center problem, extensive exact and random checks found
that the hard sign pattern

\[
g_r(q+1)<0<g_q(r),\qquad r+q<n,
\tag{18}
\]

was initially observed only when

\[
st\geq e\ell.
\tag{19}
\]

Equality really can occur.  For example,

\[
(s,t,e,\ell)=\frac{(234,50,65,180)}{529}
\]

satisfies the pairwise hypotheses and \(st=e\ell\).  At
\(n=4,r=1,q=2\),

\[
g_1(3)=-\frac{469553760}{529^4}<0,\qquad
g_2(1)=\frac{2469706200}{529^4}>0.
\]

The desired comparison nevertheless holds:

\[
g_1(2)-g_2(1)=\frac{11415236040}{529^4}>0.
\]

Section 2.5 handles the entire determinant-zero surface by a direct
independence argument.  It is important that this does **not** extend
by merely excluding (18) in the strict reverse-TP2 region.  The exact
perturbation

\[
(s,t,e,\ell)=\frac{(233,50,66,180)}{529}
\]

has strict pairwise slacks \(117/529\) and \(3/529\), and

\[
st-e\ell=-\frac{230}{529^2}<0.
\]

Nevertheless, at \(n=4,r=1,q=2\),

\[
g_1(3)=-\frac{437099792}{529^4}<0,
\qquad
g_2(1)=\frac{2731277184}{529^4}>0.
\]

The desired comparison still holds strictly,

\[
g_1(2)-g_2(1)=\frac{11215041424}{529^4}>0,
\]

so the comparison itself, rather than exclusion of its hard sign
regime, is the necessary off-center lemma on both determinant sides.

For centered ranks \(r+q=n\), exact enumeration through \(n=6\) on
all strict pairwise denominator-\(80\) points, together with random
self-dual searches through \(n=8\), found the following sharper
pattern:

> If \(st\leq e\ell\), the remove and fill gains are never both
> negative.

The joint edit need not improve in this region.  For example, on five
keys at

\[
(s,t,e,\ell)=\frac{(9,0,3,8)}{20},
\]

the wallet with minimal terms

\[
[3,5,6,9,10]
\]

has centered incomplete ranks \(2,3\) and exact gains

\[
\frac{(-147555,\ 102789,\ -44766)}{20^5}.
\]

Thus the plausible reverse-TP2 statement is specifically a
two-single-edit lemma, not a joint-edit lemma.

The reverse-TP2 hypothesis has a useful conditional-binomial form.
For \(K=n-J\),

\[
K\mid I=k
\ \stackrel d=\ 
{\rm Bin}\!\left(k,\frac{s}{s+e}\right)
+
{\rm Bin}\!\left(n-k,\frac{\ell}{t+\ell}\right).
\tag{20}
\]

The inequality \(st\leq e\ell\) is exactly

\[
\frac{s}{s+e}\leq\frac{\ell}{t+\ell}.
\tag{21}
\]

Hence increasing \(k\) replaces a Bernoulli summand by a
stochastically smaller one.  The analogous statement holds after
interchanging \(I\) and \(K\).  This gives the required
reverse-likelihood-ratio direction, but the final comparison between
the two opposite rank-boundary tails is still missing.

### 7.4 Symmetric centered slice and noise stability

On the symmetric slice \(e=\ell=a\), put

\[
p=s+a,\qquad
\rho=\frac{st-a^2}{p(1-p)}.
\]

For a monotone self-dual wallet \(f\), the transformed sets
\(X=O\) and \(Y=[n]\setminus D\) have common
\({\rm Bernoulli}(p)\) marginal, and

\[
\Phi(f)
=\Pr(f(X)=1,f(Y)=1)
=\mu_p(f)^2+
\sum_{\varnothing\ne S\subseteq[n]}
\rho^{|S|}\widehat f_p(S)^2.
\tag{22}
\]

The pairwise hypotheses become

\[
a<2p-1.
\tag{23}
\]

Self-duality chooses exactly one member of each complementary pair
\(\{A,A^c\}\).  Since \(p>1/2\), this proves that the biased marginal
\(\mu_p(f)\) is maximized by the Hamming-rank majority wallet.
On the other hand, concentrating Fourier weight at degree one favors
a dictator, whose score is exactly \(s\).  The missing TP2 centered
lemma is therefore an exact interpolation statement between these
two extremizers.

Systematic searches of one-heavy weighted majorities through 39 keys,
random self-dual weighted thresholds through 13 keys, and recursive
majorities found no intermediate function beating both endpoints.
This remains evidence rather than a proof: the elementary spectral
bound

\[
\Phi(f)\leq
\rho\,\mu_p(f)+(1-\rho)\mu_p(f)^2
\tag{24}
\]

discards too much information about the degree distribution to
establish the required interpolation.

### 7.5 A proved TP2 compression lemma

The centered TP2 problem can be reduced rigorously to shifted
families.  Let \(C_{ij}\) be the usual \(ij\)-compression, replacing
\(j\) by \(i\) when \(i<j\), the replacement is absent, and the
original set is present.  Then

\[
\boxed{\quad
st\geq e\ell
\quad\Longrightarrow\quad
\Phi(C_{ij}\mathcal F)\geq\Phi(\mathcal F).
\quad}
\tag{25}
\]

Here is the local proof.  Put \(X=O\), \(Y=D^c\), and
\(g=1_{\mathcal F^\dagger}\).  After fixing all coordinates other
than \(i,j\), a monotone two-bit fiber of either \(1_{\mathcal F}\)
or \(g\) is one of

\[
0,\quad 1,\quad x_i\wedge x_j,\quad x_i\vee x_j,\quad x_i,\quad x_j.
\]

Compression changes only a fiber of type \(x_j\) into one of type
\(x_i\), and

\[
(C_{ij}\mathcal F)^\dagger=C_{ij}(\mathcal F^\dagger).
\]

In the local bilinear form

\[
\mathbb E[a(X_i,X_j)b(Y_i,Y_j)],
\]

all changed terms cancel by coordinate symmetry except pairs of
opposing \(x_i,x_j\) fibers.  Each such pair contributes

\[
\mathbb E[X_iY_i]-\mathbb E[X_jY_i]
=s-(s+e)(s+\ell)
=st-e\ell.
\]

After multiplying by the nonnegative outside-coordinate weights and
summing the fibers, (25) follows.  Compression preserves every layer
size, hence also the extreme incomplete ranks.  In the self-dual
centered case it also preserves self-duality.  Therefore the
self-dual portion of the remaining TP2 centered lemma need only be
proved for shifted maximal intersecting families.  A general centered
wallet instead gives a shifted cross-intersecting pair
\((\mathcal F,\mathcal F^\dagger)\); reducing that pair to the
self-dual case is itself still unproved.

There is a complete classification at the first centered boundary:
if the extreme incomplete ranks are

\[
r=1,\qquad q=n-1,
\]

then \(\mathcal F\) is a dictator.  Indeed, if \(\{i\}\in\mathcal F\),
any missing \((n-1)\)-set cannot contain \(i\), so it must be the
unique set \([n]\setminus\{i\}\).  Upward and downward closure then
show that precisely the sets containing \(i\) are accepted.  Its
score is \(s\).

For \(r\geq2\), shifted intersecting families satisfy the standard
prefix-walk constraint: each accepted set has some \(k\) for which

\[
|A\cap[2k+1]|\geq k+1.
\]

Turning this constraint into the required weighted optimal-stopping
inequality is the remaining TP2 step.

The next centered boundary also splits cleanly.  For a shifted
self-dual family with \(r=2\), the accepted two-sets form an
intersecting graph.  If they are not contained in a star, shifting
forces exactly the triangle

\[
\{12,13,23\}.
\]

Intersectingness permits no additional edge.  Upward closure and
self-duality then give exactly the lifted two-out-of-three majority
wallet

\[
\mathcal F=\{A:|A\cap\{1,2,3\}|\geq2\},
\]

whose score is

\[
\Phi(\mathcal F)
=s^3+3s^2(t+e+\ell)+6se\ell
=3s^2-2s^3+6se\ell.
\tag{26}
\]

This wallet is canonical on its three-key support.  In the remaining
star branch, if the accepted edges are

\[
\{\{1,i\}:i\in L\},
\]

then the sections \(G\subseteq H\) at coordinate \(1\) have the exact
form

\[
G=\operatorname{AND}_L\wedge A,\qquad
H=\operatorname{OR}_L\vee A^\dagger
\tag{27}
\]

for a smaller monotone core \(A\) on the other coordinates.  Thus the
whole star branch consists of generalized near-dictators.  The score
inequality needed to close this recursion remains unproved.

### 7.6 The proposed reverse-TP2 oriented edit is false

The tempting claim that \(\ell\geq e\) forces the fill edit to be
non-worsening in the centered reverse-TP2 region is false.  Take

\[
(s,t,e,\ell)=\frac{(77,28,47,48)}{200}
\]

and, on five keys, let \(T=\{3,4,5\}\) and

\[
\mathcal F
=\{Z:|Z|\geq2\ \text{and}\ Z\cap\{1,2\}\ne\varnothing\}.
\]

Its incomplete ranks are \(r=2,q=3\).  The hypotheses hold strictly,

\[
s>t+e,\qquad s>t+\ell,\qquad st<e\ell,
\qquad \ell>e.
\]

With denominator \(200^5\), the original and fill scores have
numerators

\[
133718319350,\qquad 133641605867.
\]

Thus filling has exact negative gain

\[
-\frac{76713483}{200^5},
\]

even though removing improves the score by
\(28550131995/200^5\).  The proposed binomial inequality
(31) was therefore only a sufficient shortcut, and it too is false.
The reverse-TP2 centered proof must retain the interaction among all
three edits rather than orienting one edit solely by the sign of
\(\ell-e\).

### 7.7 Fixed-marginal interpolation and its exact obstruction

There is a useful parametrization which turns the determinant into a
single correlation coordinate.  Fix

\[
b=t+e=\Pr(D_i=1),\qquad d=t+\ell=\Pr(O_i=0).
\]

Then

\[
(s,t,e,\ell)=(1-b-d+t,\ t,\ b-t,\ d-t)
\]

and the determinant collapses to

\[
st-e\ell=t-bd.
\tag{32}
\]

For every monotone wallet \(f\), differentiation at fixed \(b,d\)
gives the exact Russo formula

\[
\frac{d}{dt}\Phi_t(f)
=\sum_{i=1}^n
\mathbb E_t\!\left[
\partial_i f(O_{-i})\partial_i f(D_{-i})
\right]\geq0.
\tag{33}
\]

For the off-center kernel, let \(K=n-J\), let
\(\mu_n(i,k;t)=\Pr(I=i,K=k)\), and retain
\(h=n-r-q\).  The probability generating polynomial is

\[
\bigl[t+(b-t)x+(d-t)y+(1-b-d+t)xy\bigr]^n.
\]

If

\[
T_k(t)=\Pr(I\geq k,K\geq k+h),
\qquad m_k(t)=\Pr(\min(I,K-h)=k),
\]

then coefficient differentiation gives

\[
T_k'(t)=n\mu_{n-1}(k-1,k+h-1;t)
\]

and therefore

\[
m_k'(t)=n\bigl[
\mu_{n-1}(k-1,k+h-1;t)
-\mu_{n-1}(k,k+h;t)
\bigr].
\tag{34}
\]

Put \(D_n=m_q-m_r\), \(\delta=q-r\),
\(\lambda=s/t\), and

\[
C_k=\mu_{n-1}(k,k+h;t).
\]

Skew reflection of the joint count array reduces the four terms in
(34) to the exact adjacent-ratio formula

\[
D_n'(t)
=n\left[(1+\lambda^{\delta-1})C_r
-(1+\lambda^{\delta+1})C_{r-1}\right].
\tag{35}
\]

There is a further PF-infinity representation.  With
\(z=e\ell/(st)\), \(N=n-1\), and
\(L=N-h=r+q-1\),

\[
C_k=N!\ell^h s^k t^{L-k}H_k(z),
\]

where

\[
H_k(z)=\sum_a
\frac{z^a}{(k-a)!(L-k-a)!a!(a+h)!}.
\tag{36}
\]

The ratio \(H_r/H_{r-1}\) is increasing in \(z\).  Indeed, the
ratio of corresponding coefficients is

\[
\frac{q-a}{r-a},
\]

which is increasing in \(a\); differentiating the ratio of the two
generating polynomials is then a positive covariance.  Formulae
(35)--(36) reduce the desired interpolation step to one adjacent
coefficient ratio.

Global convexity or unimodality in \(t\) is nevertheless false.  For
the exact fixed marginals

\[
b=\frac{34}{100},\qquad d=\frac{33}{100},qquad
n=7, r=2, q=4, h=1,
\]

the whole interval \(1/100<t<17/100\) lies in the strict pairwise
region below \(s=1/2\).  Yet (35) is positive at \(t=11/1000\),
negative at \(t=40/1000\), and positive again at \(t=80/1000\).
Thus interpolation must use the two hard boundary-tail signs, not
only the sign of \(D_n'\) on the full parameter interval.

### 7.8 Reverse-TP2 two-terminal cut reduction

In the centered reverse-TP2 case, a sharp sufficient statement can
be localized at each pair \(a\in A,b\in B\).  Define

\[
\begin{aligned}
H_a&=\sum_{o\in H}w(o,a),&
R_a&=\sum_{d\in\mathcal F^c}w(a,d),\\
Z_b&=\sum_{d\in C}w(b,d),&
U_b&=\sum_{o\in\mathcal F}w(o,b).
\end{aligned}
\]

It would suffice to prove

\[
\boxed{\quad H_aZ_b\geq R_aU_b\quad}
\tag{37}
\]

for every such pair.  Summing (37) over \(a,b\) gives

\[
hz\geq(x+p)(x+k),
\]

which immediately prevents the remove and fill edits from both
losing.

The likelihood ratios in (37) have a particularly simple form.  Put

\[
P=a\setminus b,\qquad Q=b\setminus a,\qquad
\theta=\frac{e\ell}{st}\geq1,qquad \delta=q-r.
\]

Then, for every \(X\subseteq[n]\),

\[
\frac{w(X,a)}{w(X,b)}
=\left(\frac\ell t\right)^\delta
\theta^{|X\cap P|-|X\cap Q|},
\]

\[
\frac{w(b,X)}{w(a,X)}
=\left(\frac s\ell\right)^\delta
\theta^{|X\cap Q|-|X\cap P|},
\tag{38}
\]

and the product of the two ratios is the constant
\((s/t)^\delta>1\).  Thus (37) is a precise two-terminal weighted-cut
inequality on the Boolean lattice.  The pointwise uncrossing

\[
w(a\cup b\cup o,a)\,
w(b,a\cap b\cap d)
\geq w(a,d)w(o,b)
\tag{39}
\]

holds for every \(o\in\mathcal F,d\notin\mathcal F\); its two images
belong to \(H\) and \(C\).  The unresolved step is a fractional
transport controlling the many-to-one multiplicity in (39).

### 7.9 Terminal TP2 near-dictator reduction

The terminal constant-core member of the shifted star recursion (27)
can be reduced to a one-variable polynomial statement.  On one
distinguished key and \(m\) leaves, let \(F_{m,j}\) accept

\[
x_1=0: |x_L|\geq m-j,
\qquad
x_1=1: |x_L|\geq j+1.
\]

Thus \(F_{m,-1}\) is the dictator and \(F_{m,0}\) is the terminal
near-dictator.  Write

\[
D_m=\Phi(F_{m,0})-s,
\qquad J_m=\Phi(F_{m,1})-\Phi(F_{m,0}).
\]

The exact terminal claim needed by the recursion is

\[
D_m>0\quad\Longrightarrow\quad J_m\geq0.
\tag{40}
\]

Normalize homogeneously by putting

\[
s=1,\qquad T=t/s,\quad E=e/s,\quad L=\ell/s.
\]

The assumptions become

\[
T+E<1,qquad T+L<1,qquad T\geq EL.
\]

Direct expansion gives

\[
\begin{aligned}
D_m(L)={}&T+E\bigl[(1+L)^m-L^m\bigr]
+L\bigl[(1+E)^m-E^m\bigr]\\
&-(T+L)^m-(T+E)^m+T^m.
\end{aligned}
\tag{41}
\]

As an ordinary polynomial in \(L\), its coefficients are

\[
\begin{aligned}
d_0&=(T+E)-(T+E)^m,\\
d_1&=m(E-T^{m-1})+(1+E)^m-E^m,\\
d_k&=\binom mk(E-T^{m-k})\quad(2\leq k\leq m-1),\\
d_m&=-1.
\end{aligned}
\tag{42}
\]

The coefficient sequence has exactly one positive-to-negative sign
change.  Indeed, \(d_0>0\), the quantities
\(E-T^{m-k}\) decrease with \(k\), and if \(d_1<0\) then
\(E<T^{m-1}\), forcing every later interior coefficient to be
negative.  Descartes' rule therefore proves that (41) has a unique
positive root \(R_D\), and

\[
D_m(L)>0\quad\Longleftrightarrow\quad 0\leq L<R_D.
\tag{43}
\]

Exact searches suggest the stronger quantitative form

\[
J_m\geq T D_m\qquad\text{whenever }D_m>0.
\tag{44}
\]

It is essential to condition on \(D_m>0\).  For example, at

\[
(s,t,e,\ell)=\frac{(49,45,3,3)}{100},\qquad m=5,
\]

both \(D_m\) and \(J_m\) are negative and (44) fails.  In the
positive-gap region, (44) is reduced by (42)--(43) to ordering the
first positive roots of two explicit degree-\(m\) polynomials.  A
Bernstein-basis projective-order inequality for their coefficient
rows has survived extensive exact tests, but its determinant proof is
still missing.
