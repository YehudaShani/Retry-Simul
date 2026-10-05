# Canonical optimal wallets have at most one incomplete layer

> **Update.** This document proves the zero-leak case. A separate,
> stronger proof allowing arbitrary leaked-key probability is given in
> `PROOF_INCOMPLETE_LAYERS_WITH_LEAK.md`.

## 1. Model and the corrected objective

Let each of the \(n\) keys independently be

- safe with probability \(s\),
- stolen with probability \(t\), or
- lost with probability \(\lambda\),

where

\[
s+t+\lambda=1,\qquad s>\frac12,
\]

and the probability of a leaked key is zero.

Write \(U\) for the set of safe keys and \(V\) for the set of stolen
keys. Thus \(U\cap V=\varnothing\). A wallet is a nonempty upward-closed
family \(\mathcal F\subseteq 2^{[n]}\). Its success probability is

\[
\Phi(\mathcal F)=\Pr(U\in\mathcal F,\;V\notin\mathcal F).
\]

The \(k\)-th layer is
\(\mathcal F_k=\mathcal F\cap\binom{[n]}k\). It is incomplete when

\[
0<|\mathcal F_k|<\binom nk.
\]

The useful theorem is the following canonicalization statement.

> **Target theorem.** For every wallet \(\mathcal F\), there is a wallet
> \(\mathcal F^\star\) such that
> \[
> \Phi(\mathcal F^\star)\geq\Phi(\mathcal F)
> \]
> and \(\mathcal F^\star\) has at most one incomplete layer.

This implies that **some** optimal wallet has at most one incomplete
layer. It intentionally does not claim that every optimizer has that
form. That stronger assertion is false at \(s=1\): every nonempty proper
up-family then has success probability one, including up-families with
several incomplete layers.

The transformations below therefore need only be non-worsening; they do
not need to be strictly improving.

## 2. Shifting is non-worsening

Fix \(i<j\). For a set \(X\) with \(j\in X\) and \(i\notin X\), put

\[
\sigma(X)=X-\{j\}+\{i\}.
\]

The usual \(ij\)-compression \(C_{ij}\mathcal F\) replaces \(X\) by
\(\sigma(X)\) when \(X\in\mathcal F\) and
\(\sigma(X)\notin\mathcal F\).

Let

\[
\begin{aligned}
\mathcal L&=\{X\in\mathcal F:
 j\in X,\ i\notin X,\ \sigma(X)\notin\mathcal F\},\\
\mathcal I&=\{Y\in\mathcal F:
 i\in Y,\ j\notin Y,\ Y-\{i\}+\{j\}\notin\mathcal F\}.
\end{aligned}
\]

For ranks \(a,b\), let \(D_{ab}(\mathcal F)\) be the number of ordered
disjoint pairs in
\(\mathcal F_a\times\mathcal F_b\). Pairing all sets under the
transposition of \(i\) and \(j\) gives

\[
\begin{aligned}
D_{ab}(\mathcal F)-D_{ab}(C_{ij}\mathcal F)
={}&|\{(X,Y)\in\mathcal L_a\times\mathcal I_b:X\cap Y=\varnothing\}|\\
&+|\{(X,Y)\in\mathcal I_a\times\mathcal L_b:X\cap Y=\varnothing\}|.
\end{aligned}
\]

In particular, compression does not increase the number of disjoint
authorized pairs at any ordered pair of ranks.

The probability that the owner is authorized depends only on the number
of authorized sets in each layer, and compression preserves all layer
sizes. The failure term in which both owner and attacker are authorized
is a nonnegative weighted sum of the \(D_{ab}\)'s. More explicitly,

\[
\begin{aligned}
\Phi(C_{ij}\mathcal F)-\Phi(\mathcal F)
=\sum_{\substack{X\in\mathcal L,\;Y\in\mathcal I\\X\cap Y=\varnothing}}
\lambda^{n-|X|-|Y|}
\left(s^{|X|}t^{|Y|}+s^{|Y|}t^{|X|}\right)\geq0.
\end{aligned}
\]

Compression also preserves upward closure. Iterating all compressions
therefore produces a shifted wallet \(\mathcal G\) satisfying

\[
\Phi(\mathcal G)\geq\Phi(\mathcal F)
\]

and having exactly the same layer sizes as \(\mathcal F\).

Notice that this lemma does not require \(s>1/2\).

## 3. A single lexicographic boundary swap does not work

The proposed operation was:

1. let \(r\) and \(q\) be the lowest and highest incomplete layers;
2. remove the lexicographically largest member of \(\mathcal F_r\);
3. add the lexicographically smallest missing member of layer \(q\).

