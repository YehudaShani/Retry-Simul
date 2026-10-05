# Canonical optimal wallets have at most one incomplete layer

## 1. Model and theorem

For each of the \(n\) keys, independently, let the state be

- safe, with probability \(s\): the owner has the key and the attacker does not;
- stolen, with probability \(t\): the attacker has the key and the owner does not;
- leaked, with probability \(e\): both have the key;
- lost, with probability \(\ell\): neither has the key.

Thus

\[
s+t+e+\ell=1,\qquad s>\frac12.
\]

Let \(O,D\subseteq[n]\) be the sets held by the owner and attacker,
respectively. A wallet is an upward-closed family
\(\mathcal F\subseteq2^{[n]}\), and its success probability is

\[
\Phi(\mathcal F)=\Pr(O\in\mathcal F,\ D\notin\mathcal F).
\]

Write

\[
\mathcal F_k=\mathcal F\cap\binom{[n]}k.
\]

Layer \(k\) is incomplete when

\[
0<|\mathcal F_k|<\binom nk.
\]

We prove the following stronger canonicalization statement.

> **Theorem.** For every wallet \(\mathcal F\), there is a wallet
> \(\mathcal F^\star\) such that
> \[
> \Phi(\mathcal F^\star)\geq\Phi(\mathcal F)
> \]
> and \(\mathcal F^\star\) has at most one incomplete layer.

In particular, some optimal wallet has at most one incomplete layer.
The argument does not require \(e=0\), shifting, or a one-set
lexicographic swap.

## 2. The three batch edits

Suppose \(\mathcal F\) has at least two incomplete layers, and let
\(r<q\) be the lowest and highest incomplete ranks. Upward closure
implies that all layers below \(r\) are empty and all layers above
\(q\) are full.

Put

\[
\mathcal A=\mathcal F_r,\qquad
\mathcal B=\binom{[n]}q\setminus\mathcal F_q,
\]

and define their densities

\[
\alpha=\frac{|\mathcal A|}{\binom nr},\qquad
\beta=\frac{|\mathcal B|}{\binom nq}.
\]

Consider:

\[
\begin{aligned}
\mathcal F_R&=\mathcal F\setminus\mathcal A,\\
\mathcal F_Q&=\mathcal F\cup\mathcal B,\\
\mathcal F_{RQ}&=(\mathcal F\setminus\mathcal A)\cup\mathcal B.
\end{aligned}
\]

These are up-families. They remove, respectively, the lowest
incomplete layer, the highest incomplete layer, or both.

Let

\[
I=|O|,\qquad J=|D|,
\]

and define the rank kernel

\[
g_k(m)=\Pr(I\geq m,J=k)-\Pr(I=k,J<m).
\tag{2.1}
\]

Exchangeability of the keys and the empty/full boundary layers give

\[
\Phi(\mathcal F_R)-\Phi(\mathcal F)
\geq \alpha g_r(q+1),
\tag{2.2}
\]

and

\[
\Phi(\mathcal F_Q)-\Phi(\mathcal F)
\geq-\beta g_q(r).
\tag{2.3}
\]

For example, in (2.2), every outcome with
\(D\in\mathcal A\) and \(I\geq q+1\) is a gain after removing
\(\mathcal A\), whereas a lost success with \(O\in\mathcal A\) can
only have \(J\leq q\).

Applying the edits in the two possible orders also gives two lower
bounds for the joint edit:

\[
\Phi(\mathcal F_{RQ})-\Phi(\mathcal F)
\geq L_1:=\alpha g_r(q)-\beta g_q(r),
\tag{2.4}
\]

\[
\Phi(\mathcal F_{RQ})-\Phi(\mathcal F)
\geq L_2:=\alpha g_r(q+1)-\beta g_q(r+1).
\tag{2.5}
\]

The first comes from filling layer \(q\) and then removing layer \(r\);
the second comes from removing layer \(r\) and then filling layer \(q\).

