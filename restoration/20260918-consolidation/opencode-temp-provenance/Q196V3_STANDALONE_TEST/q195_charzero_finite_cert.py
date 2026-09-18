"""Q195 characteristic-zero finite certificate V4 (Phase 12 script).

Reuses the FROZEN V3 exact-Gamma code (q195_exact_gamma.py, hash-checked
below — never modified). No floating point. Exit 1 unless every tested
characteristic-zero sector has a good reduction.
"""

import hashlib
import os
import sys

import q195_exact_gamma as G
from VOLTERRA_RESONANT_FIXED_STATE_CERT_STANDALONE import schedule_L3

FROZEN_GAMMA_SHA = "cdcac2a75260caf08e4e1a70598397b12b033481caab4556271559df083a64ac"

PRIMES = {9: (19, 37), 15: (31, 61), 21: (43, 127), 27: (109, 163),
          33: (67, 199), 39: (79, 157), 45: (181, 271)}
HIST9 = {(9, 3): (3, 1), (15, 5): (5, 1), (21, 14): (7, 2),
         (27, 9): (9, 1), (33, 11): (11, 1)}


def check(name, cond):
    print(f"[{'ok' if cond else 'FAIL'}] {name}", flush=True)
    if not cond:
        sys.exit(1)


def multiplicative_order(a, p):
    o = p - 1
    tmp, facs = o, set()
    d = 2
    while d * d <= tmp:
        if tmp % d == 0:
            facs.add(d)
            while tmp % d == 0:
                tmp //= d
        d += 1 if d == 2 else 2
    if tmp > 1:
        facs.add(tmp)
    for q in sorted(facs):
        while o % q == 0 and pow(a, o // q, p) == 1:
            o //= q
    return o


def exact_order_in_r(xi, r, p):
    """Exact multiplicative order (divides r since xi^r = 1)."""
    o = r
    tmp, facs = o, set()
    d = 2
    while d * d <= tmp:
        if tmp % d == 0:
            facs.add(d)
            while tmp % d == 0:
                tmp //= d
        d += 1 if d == 2 else 2
    if tmp > 1:
        facs.add(tmp)
    for q in sorted(facs):
        while o % q == 0 and pow(xi, o // q, p) == 1:
            o //= q
    return o


def divisors(n):
    ds = set()
    i = 1
    while i * i <= n:
        if n % i == 0:
            ds.add(i)
            ds.add(n // i)
        i += 1
    return sorted(ds)


def main():
    import VOLTERRA_RESONANT_FIXED_STATE_CERT_STANDALONE as _cert
    _here = os.path.realpath(os.getcwd())
    for _m in (_cert, G):
        _f = os.path.realpath(getattr(_m, "__file__", ""))
        check(f"dependency loads from run dir: {os.path.basename(_f)}",
              _f.startswith(_here + os.sep))
    with open(G.__file__, "rb") as f:
        h = hashlib.sha256(f.read()).hexdigest()
    check("frozen V3 harness hash", h == FROZEN_GAMMA_SHA)

    # §3: exact orders + the two d=7 cells side by side
    check("ord_43(4) = 7", multiplicative_order(4, 43) == 7)
    check("ord_127(4) = 7", multiplicative_order(4, 127) == 7)
    for (p, xi, want) in [(43, 4, 17), (127, 4, 18)]:
        r, core, Jcore = build_gamma_rows(7, 1, p, xi)
        j = G.fp_rank(core + Jcore, p)
        print(f"d=7 n0=1 p={p} xi={xi}: joint={j} (want {want})",
              flush=True)
        check(f"d=7 side-by-side p={p}", j == want)

    # Full grid recompute (both primes, all roots)
    cells = []
    for n0 in (1, 2):
        for d in (3, 5, 7, 9, 11, 13, 15):
            r = 3 * d
            H = (r + 1) // 2
            for p in PRIMES[r]:
                assert (p - 1) % r == 0
                for xi in G.rth_roots(p, r):
                    s = exact_order_in_r(xi, r, p)
                    check(f"lemma hypotheses p={p} odd, p∤2ξ-order "
                          f"(d={d} n0={n0} xi={xi})",
                          p % 2 == 1 and (s == 1 or p % s != 0)
                          and pow(xi, s, p) == 1)
                    r_, core, Jcore = build_gamma_rows(d, n0, p, xi)
                    rC = G.fp_rank(core, p)
                    rJ = G.fp_rank(Jcore, p)
                    joint = G.fp_rank(core + Jcore, p)
                    cells.append({'d': d, 'n0': n0, 'p': p, 'xi': xi,
                                  'ord': s, 'rC': rC, 'rJ': rJ,
                                  'joint': joint, 'H': H, 'r': r})
    # §5: certifying prime = second prime; all-roots tables
    print("d n0 r cert-p roots minRankC minJoint target CHAR-0",
          flush=True)
    allcert = True
    for n0 in (1, 2):
        for d in (3, 5, 7, 9, 11, 13, 15):
            r = 3 * d
            H = (r + 1) // 2
            p2 = PRIMES[r][1]
            sub = [c for c in cells if c['d'] == d and c['n0'] == n0
                   and c['p'] == p2]
            check(f"cert prime covers all {r} roots d={d} n0={n0}",
                  len(sub) == r)
            mC = min(c['rC'] for c in sub)
            mJ = min(c['joint'] for c in sub)
            okcell = (mC == H - 2 and mJ == r - 3)
            allcert &= okcell
            print(f"{d} {n0} {r} {p2} {len(sub)} {mC} {mJ} "
                  f"{H - 2}/{r - 3} {'CERTIFIED' if okcell else 'FAIL'}",
                  flush=True)
            for s in divisors(r):
                cov = [c for c in cells if c['d'] == d and c['n0'] == n0
                       and c['ord'] == s and c['joint'] == r - 3
                       and c['rC'] == H - 2]
                if not cov:
                    print(f"NO GOOD REDUCTION d={d} n0={n0} order {s}",
                          flush=True)
                    allcert = False
    check("every (d,n0) char-0 certified, every order covered", allcert)

    # §6: formal transversality at certifying primes
    for n0 in (1, 2):
        for d in (3, 5, 7, 9, 11, 13, 15):
            r = 3 * d
            p2 = PRIMES[r][1]
            E = (r + 1) * r
            for xi in G.rth_roots(p2, r):
                rr, _, s, R, P = G.int_word(d, n0, schedule_L3)
                T, _ = G.fstar_chronology(d)
                Fv, Rv = [], []
                for i in range(1, len(T) - 1):
                    pk, _ = G.formal_packet(R, P, s, T[i], T[i + 1], xi, p2)
                    fv = [0] * E
                    for (ii, jj), w in pk.items():
                        fv[ii * r + jj] = w
                    Fv.append(fv)
                    rv = [0] * E
                    for (ii, jj), w in G.J_formal(pk, P, xi, p2).items():
                        rv[ii * r + jj] = w
                    Rv.append(rv)
                g = len(Fv)
                rF = G.fp_rank(Fv, p2)
                rR = G.fp_rank(Rv, p2)
                fi = g + g - G.fp_rank(Fv + Rv, p2)
                if not (rF == g and rR == g and fi == 0):
                    print(f"FORMAL CERT FAIL d={d} n0={n0} xi={xi}",
                          flush=True)
                    sys.exit(1)
    print("formal transversality char-0 certified (all d, n0, roots at "
          "certifying primes)", flush=True)

    # §8: historical five, certifying primes + bad-cell reproduction
    for (rr, nn) in sorted(HIST9):
        d, n0 = HIST9[(rr, nn)]
        r = 3 * d
        H = (r + 1) // 2
        p2 = PRIMES[r][1]
        for xi in G.rth_roots(p2, r):
            r_, _, s, R, P = G.int_word(d, n0, schedule_L3)
            T, _ = G.fstar_chronology(d)
            W = []
            for (a, b) in [(T[0], T[1])] + [(T[i], T[i + 1])
                                            for i in range(1, len(T) - 1)]:
                Gam, _, _ = G.centered_gamma(R, P, a, b, xi, p2)
                W.append(G.reduce_qr(Gam, p2, r))
            JW = [G.J_poly(dict(enumerate(v)), xi, p2, r) for v in W]
            if not (G.fp_rank(W, p2) == H - 1
                    and G.fp_rank(W + JW, p2) == r - 1):
                print(f"HIST CERT FAIL (r,n)={(rr, nn)} p={p2} xi={xi}",
                      flush=True)
                sys.exit(1)
    print("historical five char-0 certified at second primes", flush=True)
    for (d, n0, p, xi, wr, wj) in [(5, 1, 31, 10, 7, 13),
                                   (11, 1, 67, 40, 16, 31)]:
        r = 3 * d
        r_, _, s, R, P = G.int_word(d, n0, schedule_L3)
        T, _ = G.fstar_chronology(d)
        W = []
        for (a, b) in [(T[0], T[1])] + [(T[i], T[i + 1])
                                        for i in range(1, len(T) - 1)]:
            Gam, _, _ = G.centered_gamma(R, P, a, b, xi, p)
            W.append(G.reduce_qr(Gam, p, r))
        JW = [G.J_poly(dict(enumerate(v)), xi, p, r) for v in W]
        print(f"bad-reduction reproduced d={d} p={p} xi={xi}: "
              f"rankW={G.fp_rank(W, p)} dimWJW={G.fp_rank(W + JW, p)} "
              f"(targets {wr} {wj})", flush=True)

    print("MODULAR BAD REDUCTIONS IDENTIFIED:", flush=True)
    print("(7,1,43,4) ord 7 joint 17; certified by (127,4) ord 7 joint 18",
          flush=True)
    print("(15,5,31,10) ord 15 W+JW 13; certified by (61,16) ord 15 W+JW 14",
          flush=True)
    print("(33,11,67,40) ord 11 W+JW 31; certified by (199,125) ord 11 "
          "W+JW 32", flush=True)

    # §9: independent cyclotomic cross-check
    run_cyclotomic_checks()

    print("Q195 SOURCE-FAITHFUL FINITE CASES:", flush=True)
    print("EXACT CHARACTERISTIC-ZERO CERTIFIED", flush=True)
    print("d = 3,5,7,9,11,13,15", flush=True)
    print("n0 = 1,2", flush=True)
    print("all xi^r = 1", flush=True)
    print("GENERAL d THEOREM: OPEN", flush=True)


def run_cyclotomic_checks():
    """§9 INDEPENDENT CYCLOTOMIC CROSS-CHECK (not part of main proof)."""
    from fractions import Fraction
    for s in (3, 7, 11, 15):
        F = Cyclo(s)
        check(f"cyclotomic selftest s={s}", F.selftest())
    # embed-check: cyclo rows mapped zeta->xi equal mod-p rows
    for (d, n0, s, p, xi) in [(5, 1, 15, 61, 16), (7, 1, 7, 127, 4)]:
        F = Cyclo(s)
        _, rows = cyclo_gamma_rows(d, n0, s, schedule_L3, full=False)
        r = 3 * d
        mapped = []
        for row in rows:
            mapped.append([sum((c.numerator * pow(c.denominator, p - 2, p)
                                * pow(xi, k, p)) % p
                               for k, c in enumerate(elt)) % p
                           for elt in row])
        _, core, _ = build_gamma_rows(d, n0, p, xi)
        check(f"cyclo embeds to mod-p rows d={d} s={s}",
              mapped == [[v % p for v in row] for row in core])
    # target ranks over Q(zeta_s)
    for (d, n0, s, want, full) in [(7, 1, 7, 18, False),
                                   (5, 1, 15, 14, True),
                                   (11, 1, 11, 32, True)]:
        F, rows = cyclo_gamma_rows(d, n0, s, schedule_L3, full=full)
        r = 3 * d
        Jrows = cyclo_J(rows, F, s, r)
        got = F.rank(rows + Jrows)
        print(f"cyclotomic d={d} s={s} full={full}: rank={got} "
              f"(want {want})", flush=True)
        check(f"cyclotomic target d={d} s={s}", got == want)


def build_gamma_rows(d, n0, p, xi):
    """Core Gamma vectors + J images (exact-Gamma objects, V3 code)."""
    r, _, s, R, P = G.int_word(d, n0, schedule_L3)
    T, _ = G.fstar_chronology(d)
    core, Jcore = [], []
    for i in range(1, len(T) - 1):
        Gam, _, _ = G.centered_gamma(R, P, T[i], T[i + 1], xi, p)
        v = G.reduce_qr(Gam, p, r)
        core.append(v)
        Jcore.append(G.J_poly(dict(enumerate(v)), xi, p, r))
    return r, core, Jcore


# ---------- cyclotomic cross-check: arithmetic in Q[X]/(Phi_s) ----------

def _pmul(a, b):
    c = {}
    for e, v in a.items():
        for f, w in b.items():
            c[e + f] = c.get(e + f, 0) + v * w
    return {e: v for e, v in c.items() if v != 0}


def _psub(a, b):
    c = dict(a)
    for e, v in b.items():
        c[e] = c.get(e, 0) - v
        if c[e] == 0:
            del c[e]
    return c


def _pdivmod(a, b):
    """Exact long division (requires exact divisibility)."""
    a = dict(a)
    db = max(b)
    lb = b[db]
    q = {}
    while a and max(a) >= db:
        da = max(a)
        coef, rem = divmod(a[da], lb)
        assert rem == 0, "inexact cyclotomic division"
        t = da - db
        q[t] = q.get(t, 0) + coef
        for e, v in b.items():
            a[e + t] = a.get(e + t, 0) - coef * v
            if a[e + t] == 0:
                del a[e + t]
    assert not a, "nonzero remainder in cyclotomic division"
    return q


def _mobius(n):
    p, i, sq = 2, 0, False
    nn = n
    while p * p <= nn:
        if nn % p == 0:
            i += 1
            nn //= p
            if nn % p == 0:
                return 0
        p += 1 if p == 2 else 2
    if nn > 1:
        i += 1
    return -1 if i % 2 else 1


def _divisors(n):
    ds = set()
    i = 1
    while i * i <= n:
        if n % i == 0:
            ds.add(i)
            ds.add(n // i)
        i += 1
    return sorted(ds)


def cyclo_phi(s):
    """Phi_s as {exp: int} via Moebius product formula."""
    from math import gcd  # noqa: F401 (documents integer nature)
    num, den = {0: 1}, {0: 1}
    for d in _divisors(s):
        mu = _mobius(s // d)
        term = {d: 1, 0: -1}  # x^d - 1
        if mu == 1:
            num = _pmul(num, term)
        elif mu == -1:
            den = _pmul(den, term)
    return _pdivmod(num, den)


class Cyclo:
    """Field Q(zeta_s) = Q[X]/(Phi_s); elements = Fraction lists length m."""

    def __init__(self, s):
        from fractions import Fraction
        self.s = s
        self.phi = cyclo_phi(s)
        self.m = max(self.phi)
        assert self.phi[self.m] == 1
        self.Fraction = Fraction

    def one(self):
        return [self.Fraction(1)] + [self.Fraction(0)] * (self.m - 1)

    def gen(self, k):
        """zeta^k reduced mod Phi_s (k >= 0)."""
        from fractions import Fraction
        poly = {k: Fraction(1)}
        return self._red(poly)

    def _red(self, poly):
        F = self.Fraction
        a = {e: F(v) for e, v in poly.items() if F(v) != 0}
        m = self.m
        lc = F(self.phi[m])
        while a and max(a) >= m:
            da = max(a)
            coef = a.pop(da) / lc
            t = da - m
            for e, v in self.phi.items():
                if e == m:
                    continue
                a[e + t] = a.get(e + t, F(0)) - coef * F(v)
                if a[e + t] == 0:
                    del a[e + t]
        out = [F(0)] * m
        for e, v in a.items():
            out[e] = v
        return out

    def add(self, a, b):
        return [(x + y) for x, y in zip(a, b)]

    def neg(self, a):
        return [-x for x in a]

    def mul(self, a, b):
        F = self.Fraction
        poly = {}
        for i, x in enumerate(a):
            if x == 0:
                continue
            for j, y in enumerate(b):
                if y == 0:
                    continue
                poly[i + j] = poly.get(i + j, F(0)) + x * y
        return self._red(poly)

    def _fdivmod(self, a, b):
        F = self.Fraction
        a = {e: F(v) for e, v in a.items() if F(v) != 0}
        b = {e: F(v) for e, v in b.items() if F(v) != 0}
        db = max(b)
        lb = b[db]
        q = {}
        while a and max(a) >= db:
            da = max(a)
            coef = a.pop(da) / lb
            t = da - db
            q[t] = q.get(t, F(0)) + coef
            for e, v in b.items():
                if e == db:
                    continue  # cancels the popped leading term by construction
                a[e + t] = a.get(e + t, F(0)) - coef * v
                if a[e + t] == 0:
                    del a[e + t]
        return q, a

    def inv(self, a):
        """Extended Euclid: a^-1 mod Phi_s."""
        F = self.Fraction
        assert any(x != 0 for x in a), "inverse of zero"
        pa = {i: x for i, x in enumerate(a) if x != 0}
        pb = {e: F(v) for e, v in self.phi.items()}
        r_prev, r = pb, pa
        s_prev, s = {}, {0: F(1)}
        while r:
            q, rem = self._fdivmod(r_prev, r)
            r_prev, r = r, rem
            sq = {}
            for e, v in q.items():
                for f, w in s.items():
                    sq[e + f] = sq.get(e + f, F(0)) + v * w
            s_prev, s = s, {e: s_prev.get(e, F(0)) - sq.get(e, F(0))
                            for e in set(s_prev) | set(sq)}
            s = {e: v for e, v in s.items() if v != 0}
        assert len(r_prev) == 1 and 0 in r_prev, "zero divisor?"
        c = r_prev[0]
        return self._red({e: v / c for e, v in s_prev.items()})

    def rank(self, rows):
        M = [list(r) for r in rows]
        m = len(M)
        n = len(M[0]) if m else 0
        z = [self.Fraction(0)] * self.m
        rk = 0
        for c in range(n):
            piv = next((i for i in range(rk, m)
                        if any(x != 0 for x in M[i][c])), None)
            if piv is None:
                continue
            M[rk], M[piv] = M[piv], M[rk]
            inv = self.inv(M[rk][c])
            M[rk] = [self.mul(elt, inv) for elt in M[rk]]
            for i in range(m):
                if i != rk and any(x != 0 for x in M[i][c]):
                    f = M[i][c]
                    M[i] = [self.add(a, self.neg(self.mul(f, b)))
                            for a, b in zip(M[i], M[rk])]
            rk += 1
        return rk

    def _lift(self, x):
        return [x] + [self.Fraction(0)] * (self.m - 1)

    def selftest(self):
        import random
        z = self.gen(1)
        assert self.mul(z, z) != self.one() or self.s == 1
        pw, one = self.one(), self.one()
        for _ in range(self.s):
            pw = self.mul(pw, z)
        assert pw == one, "zeta^s != 1"
        pw = self.one()
        for k in range(1, self.s):
            pw = self.mul(pw, z)
            if k < self.s:
                pass
        assert self.gen(0) == one
        random.seed(7)
        for _ in range(6):
            a = [self.Fraction(random.randint(-5, 5))
                 for _ in range(self.m)]
            if all(x == 0 for x in a):
                continue
            assert self.mul(a, self.inv(a)) == one, "inverse law fails"
        return True


def cyclo_gamma_rows(d, n0, s, schedule_L3, full=False):
    """Gamma vectors over Q(zeta_s): weight exponents mod s.

    Returns (r, rows) with rows = core (H-2) or full (H-1, +b_in) vectors
    as lists of Cyclo field elements. F = Cyclo(s) built by caller? No:
    builds its own field; returns (field, rows).
    """
    F = Cyclo(s)
    r, n, e, U, B, FF, Fs, g = schedule_L3(d, n0)
    R, P, svec = [{0: 1}], [0], [n + g[k] for k in range(r)]
    for sk in svec:
        sh = {ee + sk: v for ee, v in R[-1].items()}
        nxt = dict(sh)
        nxt[0] = nxt.get(0, 0) + 1
        R.append(nxt)
        P.append(P[-1] + sk)
    from fractions import Fraction
    import q195_exact_gamma as _G
    T, _ = _G.fstar_chronology(d)
    ivs = [(T[0], T[1])] + [(T[i], T[i + 1]) for i in range(1, len(T) - 1)]
    if not full:
        ivs = ivs[1:]
    rows = []
    for (a, b) in ivs:
        acc = {}
        for h in range(a + 1, b + 1):
            eh = (P[b] - P[h]) % s
            for ee, vv in R[h].items():
                q_, rem = divmod(ee, r)
                sgn = -1 if q_ % 2 else 1
                acc.setdefault(rem, {})
                acc[rem][eh] = acc[rem].get(eh, 0) + sgn * vv
        cexp = {}
        for h in range(a + 1, b + 1):
            eh = (P[b] - P[h]) % s
            cexp[eh] = cexp.get(eh, 0) + 1
        row = []
        for rem in range(r):
            d_ = dict(acc.get(rem, {}))
            if rem == 0:
                for k, v in cexp.items():
                    d_[k] = d_.get(k, 0) - Fraction(v, 2)
            poly = {k: Fraction(v) for k, v in d_.items() if Fraction(v) != 0}
            row.append(F._red(poly))
        rows.append(row)
    return F, rows


def cyclo_J(rows, F, s, r):
    """J on exponent-form rows: J(ck zk x^h) = -ck z^{k+kh} x^{r-h}."""
    out = []
    for row in rows:
        nrow = [[F.Fraction(0)] * F.m for _ in range(r)]
        for h, coeff in enumerate(row):
            if all(x == 0 for x in coeff):
                continue
            if h == 0:
                nrow[0] = F.add(nrow[0], coeff)
            else:
                # J(c z^k x^h) = -c z^{k+h} x^{r-h}: shift is +h.
                zh = F.gen(h % s)
                for k, ck in enumerate(coeff):
                    if ck == 0:
                        continue
                    base = F.mul(F.gen(k), zh)
                    term = F.mul([ck if i == 0 else F.Fraction(0)
                                  for i in range(F.m)], base)
                    term = F.neg(term)
                    nrow[(r - h) % r] = F.add(nrow[(r - h) % r], term)
        out.append(nrow)
    return out


if __name__ == "__main__":
    main()