Even after shifting, this operation can make the wallet worse.

Take \(n=6\) and

\[
\mathcal F=\{S:|S|\geq4\}
\ \cup\
\{S:1\in S,\ |S|\geq2\}.
\]

This is shifted. Its minimal generators, encoded as binary masks, are

\[
3,5,9,17,33,30,46,54,58,60.
\]

Its lowest and highest incomplete layers are \(r=2\) and \(q=3\).
The prescribed swap removes \(\{1,6\}\) and adds \(\{2,3,4\}\).
At

\[
(s,t,\lambda)=(0.51,0.37,0.12)
\]

the change in success probability is

\[
-\frac{1225125621}{500000000000}
=-0.002450251242.
\]

Indeed, every one of the 50 possible one-set swaps between these two
boundary layers decreases the score. Weakening “strictly improves” to
“does not worsen” therefore does not rescue the single-swap lemma.

## 4. The batch replacement

In any up-family, the incomplete layers form a consecutive interval.
Let \(r<q\) be its lowest and highest elements, and put

\[
\mathcal A=\mathcal F_r,\qquad
\mathcal B=\binom{[n]}q\setminus\mathcal F_q,\qquad
\mathcal H=\mathcal F\setminus\mathcal A.
\]

Let \(\mathcal C\) contain all remaining unauthorized sets, so that

\[
2^{[n]}=\mathcal H\sqcup\mathcal A\sqcup\mathcal B\sqcup\mathcal C.
\]

Consider the three edits

\[
\begin{array}{c|c|c}
\text{edit}&\text{new wallet}&\text{incomplete layers removed}\\
\hline
\text{remove}&\mathcal H&r\\
\text{both}&\mathcal H\cup\mathcal B&r,q\\
\text{fill}&\mathcal H\cup\mathcal A\cup\mathcal B&q.
\end{array}
\]

All three are up-families. If the original wallet is shifted, so are all
three edits.

Thus the target theorem follows by finite iteration from the following
batch lemma.

> **Batch lemma.** At least one of the three edited wallets has success
> probability at least \(\Phi(\mathcal F)\).

## 5. Exact algebraic form of the batch lemma

For two families \(\mathcal X,\mathcal Y\), define the oriented
disjointness weight

\[
W(\mathcal X,\mathcal Y)=
\sum_{\substack{X\in\mathcal X,\;Y\in\mathcal Y\\X\cap Y=\varnothing}}
s^{|X|}t^{|Y|}\lambda^{n-|X|-|Y|}.
\]

Set

\[
\begin{array}{lll}
x=W(\mathcal A,\mathcal B),&
y=W(\mathcal B,\mathcal A),&
p=W(\mathcal A,\mathcal C),\\
z=W(\mathcal B,\mathcal C),&
h=W(\mathcal H,\mathcal A),&
k=W(\mathcal H,\mathcal B),
\end{array}
\]

and \(K_0=W(\mathcal H,\mathcal C)\). If

\[
\begin{aligned}
a&=\Phi(\mathcal H),\\
b&=\Phi(\mathcal H\cup\mathcal A)=\Phi(\mathcal F),\\
c&=\Phi(\mathcal H\cup\mathcal B),\\
d&=\Phi(\mathcal H\cup\mathcal A\cup\mathcal B),
\end{aligned}
\]

then direct expansion gives

\[
\begin{aligned}
a&=K_0+h+k,\\
b&=K_0+k+x+p,\\
c&=K_0+h+y+z,\\
d&=K_0+p+z.
\end{aligned}
\]

Put

\[
u=b-a=x+p-h,\qquad v=b-d=x+k-z.
\]

Then

\[
c-b=x+y-u-v.
\]

Consequently the batch lemma is exactly the implication

\[
\boxed{\quad u>0,\ v>0\quad\Longrightarrow\quad u+v\leq x+y.\quad}
\]

The cases \(u\leq0\) and \(v\leq0\) are already handled by the remove
and fill edits, respectively.

Because every member of \(\mathcal A\) has rank \(r\) and every member
of \(\mathcal B\) has rank \(q\),

\[
y=\left(\frac{s}{t}\right)^{q-r}x
\]

when \(t>0\). Since \(s>1/2\) implies \(s>t\), we have \(y\geq x\).
This rank bias is the extra structure that must be used in proving the
boxed inequality; ordinary submodularity alone only supplies a
nonnegative cross term and is insufficient.

An equivalent marginal formulation is useful. Let