We will prove that at least one of the lower bounds on the right sides
of (2.2)--(2.5) is nonnegative.

## 3. The low-sum kernel certificate

The central inequality is the following.

> **Kernel certificate.** If
> \[
> 1\leq r<q\leq n-1,\qquad r+q\leq n,
> \]
> then
> \[
> \boxed{\quad
> \binom nq\,g_r(q+1)
> \geq
> \binom nr\,g_q(r+1).
> \quad}
> \tag{3.1}
> \]

Sections 4--7 prove (3.1).

First we show how it finishes the batch argument when \(r+q\leq n\).
From (2.1),

\[
g_k(m+1)-g_k(m)
=-\Pr(I=m,J=k)-\Pr(I=k,J=m).
\tag{3.2}
\]

If \(g_r(q+1)\geq0\), (2.2) proves that the remove edit is
non-worsening. If \(g_q(r)\leq0\), (2.3) proves the same for the fill
edit. It remains to consider

\[
g_r(q+1)<0<g_q(r).
\tag{3.3}
\]

Set

\[
w=\Pr(I=q,J=r)+\Pr(I=r,J=q)
\]

and

\[
\rho=\frac{\binom nq}{\binom nr}\geq1.
\]

Indeed, \(r<q\leq n-r\), and binomial coefficients are nondecreasing
from rank \(r\) through the middle rank, with symmetry about the
middle.

By (3.2),

\[
g_r(q+1)=g_r(q)-w,\qquad
g_q(r+1)=g_q(r)-w.
\tag{3.4}
\]

The certificate (3.1) therefore says

\[
\rho\bigl(g_r(q)-w\bigr)\geq g_q(r)-w.
\tag{3.5}
\]

Because \(g_r(q+1)<0\), we have \(w>g_r(q)\). Equation (3.5) then
gives explicitly

\[
g_r(q)-g_q(r)
\geq(\rho-1)\bigl(w-g_r(q)\bigr)\geq0,
\]

and hence

\[
g_r(q)\geq g_q(r)>0.
\tag{3.6}
\]

Using (3.4) once more,

\[
g_q(r+1)\leq g_r(q+1)<0.
\tag{3.7}
\]

If \(L_1\geq0\), the joint edit is non-worsening. Otherwise,

\[
\alpha g_r(q)<\beta g_q(r).
\]

By (3.6), this implies \(\alpha<\beta\). By (3.7),

\[
-g_q(r+1)\geq-g_r(q+1)>0,
\]

so

\[
L_2
=\beta[-g_q(r+1)]-\alpha[-g_r(q+1)]>0.
\]

Thus one of the three edits is non-worsening.

## 4. Coefficient reduction

Put

\[
\eta=s-(t+e+\ell)=2s-1\geq0,
\qquad
s=t+e+\ell+\eta.
\tag{4.1}
\]

After this substitution, the difference between the two sides of
(3.1) is a homogeneous polynomial in \(t,e,\ell,\eta\). We prove that
every coefficient is nonnegative.

Fix a monomial

\[
t^a e^b\ell^c\eta^d,\qquad a+b+c+d=n.
\]

For a fixed labelled partition

\[
[n]=T\sqcup E\sqcup L\sqcup H,
\qquad
|T|=a,\ |E|=b,\ |L|=c,\ |H|=d,
\]

the expansion (4.1) has the following combinatorial meaning:

- a \(T\)-coordinate is either safe or stolen;
- an \(E\)-coordinate is either safe or leaked;
- an \(L\)-coordinate is either safe or lost;
- an \(H\)-coordinate is safe.

If \(x,y,z\) are the numbers chosen as stolen, leaked, and lost in the
first three blocks, then

\[
J=x+y,\qquad n-I=x+z,
\tag{4.2}
\]

with multiplicity

\[
\binom ax\binom by\binom cz.
\]

Let

\[
G_k(m)
=\#\{J=k,\ n-I\leq n-m\}
-\#\{n-I=n-k,\ J<m\}
\tag{4.3}
\]

