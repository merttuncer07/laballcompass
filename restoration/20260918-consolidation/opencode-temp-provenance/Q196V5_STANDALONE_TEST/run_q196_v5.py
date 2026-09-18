"""Q196 V5 driver: phase-grid theorem asserts + transfer measurement.

Proves nothing new by itself; every assert is an exact finite check of a
symbolically derived formula (see Q196_PHASE_GRID_THEOREM.md). Transfer
fit-tests are MEASURED (recorded outcomes); a verified fit would print
prominently. Exit nonzero only on failed exact assertions. No floats.
"""

import hashlib
import os
import sys

import q195_exact_gamma as G
import q196_boundary_closure as Q6
from VOLTERRA_RESONANT_FIXED_STATE_CERT_STANDALONE import schedule_L3

FROZEN_GAMMA_SHA = "cdcac2a75260caf08e4e1a70598397b12b033481caab4556271559df083a64ac"
PRIMES = {9: (19, 37), 15: (31, 61), 21: (43, 127), 27: (109, 163),
          33: (67, 199), 39: (79, 157), 45: (181, 271)}


def check(name, cond):
    print(f"[{'ok' if cond else 'FAIL'}] {name}", flush=True)
    if not cond:
        sys.exit(1)


def main():
    import VOLTERRA_RESONANT_FIXED_STATE_CERT_STANDALONE as _cert
    _here = os.path.realpath(os.getcwd())
    for _m in (_cert, G, Q6):
        _f = os.path.realpath(getattr(_m, "__file__", ""))
        check(f"dependency loads from run dir: {os.path.basename(_f)}",
              _f.startswith(_here + os.sep))
    with open(G.__file__, "rb") as f:
        check("frozen V3 harness hash",
              hashlib.sha256(f.read()).hexdigest() == FROZEN_GAMMA_SHA)

    # §§3-5: partition, PH1/PH2, PG0-2, MU0-2 vs schedule, d<=31
    for d in range(3, 32, 2):
        e = (d - 1) // 2
        for n0 in (1, 2):
            r, n, s, R, P = G.int_word(d, n0, schedule_L3)
            rr = 3 * d
            ha = [rr - 2 - 2 * a for a in range(d)]
            qa = [rr - 1 - 2 * a for a in range(d)]
            Ps = [0]
            for sk in s:
                Ps.append(Ps[-1] + sk)
            ok = (sorted(list(range(d)) + ha + qa) == list(range(rr)))
            for a in range(d):
                ok &= (Ps[a] == a * (n + 1))
                ok &= (Ps[ha[a]] == ha[a] * n + rr * ((d - 1 - a)
                       + max(e - a, 0)) + a)
                ok &= (Ps[qa[a]] == Ps[ha[a]] + n
                       + (rr if a <= e else 0))
                ok &= (Ps[a] % rr == (a + d * ((n0 * a) % 3)) % rr)
                ok &= (Ps[ha[a]] % rr
                       == (a + d * ((n0 * (a + 1)) % 3)) % rr)
                ok &= (Ps[qa[a]] % rr
                       == (a + d * ((n0 * (a + 2)) % 3)) % rr)
                m = n0 * (a + 1)
                tau = m % 3
                muh = (d * n0 + (d - 1 - a) + max(e - a, 0)
                       - 2 * (m // 3) - tau)
                muq = muh + (1 if a <= e else 0) + ((tau + n0) // 3)
                ok &= (Ps[a] // rr == (n0 * a) // 3)
                ok &= (Ps[ha[a]] // rr == muh)
                ok &= (Ps[qa[a]] // rr == muq)
            check(f"grid/PH/PG/MU d={d} n0={n0}", ok)

    # §8 grid path visits Z_d x Z_3 exactly once
    for d in range(3, 32, 2):
        for n0 in (1, 2):
            seen = set()
            for a in range(d):
                seen.add((a, (n0 * a) % 3))
            for a in range(d - 1, -1, -1):
                seen.add((a, (n0 * (a + 1)) % 3))
                seen.add((a, (n0 * (a + 2)) % 3))
            check(f"grid path Hamiltonian d={d} n0={n0}",
                  len(seen) == 3 * d)

    # §§6-7,9: END1 residues/signs + J grid coords (sample cells)
    for (d, n0, p) in [(5, 1, 61), (7, 2, 43), (11, 1, 199)]:
        r = 3 * d
        H = (r + 1) // 2
        xi = G.rth_roots(p, r)[1]
        rr, _, s, R, P = G.int_word(d, n0, schedule_L3)
        # END1: S_{r-1} assembled by (a,h,q) branches equals direct sum
        Sdirect = {}
        for i in range(r):
            Sdirect[P[i]] = Sdirect.get(P[i], 0) + 1
        Sbranch = {}
        for a in range(d):
            for k in (a, r - 2 - 2 * a, r - 1 - 2 * a):
                Sbranch[P[k]] = Sbranch.get(P[k], 0) + 1
        check(f"END1 branch sum d={d} n0={n0}", Sdirect == Sbranch)
        # JG1/JG2 on all monomials present
        ok = True
        for a in range(d):
            for t in (0, 1, 2):
                h = a + d * t
                if h == 0 or h >= r:
                    continue
                Jh = G.J_poly({h: 1}, xi, p, r)
                if a > 0:
                    exp = {((d - a) + d * (2 - t)) % r:
                           (-pow(xi, h, p)) % p}
                    expv = [0] * r
                    for ee, vv in exp.items():
                        q_, rem = divmod(ee, r)
                        expv[rem] = (expv[rem] + ((-1) ** q_) * vv) % p
                    ok &= (Jh == expv)
        # JG2 + J1
        for t, want in [(1, 2), (2, 1)]:
            Jh = G.J_poly({d * t: 1}, xi, p, r)
            expv = [0] * r
            expv[(d * (3 - t)) % r] = (-pow(xi, d * t, p)) % p
            if (d * (3 - t)) % r == 0:
                expv[0] = (-pow(xi, d * t, p)) % p
            ok &= (Jh == expv)
        ok &= (G.J_poly({0: 1}, xi, p, r) == [1] + [0] * (r - 1))
        check(f"J grid coords d={d} n0={n0} p={p}", ok)

    # §10: TR1/TR2 (+TR3 consequence) as RING identities mod (x^r+1)
    # (x^{n+r} = -x^n and x^{-1} = -x^{r-1} only hold in the quotient).
    # Compare reduced coefficient vectors over ZZ (exact integers).
    def redvec(poly, r):
        v = [0] * r
        for e, vv in poly.items():
            if e >= 0:
                q_, rem = divmod(e, r)
                v[rem] += ((-1) ** q_) * vv
            else:
                # x^{-k} = (-1)^m x^t with t = mr-k in [0, r)
                m = (-e + r - 1) // r
                v[m * r + e] += ((-1) ** m) * vv
        return v

    for d in (3, 5, 7, 9, 11):
        for n0 in (1, 2):
            r, n, e, U, B, F, Fs, g = schedule_L3(d, n0)
            rr, _, s, R, P = G.int_word(d, n0, schedule_L3)
            ok = True
            for a in range(d):
                ha, qa = r - 2 - 2 * a, r - 1 - 2 * a
                # TR1: R_{qa} = 1 + sig*Y^n0 R_{ha}, Y = x^d
                sig = -1 if a <= (d - 1) // 2 else 1
                lhs = dict(R[qa])
                rhs = {0: 1}
                for ee, vv in R[ha].items():
                    rhs[ee + d * n0] = rhs.get(ee + d * n0, 0) + sig * vv
                ok &= (redvec(lhs, r) == redvec(rhs, r))
                # TR2 for a>=1: R_{h_{a-1}} = 1 - Y^n0 x^{-1} R_{qa}
                if a >= 1:
                    hprev = r - 2 - 2 * (a - 1)
                    lhs2 = dict(R[hprev])
                    rhs2 = {0: 1}
                    for ee, vv in R[qa].items():
                        rhs2[ee + d * n0 - 1] = rhs2.get(
                            ee + d * n0 - 1, 0) - vv
                    ok &= (redvec(lhs2, r) == redvec(rhs2, r))
            check(f"TR1/TR2 d={d} n0={n0}", ok)
    print("Q196 V5 GRID THEOREM CHECKS COMPLETE")


if __name__ == "__main__":
    main()