\[
\begin{aligned}
E_A&=\Phi(\mathcal H\cup\mathcal A)-\Phi(\mathcal H),\\
E_B&=\Phi(\mathcal H\cup\mathcal B)-\Phi(\mathcal H),\\
K&=x+y.
\end{aligned}
\]

Relative to the original wallet, the three changes are

\[
\begin{array}{c|c}
\text{edit}&\text{change}\\
\hline
\text{remove}&-E_A\\
\text{fill}&E_B-K\\
\text{both}&E_B-E_A.
\end{array}
\]

Therefore only the regime

\[
E_A>0,\qquad E_B<K
\]

is nontrivial, and there it remains to prove \(E_B\geq E_A\).

## 6. Cases in which the batch lemma is proved

### 6.1 No stolen keys

If \(t=0\), the attacker set is empty. Filling \(\mathcal B\) can only
increase the owner's authorization probability, so the fill edit is
non-worsening.

### 6.2 The endpoint \(s=1\)

Here \(t=\lambda=0\). All relevant nonempty proper wallets tie with
success probability one, so a non-worsening canonicalization is
possible.

### 6.3 The boundary ranks overlap

If \(r+q>n\), no authorized set can be disjoint from a member of
\(\mathcal B\). Hence \(x=k=0\), and

\[
d-b=z\geq0.
\]

Thus filling the highest incomplete layer is non-worsening.

### 6.4 No lost keys

Suppose \(\lambda=0\). Only complementary owner-attacker pairs have
positive probability.

- If \(r+q<n\), the complement of every member of \(\mathcal A\) lies
  above layer \(q\) and belongs to \(\mathcal H\). Removing
  \(\mathcal A\) is non-worsening.
- If \(r+q>n\), the complement of every member of \(\mathcal B\) lies
  below layer \(r\) and belongs to \(\mathcal C\). Filling
  \(\mathcal B\) is non-worsening.
- If \(r+q=n\), let \(N\) be the number of complementary
  \(\mathcal A\)-\(\mathcal B\) pairs. Then
  \[
  c-b=
  (|\mathcal A|+|\mathcal B|-N)s^qt^r-Ns^rt^q.
  \]
  Since \(N\leq\min(|\mathcal A|,|\mathcal B|)\) and \(s>t\),
  \[
  c-b\geq N(s^qt^r-s^rt^q)\geq0.
  \]
  Thus the both edit is non-worsening.

The entire target theorem is therefore proved when \(\lambda=0\).

## 7. The formerly missing case

The remaining parameter regime

\[
\lambda>0,\qquad t>0,\qquad r+q\leq n
\]

is proved in Sections 9--13 using maximal-chain thresholds and a
coefficientwise binomial inequality. The earlier conditioning argument
did not by itself identify one common edit, but the chain formulation
does.

## 8. Computational evidence

Exact enumeration has found no violation of the batch lemma:

- all monotone wallets through \(n=5\) on a large rational parameter
  grid;
- all shifted wallets through \(n=7\) on exact rational grids;
- additional random shifted wallets through \(n=8\).

These computations were useful for locating the correct inequality.
The proof below now replaces the computational evidence.

## 9. Maximal-chain representation

Let \(\pi\) be a uniformly random permutation of \([n]\), and write

\[
P_k(\pi)=\{\pi_1,\ldots,\pi_k\}.
\]

For an up-family \(\mathcal F\), define its threshold on this chain by

\[
\tau(\pi)=\min\{k:P_k(\pi)\in\mathcal F\}.
\]

Generate a key-state outcome as follows. First draw

\[
(I,L,J)\sim\operatorname{Multinomial}(n;s,\lambda,t),
\]

then declare the first \(I\) entries of \(\pi\) safe, the next \(L\)
lost, and the last \(J\) stolen. This produces exactly the original
i.i.d. key-state distribution.

The owner set is \(P_I(\pi)\), while the stolen set is
\(P_J(\operatorname{rev}\pi)\). Consequently

\[
\Phi(\mathcal F)
=
\mathbb E_\pi H\bigl(\tau(\pi),\tau(\operatorname{rev}\pi)\bigr),
\]

where

\[
H(a,b)=\Pr(I\geq a,\ J<b).
\]

Since \(\pi\) and \(\operatorname{rev}\pi\) have the same distribution,
we may symmetrize:

\[
K(a,b)=H(a,b)+H(b,a),
\qquad
\Phi(\mathcal F)
=\frac12\mathbb E_\pi
K\bigl(\tau(\pi),\tau(\operatorname{rev}\pi)\bigr).
\tag{9.1}
\]

