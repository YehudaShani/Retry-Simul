from fractions import Fraction as F
from math import comb


def power(x, k):
    return x ** k


def check_type(n, c, a, b, d, y, z, u):
    r, q = c + a, c + b
    yp = [y ** h for h in range(n + 1)]
    zp = [z ** h for h in range(n + 1)]
    up = [u ** h for h in range(n + 1)]

    def gamma(i, j, k, ell):
        m = i + j + k + ell
        return (
            yp[m] * zp[n - r] * up[k + ell]
            + yp[r] * zp[n - m] * up[c - i + a - j]
            - yp[m] * zp[n - q] * up[j + ell]
            - yp[q] * zp[n - m] * up[c - i + b - k]
        )

    po_r = power(1 + y, r) * power(z * (1 + u * y), n - r)
    po_q = power(1 + y, q) * power(z * (1 + u * y), n - q)
    cross = (
        yp[q] * zp[n - q]
        + yp[r] * zp[n - r]
        - yp[r] * zp[n - q] * up[a]
        - yp[q] * zp[n - r] * up[b]
    )
    delta0 = po_q - po_r - cross
    negative_residual = F(0)

    for i in range(c + 1):
        for j in range(a + 1):
            for k in range(b + 1):
                for ell in range(d + 1):
                    mult = comb(c, i) * comb(a, j) * comb(b, k) * comb(d, ell)
                    g = gamma(i, j, k, ell)
                    forced_one = (i == c and j == a) or (
                        i == c and k == b and j + ell > 0
                    )
                    residual = (
                        j + ell > 0
                        and not (i == c and j == a)
                        and not (i == c and k == b)
                    )
                    if forced_one:
                        delta0 += mult * g
                    elif residual and g < 0:
                        negative_residual += mult * g
    return delta0 + negative_residual, delta0, negative_residual


def parameters():
    us = [F(0), F(1, 100), F(1, 10), F(1, 2), F(9, 10), F(99, 100), F(1)]
    ys = [F(1, 100), F(1, 10), F(1, 3), F(1, 2), F(2, 3), F(9, 10), F(99, 100)]
    zs = [F(1, 100), F(1, 10), F(1, 3), F(1, 2), F(2, 3), F(9, 10), F(99, 100)]
    for u in us:
        for y in ys:
            for z in zs:
                if y + z + u * y * z < 1:
                    yield y, z, u
        # Boundary points: z=(1-y-epsilon)/(1+uy)
        for y in ys:
            for eps in [F(1, 100), F(1, 1000), F(1, 10000)]:
                if y + eps < 1:
                    z = (1 - y - eps) / (1 + u * y)
                    if z > 0:
                        yield y, z, u


def main():
    pars = list(parameters())
    tested = 0
    closest = None
    for n in range(3, 11):
        for c in range(n + 1):
            for a in range(1, n - c + 1):
                for b in range(a + 1, n - c - a + 1):
                    d = n - c - a - b
                    if d < 0:
                        continue
                    for y, z, u in pars:
                        value, delta0, neg = check_type(n, c, a, b, d, y, z, u)
                        tested += 1
                        if closest is None or value < closest[0]:
                            closest = (value, n, c, a, b, d, y, z, u, delta0, neg)
                        if value < 0:
                            print("COUNTEREXAMPLE", closest)
                            return
        print("finished", n, "closest", closest)
    print("all nonnegative", tested, "closest", closest)


if __name__ == "__main__":
    main()