under these toggle assignments. The coefficient of the polynomial in
(3.1) is the common positive factor

\[
\frac{n!}{a!b!c!d!}
\]

times

\[
\binom nqG_r(q+1)-\binom nrG_q(r+1).
\tag{4.4}
\]

It remains to prove that (4.4) is nonnegative for every labelled color
partition.

## 5. Averaging over nested sets

For \(A\subset B\), with \(|A|=r\) and \(|B|=q\), define the signed
indicator

\[
\begin{aligned}
\Lambda(A,B)={}&
\mathbf1_{\{D=A,\ |O|\geq q+1\}}
+\mathbf1_{\{O=B,\ |D|\leq r\}}\\
&-\mathbf1_{\{O=A,\ |D|\leq q\}}
-\mathbf1_{\{D=B,\ |O|\geq r+1\}}.
\end{aligned}
\tag{5.1}
\]

Summing over all toggle assignments and all nested pairs gives

\[
\begin{aligned}
\sum_{\substack{A\subset B\\|A|=r,\ |B|=q}}
\ \sum_{\rm assignments}\Lambda(A,B)
={}&
\binom{n-r}{q-r}G_r(q+1)
-\binom qrG_q(r+1)\\
={}&
\frac{\binom qr}{\binom nr}
\left[
\binom nqG_r(q+1)-\binom nrG_q(r+1)
\right].
\end{aligned}
\tag{5.2}
\]

We prove the left side is nonnegative by fixing

\[
M=B\setminus A,\qquad |M|=q-r,
\]

and summing over all \(r\)-sets \(A\) disjoint from \(M\).

There are four exhaustive cases.

1. If \(M\) contains an \(H\)-coordinate, both negative events in
   (5.1) are impossible.
2. If \(M\) contains both an \(E\)-coordinate and an \(L\)-coordinate,
   \(O=A\) is impossible because every \(E\)-coordinate belongs to
   \(O\), while \(D=B\) is impossible because no \(L\)-coordinate
   belongs to \(D\).
3. If every coordinate of \(M\) has color \(T\), changing all of them
   from stolen to safe injects
   \[
   \{O=A,\ |D|\leq q\}
   \longrightarrow
   \{O=B,\ |D|\leq r\},
   \]
   and
   \[
   \{D=B,\ |O|\geq r+1\}
   \longrightarrow
   \{D=A,\ |O|\geq q+1\}.
   \]
4. The only remaining cases are
   \(M\subseteq T\cup L\) with an \(L\)-coordinate, and
   \(M\subseteq T\cup E\) with an \(E\)-coordinate.

The two remaining injections are given next.

## 6. The \(L\)-case

Suppose

\[
M\subseteq T\cup L,\qquad
l:=|M\cap L|\geq1.
\]

Outside \(M\), let the numbers of \(T,E,L,H\)-coordinates be

\[
T,\ b,\ L,\ d,
\]

respectively. Put

\[
\delta=n-r-q\geq0,\qquad k_0=r-b-d.
\]

Since \(|M|=q-r\),

\[
T=2r-b-L-d+\delta,
\qquad
2k_0=T-b+L-d-\delta.
\tag{6.1}
\]

Here is the event count leading to the reduced inequality. The
negative event \(O=A\) forces every outside-\(M\) \(E\)- and
\(H\)-coordinate into \(A\). If \(A\) also contains \(j\) of the
outside \(L\)-coordinates, it contains \(k_0-j\) outside
\(T\)-coordinates. Pairing with the positive event \(O=B\) leaves
exactly the configurations in which the number of leaked
\(E\)-coordinates is

\[
L-\delta-j+s,\qquad 1\leq s\leq l.
\]

Their count is the negative term in (6.3).

For the other positive event, \(D=A\), reindex by

\[
|A\cap E|=L-\delta-j.
\]

The \(T\)-choice has size complementary to \(k_0-j\), and hence has
the same binomial count \(\binom{T}{k_0-j}\). If \(W\) is the set of
lost coordinates in the combined \(L\)-block of size \(L+l\), the
condition \(|O|\geq q+1\) is exactly

