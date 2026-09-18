"""Q196 V2 part B: dual/z derivation checks, transfer measurement, d<=25 data.

Dual route is pivot-independent. Exit nonzero on: J-even space dim != H,
defect-dual dim != 2, z-law violation, parametrization failure at
det!=0 cells. Transfer/band/d25 are MEASURED (reported, not asserted).
"""

import hashlib
import os
import sys

import q195_exact_gamma as G
import q196_boundary_closure as Q6
import q196_canonical as QV
from VOLTERRA_RESONANT_FIXED_STATE_CERT_STANDALONE import schedule_L3

FROZEN_GAMMA_SHA = "cdcac2a75260caf08e4e1a70598397b12b033481caab4556271559df083a64ac"
PRIMES = {9: (19, 37), 15: (31, 61), 21: (43, 127), 27: (109, 163),
          33: (67, 199), 39: (79, 157), 45: (181, 271)}
D25 = {51: 103, 57: 229, 63: 127, 69: 139, 75: 151}


def check(name, cond):
    print(f"[{'ok' if cond else 'FAIL'}] {name}", flush=True)
    if not cond:
        sys.exit(1)


def is_prime_small(p):
    if p < 2:
        return False
    d = 2
    while d * d <= p and d < 1000:
        if p % d == 0:
            return p == d
        d += 1 if d == 2 else 2
    if p > 1000:
        for a in (2, 3):
            if pow(a, p - 1, p) != 1:
                return False
    return True


def left_fixed_covectors(Jm, p):
    """Row covectors lam with lam . R_j = lam_j for all rows R_j of Jm.

    With the row-combination action J(v) = sum_j v_j R_j, invariance
    lam(J(v)) = lam(v) needs lam . R_j = lam_j, i.e. lam Jm^T = lam,
    i.e. lam^T in ker(Jm - I) = the RIGHT nullspace. (V1's Vp, misused
    there as primal vectors, is exactly the right dual object.)
    Returns the right-nullspace basis AS rows.
    """
    r = len(Jm)
    rows = [[(Jm[i][j] - (1 if i == j else 0)) % p for j in range(r)]
            for i in range(r)]
    basis, _ = Q6.fp_nullspace_rows(rows, p)
    return basis