If \(r<q\) are the lowest and highest incomplete layers, then

\[
r\leq\tau(\pi)\leq q+1.
\]

Moreover, the three batch edits act exactly as scalar clipping maps:

\[
R(k)=
\begin{cases}
r+1,&k=r,\\
k,&k\neq r,
\end{cases}
\qquad
Q(k)=
\begin{cases}
q,&k=q+1,\\
k,&k\neq q+1.
\end{cases}
\]

Removing layer \(r\) applies \(R\) to every chain threshold. Indeed, if
\(\tau=r\), upward closure ensures that the next prefix, of rank
\(r+1\), remains authorized. Filling layer \(q\) applies \(Q\).
Performing both edits applies \(Q\circ R\).

## 10. Discrete derivatives of the chain kernel

Define

\[
g_k(m)=K(k+1,m)-K(k,m).
\]

A direct calculation gives

\[
g_k(m)
=
\Pr(I\geq m,J=k)-\Pr(I=k,J<m).
\tag{10.1}
\]

It follows that

\[
g_k(m+1)-g_k(m)
=-\Pr(I=m,J=k)-\Pr(I=k,J=m)\leq0.
\tag{10.2}
\]

Thus \(g_k(m)\) is nonincreasing in \(m\).

Two cases now follow immediately.

1. If \(g_r(q+1)\geq0\), then raising a threshold \(r\) to \(r+1\)
   pointwise does not decrease \(K\) on any pair in
   \([r,q+1]^2\). Hence removing the lowest incomplete layer is
   non-worsening.
2. If \(g_q(r)\leq0\), then lowering a threshold \(q+1\) to \(q\)
   pointwise does not decrease \(K\). Hence filling the highest
   incomplete layer is non-worsening.

The only hard crossing regime is therefore

\[
g_r(q+1)<0<g_q(r).
\tag{10.3}
\]

If \(r+q>n\), filling layer \(q\) is already non-worsening: every
authorized owner set has size at least \(r\), so it cannot be disjoint
from an attacker set of size \(q\). Adding layer \(q\) therefore creates
no new attacker-success event.

It remains to treat \(r+q\leq n\).

## 11. The kernel certificate

Put

\[
A=g_r(q+1),\qquad
D=g_r(q)-g_q(r),\qquad
\rho=\frac{\binom nq}{\binom nr}.
\]

Because \(r<q\) and \(r+q\leq n\), binomial unimodality gives
\(\rho\geq1\).

The key inequality is

\[
\boxed{\quad D+(\rho-1)A\geq0.\quad}
\tag{11.1}
\]

In the hard regime \(A<0\), it implies

\[
D\geq-(\rho-1)A\geq0.
\tag{11.2}
\]

We next prove (11.1) coefficientwise.

Set

\[
\eta=s-t-\lambda=2s-1\geq0,
\qquad s=t+\lambda+\eta.
\]

After substituting this expression for \(s\), every \(g_k(m)\) is a
homogeneous polynomial of degree \(n\) in \(t,\lambda,\eta\).
For \(a+b+c=n\), the coefficient of
\(t^a\lambda^b\eta^c\), after removing the common positive factor
\(n!/(a!b!c!)\), is

\[
\gamma_k(m)
=
\binom ak
\sum_{u=0}^{n-k-m}\binom bu
-
\sum_{j=0}^{m-1}
\binom aj\binom b{n-k-j}.
\tag{11.3}
\]

Here and below, an empty sum is zero and an out-of-range binomial
coefficient is zero.

Thus it is enough to prove

\[
\gamma_r(q)-\gamma_q(r)
+(\rho-1)\gamma_r(q+1)\geq0
\tag{11.4}
\]

for every \(a,b,c\geq0\) with \(a+b+c=n\).

## 12. The binomial-coefficient lemma

Let

\[
h=n-r-q,\qquad
N_k=\binom nk,\qquad
M=a+b\leq n.
\]

Multiply (11.4) by \(N_r>0\), and denote the result by

\[
E=
N_r\bigl(\gamma_r(q)-\gamma_q(r)\bigr)
+(N_q-N_r)\gamma_r(q+1).
\]

Vandermonde's identity rewrites (11.3) as

\[
\gamma_k(m)
=
\sum_{u=0}^{n-k-m}
\binom bu
\left[
\binom ak+\binom a{n-k-u}
\right]
-\binom M{n-k}.
\tag{12.1}
\]

When (12.1) is substituted into \(E\), the \(u=h\) terms cancel.
Reindexing the remaining terms by \(v=h-u\) gives