\[
|W|\leq L-j-1.
\]

This gives the positive term in (6.3). Therefore the sum of the four
terms in (5.1), over all \(A\cap M=\varnothing\), is

\[
\sum_{j\in\mathbb Z}\binom{T}{k_0-j}H_j\geq0,
\tag{6.2}
\]

where

\[
\begin{aligned}
H_j={}&
\binom b{L-\delta-j}
\sum_{w=0}^{L-j-1}\binom{L+l}{w}\\
&-\binom Lj
\sum_{s=1}^{l}\binom b{L-\delta-j+s}.
\end{aligned}
\tag{6.3}
\]

All out-of-range binomial coefficients and empty sums are zero. In
particular, negative values of \(j\) are allowed when the first term is
nonzero.

We inject every object counted by the negative part into the positive
part. A negative object indexed by \((j,s)\) consists of

\[
\begin{aligned}
&K\subseteq[T], &&|K|=k_0-j=:k,\\
&J\subseteq[L], &&|J|=j,\\
&A_E\subseteq[b],&&|A_E|=L-\delta-j+s,\\
&1\leq s\leq l.
\end{aligned}
\]

Set

\[
j'=j-s.
\]

Keep \(A_E\), and define

\[
W=([L]\setminus J)\cup P_{s-1},
\tag{6.4}
\]

where \(P_{s-1}\) is the fixed canonical prefix of length \(s-1\) in
the \(l\)-element block \(M\cap L\). Then

\[
|W|=L-j+s-1=L-j'-1,
\]