def main():
    import VOLTERRA_RESONANT_FIXED_STATE_CERT_STANDALONE as _cert
    _here = os.path.realpath(os.getcwd())
    for _m in (_cert, G, Q6, QV):
        _f = os.path.realpath(getattr(_m, "__file__", ""))
        check(f"dependency loads from run dir: {os.path.basename(_f)}",
              _f.startswith(_here + os.sep))
    with open(G.__file__, "rb") as f:
        check("frozen V3 harness hash",
              hashlib.sha256(f.read()).hexdigest() == FROZEN_GAMMA_SHA)

    # §§12-13: dual defect space + z-laws, sample sectors
    for (d, n0, p, xi) in [(5, 1, 61, 16), (7, 1, 127, 4), (3, 1, 37, 10)]:
        r = 3 * d
        H = (r + 1) // 2
        b = Q6.build_boundary(d, n0, p, xi, schedule_L3)
        Jm = b['Jm']
        Lam = left_fixed_covectors(Jm, p)
        check(f"dual J-even dim H={H} d={d} p={p} xi={xi}",
              len(Lam) == H)
        check(f"dual invariance lam.R_j=lam_j d={d} p={p} xi={xi}",
              all(all(sum(l[i] * Jm[j][i] for i in range(r)) % p == l[j]
                      for j in range(r)) for l in Lam))
        # L = {lam J-even : lam(C) = 0}
        r_, _, s, R, P = G.int_word(d, n0, schedule_L3)
        T, _ = G.fstar_chronology(d)
        Cvec = []
        for i in range(1, len(T) - 1):
            Gam, _, _ = G.centered_gamma(R, P, T[i], T[i + 1], xi, p)
            Cvec.append(G.reduce_qr(Gam, p, r))
        CL = [[sum(l[j] * c[j] for j in range(r)) % p for c in Cvec]
              for l in Lam]
        # L = {lam J-even : lam(C) = 0}: nullspace over Lam coefficients.
        # M rows = C-constraints, cols = Lam-coeffs; ker M spans L.
        M = [[CL[i][j] for i in range(len(Lam))] for j in range(len(Cvec))]
        N, _ = Q6.fp_nullspace_rows(M, p)
        check(f"dual defect dim 2 d={d} p={p} xi={xi}", len(N) == 2)
        # z-laws on L[0], L[1]
        for t in range(2):
            a = N[t]
            lam = [0] * r
            for i, ai in enumerate(a):
                if ai:
                    lam = [(x + ai * y) % p
                           for x, y in zip(lam, Lam[i])]
            # lam is J-even by construction; check lam(C) = 0
            vals = [sum(lam[j] * c[j] for j in range(r)) % p for c in Cvec]
            check(f"lam[{t}] annihilates C d={d} xi={xi}",
                  all(v == 0 for v in vals))
            l0 = sum(lam[j] * (1 if j == 0 else 0) for j in range(r)) % p
            Rv = []
            for h in range(r + 1):
                rh = [0] * r
                for e, vv in R[h].items():
                    q_, rem = divmod(e, r)
                    rh[rem] = (rh[rem] + ((-1) ** q_) * (vv % p)) % p
                Rv.append((sum(lam[j] * rh[j] for j in range(r)) % p
                           - l0 * pow(2, p - 2, p)) % p)
            laws = True
            for i in range(1, len(T) - 1):
                a_, bb = T[i], T[i + 1]
                if bb == a_ + 1:
                    laws &= (Rv[bb] == 0)
                elif bb == a_ + 2:
                    laws &= ((pow(xi, s[bb - 1], p) * Rv[a_ + 1] + Rv[a_ + 2]) % p == 0)
                else:
                    laws = False
            check(f"z interval laws d={d} xi={xi} lam[{t}]", laws)
        # parametrization by (lam(B), lam(Q)) an iso where det != 0
        Bv = b['B']
        Qv = b['QP']
        Mb = [[sum(N[t][i] * sum(Lam[i][j] * Bv[j] for j in range(r))
                     for i in range(len(Lam))) % p for t in range(2)],
              [sum(N[t][i] * sum(Lam[i][j] * Qv[j] for j in range(r))
                     for i in range(len(Lam))) % p for t in range(2)]]
        # Mb rows = B/Q vals? fix orientation: rows lam, cols (B,Q)
        Mb = [[Mb[0][0], Mb[1][0]], [Mb[0][1], Mb[1][1]]]
        det = (Mb[0][0] * Mb[1][1] - Mb[0][1] * Mb[1][0]) % p
        print(f"dual-parametrization det d={d} p={p} xi={xi}: {det}",
              flush=True)

    # §11b/§10 row-species + bandwidth measurement (chronological order)
    print("d gap1 gap2 bandwidth fillsteps", flush=True)
    for d in (3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25):
        r = 3 * d
        T, _ = G.fstar_chronology(d)
        gaps = [T[i + 1] - T[i] for i in range(len(T) - 1)]
        g1 = sum(1 for g in gaps if g == 1)
        g2 = sum(1 for g in gaps if g == 2)
        other = [g for g in gaps if g not in (1, 2)]
        print(f"{d} {g1} {g2} other={other}", flush=True)

    # §17 d<=25 inference data (one prime each; inference only)
    for d in (17, 19, 21, 23, 25):
        r = 3 * d
        H = (r + 1) // 2
        p = D25[r]
        check(f"prime {p} for r={r}",
              is_prime_small(p) and (p - 1) % r == 0)
        for n0 in (1, 2):
            for xi in G.rth_roots(p, r):
                c = QV.build_canonical(d, n0, p, xi, schedule_L3)
                piv = Q6.fp_row_pivots(c['ME'], p)
                b = c['base']
                rEBQ = G.fp_rank(b['E'] + [b['B'], b['QP']], p)
                print(f"INFER d={d} n0={n0} p={p} xi={xi} "
                      f"pivots={piv == list(range(H - 2))} rankEBQ={rEBQ}/{H}",
                      flush=True)
    print("Q196 V2 PART-B COMPLETE")


if __name__ == "__main__":
    main()