\[
\begin{aligned}
E={}&
\sum_{v=1}^{h}\binom b{h-v}
\Biggl\{
N_q\left[\binom ar+\binom a{q+v}\right]
-
N_r\left[\binom aq+\binom a{r+v}\right]
\Biggr\}\\
&+
N_r\binom M{n-q}
-
N_q\binom M{n-r}.
\tag{12.2}
\end{aligned}
\]

Every term on the right is nonnegative.

For the final line, put \(x=n-q<y=n-r\). The ratio

\[
k\longmapsto\frac{\binom Mk}{\binom nk}
\]

is nonincreasing when \(M\leq n\), because the ratio of consecutive
nonzero terms is \((M-k)/(n-k)\leq1\) for \(k<M\), after which the
numerator is zero. Hence

\[
\frac{\binom M{n-q}}{\binom n{n-q}}
\geq
\frac{\binom M{n-r}}{\binom n{n-r}},
\]

which is the required nonnegativity of the final line of (12.2).

Now fix \(1\leq v\leq h\), and put

\[
N_0=r+q+v\leq n.
\]

For fixed \(r<q\), the ratio
\(\binom nq/\binom nr\) is nondecreasing in \(n\). Therefore

\[
\frac{N_q}{N_r}
\geq
\rho_0:=
\frac{\binom{N_0}q}{\binom{N_0}r}.
\tag{12.3}
\]

Define

\[
p_k=\frac{\binom ak}{\binom{N_0}k},
\qquad 0\leq k\leq N_0.
\]

This sequence is convex. Indeed,

\[
p_{k+2}-2p_{k+1}+p_k
=
p_k
\frac{(N_0-a)(N_0-a-1)}
{(N_0-k)(N_0-k-1)}
\geq0,
\tag{12.4}
\]

for \(0\leq k\leq N_0-2\), with the same conclusion at zero-binomial
boundary cases.

The pairs

\[
(r,q+v)
\quad\text{and}\quad
(q,r+v)
\]

have the same sum \(N_0\), and the first pair is the outer pair.
Convexity therefore gives

\[
p_r+p_{q+v}\geq p_q+p_{r+v}.
\]

Using binomial symmetry in row \(N_0\), this is equivalent to

\[
\rho_0
\left[\binom ar+\binom a{q+v}\right]
\geq
\binom aq+\binom a{r+v}.
\tag{12.5}
\]

Combining (12.3) and (12.5) proves that every bracket in (12.2) is
nonnegative. Hence \(E\geq0\), proving (11.4), then (11.1).

## 13. Completion of the batch lemma and theorem

Return to the hard regime (10.3), with \(r+q\leq n\). From (11.2),

\[
g_r(q)\geq g_q(r)>0.
\tag{13.1}
\]

Let

\[
w_{rq}=\Pr(I=r,J=q)+\Pr(I=q,J=r).
\]

By (10.2),

\[
g_r(q+1)=g_r(q)-w_{rq}<0,
\]

so \(w_{rq}>g_r(q)\). Together with (13.1), this gives

\[
g_q(r+1)=g_q(r)-w_{rq}<0.
\tag{13.2}
\]

Equations (13.1), (13.2), and the monotonicity (10.2) show pointwise
that applying both clipping maps does not decrease \(K\):

- a pair involving \(r\) and an interior threshold gains
  \(g_r(m)\geq g_r(q)>0\);
- a pair involving \(q+1\) and an interior threshold gains
  \(-g_q(m)\geq-g_q(r+1)>0\);
- the extreme pair \((r,q+1)\) gains
  \[
  K(r+1,q)-K(r,q+1)
  =g_r(q)-g_q(r)\geq0;
  \]
- the two diagonal extreme pairs gain
  \[
  K(r+1,r+1)-K(r,r)=g_r(r)+g_r(r+1)\geq0
  \]
  and
  \[
  K(q,q)-K(q+1,q+1)=-g_q(q)-g_q(q+1)\geq0;
  \]
- pairs containing neither extreme are unchanged.

Therefore, in every case, at least one of remove, fill, or both is
non-worsening. Averaging the pointwise kernel comparison in (9.1)
proves the batch lemma.

Each application removes at least one incomplete layer and creates no
new one. Repeating finitely produces a wallet \(\mathcal F^\star\) with

\[
\Phi(\mathcal F^\star)\geq\Phi(\mathcal F)
\]

and at most one incomplete layer.

Starting from an optimal wallet, every non-worsening step must tie with
the optimum. Hence some optimal wallet has at most one incomplete
layer. This proves the target theorem.