so \(W\) is counted by the cumulative sum in the positive term at
index \(j'\).

It remains to raise \(K\) from size \(k\) to size \(k+s\). Since the
negative object is nonzero,

\[
L-\delta-j+s\leq b.
\]

Using (6.1),

\[
\begin{aligned}
T-2k-s
&=b-L+d+\delta+2j-s\\
&=(b-L+\delta+j-s)+(d+j)\geq0.
\end{aligned}
\tag{6.5}
\]

Hence \(k+s\leq T-k\). A fixed symmetric-chain decomposition of
\(2^{[T]}\) therefore gives an injective raising map

\[
\binom{[T]}k\longrightarrow\binom{[T]}{k+s}.
\]

Use it to send \(K\) to \(K'\).

The image recovers \(s\) from the canonical prefix
\(W\cap(M\cap L)\), then recovers \(j,J,A_E\), and finally \(K\) from
the injective raising map. Images from distinct \((j,s)\) are
therefore disjoint. This proves (6.2).

## 7. The \(E\)-case

Suppose

\[
M\subseteq T\cup E,\qquad
e_M:=|M\cap E|\geq1.
\]

Outside \(M\), let the numbers of \(T,E,L,H\)-coordinates be

\[
T,\ E,\ c,\ d,
\]

and put

\[
\delta=n-r-q,\qquad k_0=r-E-d.
\]

For completeness, the corresponding event count is as follows. In
the positive event \(O=B\), suppose \(A\) contains \(j\) outside
\(L\)-coordinates. It must contain all outside \(E\)- and
\(H\)-coordinates, leaving \(k_0-j\) choices from the outside
\(T\)-block. The condition \(|D|\leq r\) permits at most

\[
c-\delta-j
\]

leaked coordinates in the combined \(E\)-block of size \(E+e_M\).
This is the first term in (7.1).

For the negative event \(D=B\), pair the configurations covered by
the positive event \(D=A\) by forcing the coordinates of \(M\) safe.
Reindex the remaining configurations by taking
\(|A\cap E|=c-\delta-j\). The unmatched configurations have an
outside-\(L\) safe set of size

\[
j+1-s,\qquad 1\leq s\leq e_M.
\]

This gives the second term. Hence the fixed-\(M\) sum is

\[
\begin{aligned}
\sum_{j\in\mathbb Z}\binom{T}{k_0-j}
\Bigg[
&\binom cj\sum_{w=0}^{c-\delta-j}\binom{E+e_M}{w}\\
&-\binom E{c-\delta-j}
\sum_{s=1}^{e_M}\binom c{j+1-s}
\Bigg].
\end{aligned}
\tag{7.1}
\]

Again, all sums are over integer \(j\), and out-of-range binomial
coefficients and empty sums are zero.

A negative object indexed by \((j,s)\) consists of

\[
\begin{aligned}
&K\subseteq[T],&&|K|=k_0-j=:k,\\
&A_E\subseteq[E],&&|A_E|=c-\delta-j,\\
&J\subseteq[c],&&|J|=j+1-s,\\
&1\leq s\leq e_M.
\end{aligned}
\]

Set

\[
j'=j+1-s.
\]

Keep \(J\), extend \(A_E\) by the canonical prefix of length \(s-1\)
in \(M\cap E\), and raise \(K\) by \(s-1\) ranks in a fixed
symmetric-chain decomposition.

Indeed, nonvanishing of \(A_E\) and \(J\) gives

\[
E-c+\delta+j\geq0,\qquad j-s+1\geq0.
\]

Consequently,

\[
\begin{aligned}
T-2k-(s-1)
&=(E-c+\delta+j)+(d+j-s+1)\geq0,
\end{aligned}
\tag{7.2}
\]

so the required raising map exists. The enlarged \(E\)-set has size

\[
c-\delta-j+s-1=c-\delta-j',
\]

which is exactly the top allowed size in the positive cumulative term
at \(j'\).

As in Section 6, the canonical prefix recovers \(s\), after which all
source data are recovered. The map is injective and its strata are
disjoint. This proves (7.1).

Every fixed-\(M\) sum in (5.2) is now nonnegative. Hence (4.4) is
nonnegative for every coefficient, proving the kernel certificate
(3.1).

## 8. The high-sum case

It remains to handle \(r+q>n\). Define the dual wallet

\[
\mathcal F^\ast
=\{X\subseteq[n]:[n]\setminus X\notin\mathcal F\}.
\tag{8.1}
\]

It is an up-family. Define transformed owner and attacker sets by

\[
O^\ast=[n]\setminus D,\qquad
D^\ast=[n]\setminus O.
\tag{8.2}
\]

On each coordinate, this transformation preserves the safe and stolen
states and exchanges the leaked and lost states. Moreover,

\[
O^\ast\in\mathcal F^\ast,\ D^\ast\notin\mathcal F^\ast
\quad\Longleftrightarrow\quad
O\in\mathcal F,\ D\notin\mathcal F.
\tag{8.3}
\]

Thus

\[
\Phi_{s,t,e,\ell}(\mathcal F)
=\Phi_{s,t,\ell,e}(\mathcal F^\ast).
\tag{8.4}
\]

The lowest and highest incomplete ranks of \(\mathcal F^\ast\) are

\[
r^\ast=n-q,\qquad q^\ast=n-r.
\]

When \(r+q>n\),

\[
r^\ast+q^\ast=2n-r-q<n.
\]

The low-sum result applies to \(\mathcal F^\ast\). Dualizing its
non-worsening batch edit back to \(\mathcal F\) proves the high-sum
case: removal in the dual becomes filling in the original, filling in
the dual becomes removal in the original, and the joint edit remains
a joint edit.

## 9. Completion

For any wallet with at least two incomplete layers, at least one of
the remove, fill, or joint batch edits is non-worsening. Each edit
removes at least one incomplete layer and creates no new incomplete
layer. After finitely many steps we obtain a wallet
\(\mathcal F^\star\) with

\[
\Phi(\mathcal F^\star)\geq\Phi(\mathcal F)
\]

and at most one incomplete layer.

Starting from an optimal wallet, every non-worsening edit must tie with
the optimum. Therefore some optimal wallet has at most one incomplete
layer, for arbitrary leaked-key probability.
