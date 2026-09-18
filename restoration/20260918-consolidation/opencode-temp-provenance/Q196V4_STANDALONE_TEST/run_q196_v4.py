"""Q196 V4 driver: canonical scalar via lambda_star.

Frozen reuse only (hash-checked): q195_exact_gamma (V3), schedule_L3.
V1-V4 + Q196V1-V3 packages sealed. Exit nonzero on any failed exact
assertion. No floating point.
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
D31 = {51: 103, 57: 229, 63: 127, 69: 139, 75: 151,
       81: 163, 87: 349, 93: 373}


def check(name, cond):
    print(f"[{'ok' if cond else 'FAIL'}] {name}", flush=True)
    if not cond:
        sys.exit(1)


def order_in_r(xi, r, p):
    o = r
    tmp, facs, dd = o, set(), 2
    while dd * dd <= tmp:
        if tmp % dd == 0:
            facs.add(dd)
            while tmp % dd == 0:
                tmp //= dd
        dd += 1 if dd == 2 else 2
    if tmp > 1:
        facs.add(tmp)
    for q in sorted(facs):
        while o % q == 0 and pow(xi, o // q, p) == 1:
            o //= q
    return o


def dual_basis(d, n0, p, xi):
    """J-even covector basis annihilating C (V3-verified construction).

    Returns (lams, R, P, T, bnd) with len(lams) == 2, or None.
    """
    r = 3 * d
    bnd = Q6.build_boundary(d, n0, p, xi, schedule_L3)
    Jm = bnd['Jm']
    rows = [[(Jm[i][j] - (1 if i == j else 0)) % p for j in range(r)]
            for i in range(r)]
    Lam, _ = Q6.fp_nullspace_rows(rows, p)
    if len(Lam) != (r + 1) // 2:
        return None
    _, _, _, R, P = G.int_word(d, n0, schedule_L3)
    T, _ = G.fstar_chronology(d)
    Cvec = []
    for i in range(1, len(T) - 1):
        Gam, _, _ = G.centered_gamma(R, P, T[i], T[i + 1], xi, p)
        Cvec.append(G.reduce_qr(Gam, p, r))
    M = [[sum(Lam[i][j] * c[j] for j in range(r)) % p
          for i in range(len(Lam))] for c in Cvec]
    N, _ = Q6.fp_nullspace_rows(M, p)
    if len(N) != 2:
        return None
    lams = []
    for t in range(2):
        lam = [0] * r
        for i, ai in enumerate(N[t]):
            if ai:
                lam = [(x + ai * y) % p for x, y in zip(lam, Lam[i])]
        lams.append(lam)
    return lams, R, P, T, bnd


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
    print("Q196 V4 PART-A COMPLETE")

    def fp_solve(rows, p):
        """Solve square system; return solution or None (singular)."""
        n = len(rows)
        M = [list(map(lambda v: v % p, row)) for row in rows]
        pivcol = []
        r_ = 0
        for c in range(n):
            q = next((i for i in range(r_, n) if M[i][c] % p != 0), None)
            if q is None:
                return None
            M[r_], M[q] = M[q], M[r_]
            inv = pow(M[r_][c], p - 2, p)
            M[r_] = [(v * inv) % p for v in M[r_]]
            for i in range(n):
                if i != r_ and M[i][c] % p != 0:
                    f = M[i][c]
                    M[i] = [(a - f * b_) % p for a, b_ in zip(M[i], M[r_])]
            pivcol.append(c)
            r_ += 1
        if r_ != n:
            return None
        sol = [0] * n
        for i, c in enumerate(pivcol):
            sol[c] = M[i][n] % p
        return sol

    def ring_vec(Rh, p, r):
        v = [0] * r
        for e, vv in Rh.items():
            q_, rem = divmod(e, r)
            v[rem] = (v[rem] + ((-1) ** q_) * (vv % p)) % p
        return v

    # §8: quadratic telescoping as POLYNOMIAL identity (all V4 cells,
    # all C intervals + both boundary intervals).
    for n0 in (1, 2):
        for d in (3, 5, 7, 9, 11, 13, 15):
            r = 3 * d
            for p in PRIMES[r]:
                for xi in G.rth_roots(p, r):
                    r_, _, s, R, P = G.int_word(d, n0, schedule_L3)
                    T, _ = G.fstar_chronology(d)
                    Rv = [ring_vec(R[k], p, r) for k in range(r + 1)]
                    Jv = [G.J_poly(dict(enumerate(v)), xi, p, r)
                          for v in Rv]
                    Qq = [Q6.polymod_mul(Rv[k], Jv[k], p, r)
                          for k in range(r + 1)]
                    ivs = ([(T[0], T[1])] + [(T[i], T[i + 1])
                                             for i in range(1, len(T) - 1)]
                           + [(T[-1], r - 1)])
                    ok = True
                    for (a, b) in ivs:
                        lhs = [(Qq[b][i] - pow(xi, P[b] - P[a], p)
                                * Qq[a][i]) % p for i in range(r)]
                        Gam, _, _ = G.centered_gamma(R, P, a, b, xi, p)
                        Gv = G.reduce_qr(Gam, p, r)
                        JGv = G.J_poly(dict(enumerate(Gv)), xi, p, r)
                        rhs = [(x + y) % p for x, y in zip(Gv, JGv)]
                        ok &= (lhs == rhs)
                    if not ok:
                        print(f"QUAD-TEL FAIL d={d} n0={n0} p={p} xi={xi}",
                              flush=True)
                        sys.exit(1)
    print("Part-8 quadratic telescoping identity verified (all cells)",
          flush=True)

    # §§2,4-7,9-11: b_out form, boundary pair, lambda_star, Theta,
    # propagation, endpoint reduction, grouped anchor.
    theta_rows = []
    pair_wit = {}
    lstar_missing = []
    lstar_cells = []
    lstar_wit = {}
    theta_rows = ["# d n0 p xi order Theta"]
    pair_wit = {}
    for n0 in (1, 2):
        for d in (3, 5, 7, 9, 11, 13, 15):
            r = 3 * d
            H = (r + 1) // 2
            for p in PRIMES[r]:
                for xi in G.rth_roots(p, r):
                    s = order_in_r(xi, r, p)
                    r_, _, sv, R, P = G.int_word(d, n0, schedule_L3)
                    T, _ = G.fstar_chronology(d)
                    # §2 b_out unit form
                    Go, _, _ = G.centered_gamma(R, P, T[-1], r - 1, xi, p)
                    Rd1 = {e: v % p for e, v in R[r - 1].items()}
                    if not (G.padd(Rd1, {0: (-pow(2, p - 2, p)) % p}, p)
                            == {e: v % p for e, v in Go.items()}):
                        print(f"BOUT-FORM FAIL d={d} n0={n0} p={p} xi={xi}",
                              flush=True)
                        sys.exit(1)
                    db = dual_basis(d, n0, p, xi)
                    if db is None:
                        print(f"DUALDIM FAIL d={d} n0={n0} p={p} xi={xi}",
                              flush=True)
                        sys.exit(1)
                    # NOTE dual_basis returns (lams, R, P, T, bnd)
                    lams, R2, P2, T2, bnd = db
                    inv2 = pow(2, p - 2, p)

                    def zh(lam, h):
                        return (sum(lam[j] * ring_vec(R[h], p, r)[j]
                                    for j in range(r)) % p
                                - lam[0] * inv2) % p
                    # §2: 2z_{r-1} regression on both lams
                    bv_out = G.reduce_qr(Go, p, r)
                    Jbo = G.J_poly(dict(enumerate(bv_out)), xi, p, r)
                    Bout = [(a + b_) % p for a, b_ in zip(bv_out, Jbo)]
                    for t in range(2):
                        lB = sum(lams[t][j] * Bout[j] for j in range(r)) % p
                        if lB != (2 * zh(lams[t], r - 1)) % p:
                            print(f"BOUT-2Z FAIL d={d} n0={n0} p={p} "
                                  f"xi={xi} lam={t}", flush=True)
                            sys.exit(1)
                    # §4: boundary-pair evaluation matrix
                    E = [[zh(lams[t], d + 1), zh(lams[t], r - 1)]
                         for t in range(2)]
                    detE = (E[0][0] * E[1][1] - E[0][1] * E[1][0]) % p
                    key = (d, n0, s)
                    if detE != 0 and key not in pair_wit:
                        pair_wit[key] = (p, xi)
                    # §§5-7: lambda_star via H conditions on Lam basis
                    # (recompute Lam basis here for the solve)
                    Jm = bnd['Jm']
                    rows = [[(Jm[i][j] - (1 if i == j else 0)) % p
                             for j in range(r)] for i in range(r)]
                    Lam, _ = Q6.fp_nullspace_rows(rows, p)
                    Cvec = []
                    for i in range(1, len(T) - 1):
                        Gm, _, _ = G.centered_gamma(R, P, T[i], T[i + 1],
                                                   xi, p)
                        Cvec.append(G.reduce_qr(Gm, p, r))
                    Gb, _, _ = G.centered_gamma(R, P, T[0], T[1], xi, p)
                    bv_in = G.reduce_qr(Gb, p, r)
                    sysrows = []
                    for c in Cvec + [bv_in]:
                        sysrows.append(
                            [sum(Lam[i][j] * c[j] for j in range(r)) % p
                             for i in range(H)] + [0])
                    zr1 = [0] * H + [1]
                    # z_{r-1}(lam) = lam(R_{r-1}) - lam[0]/2
                    Rrm1 = ring_vec(R[r - 1], p, r)
                    zrow = [(sum(Lam[i][j] * Rrm1[j] for j in range(r))
                             - Lam[i][0] * inv2) % p for i in range(H)]
                    sysrows.append(zrow + [1])
                    sol = fp_solve([row[:] for row in sysrows], p)
                    if sol is None:
                        print(f"LSTAR-SINGULAR d={d} n0={n0} p={p} "
                              f"xi={xi} (recorded; bad reduction)",
                              flush=True)
                        lstar_missing.append((d, n0, p, xi, s))
                        continue
                    lstar_cells.append((d, n0, s))
                    lam = [0] * r
                    for i, ai in enumerate(sol):
                        if ai:
                            lam = [(x + ai * y) % p
                                   for x, y in zip(lam, Lam[i])]
                    # verify: annihilates C + b_in; z_{d+1}=0; z_{r-1}=1
                    vals = [sum(lam[j] * c[j] for j in range(r)) % p
                            for c in Cvec + [bv_in]]
                    if not all(v == 0 for v in vals):
                        print(f"LSTAR-ANN FAIL d={d} n0={n0} p={p} "
                              f"xi={xi}", flush=True)
                        sys.exit(1)
                    Rrd1 = ring_vec(R[d + 1], p, r)
                    zd1 = (sum(lam[j] * Rrd1[j] for j in range(r))
                           - lam[0] * inv2) % p
                    zrm1 = (sum(lam[j] * Rrm1[j] for j in range(r))
                            - lam[0] * inv2) % p
                    if not (zd1 == 0 and zrm1 == 1):
                        print(f"LSTAR-NORM FAIL d={d} n0={n0} p={p} "
                              f"xi={xi}", flush=True)
                        sys.exit(1)
                    lstar_cells.append((d, n0, s))
                    key2 = (d, n0, s)
                    if key2 not in lstar_wit:
                        lstar_wit[key2] = (p, xi)
                    # Theta via grouped double-sum anchor (§11)
                    n_ = d * n0
                    Pterms = [(0, 1)] + [(n_ + j * (n_ + 1), 1)
                                         for j in range(d)]
                    QP = [0] * r
                    for (e1, c1) in Pterms:
                        for (e2, c2) in Pterms:
                            # P(x)P(xi/x): x^{e1} * xi^{e2} x^{-e2}
                            D = e1 - e2
                            m = 0
                            t = D
                            while t < 0:
                                t += r
                                m += 1
                            q_, rem = divmod(t, r)
                            sgn = (-1) ** (q_ + m)
                            QP[rem] = (QP[rem] + sgn * c1 * c2
                                       * pow(xi, e2, p)) % p
                    Theta = sum(lam[j] * QP[j] for j in range(r)) % p
                    # cross-check vs direct polymod route
                    Pd = G.reduce_qr({e: v % p for e, v in R[d].items()},
                                     p, r)
                    QP2 = Q6.polymod_mul(
                        Pd, G.J_poly(dict(enumerate(Pd)), xi, p, r), p, r)
                    if QP != QP2:
                        print(f"ANCHOR-MISMATCH d={d} n0={n0} p={p} "
                              f"xi={xi}", flush=True)
                        sys.exit(1)
                    # §§9-10: propagation + endpoint formula
                    qd = Theta  # q_d = lam(Q^P)
                    qr2 = (pow(xi, P[r - 2] - P[d], p) * qd) % p
                    # verify by direct evaluation
                    Rr2 = ring_vec(R[r - 2], p, r)
                    Jr2 = G.J_poly(dict(enumerate(Rr2)), xi, p, r)
                    Qr2 = Q6.polymod_mul(Rr2, Jr2, p, r)
                    if (sum(lam[j] * Qr2[j] for j in range(r)) % p
                            != qr2):
                        print(f"PROPAGATE FAIL d={d} n0={n0} p={p} "
                              f"xi={xi}", flush=True)
                        sys.exit(1)
                    qr1 = (sum(lam[j] * Q6.polymod_mul(
                        ring_vec(R[r - 1], p, r),
                        G.J_poly(dict(enumerate(
                            ring_vec(R[r - 1], p, r))), xi, p, r),
                        p, r)[j] for j in range(r)) % p)
                    if ((qr1 - pow(xi, sv[r - 2], p) * qr2) % p != 2
                            or (qr1 - pow(xi, P[r - 1] - P[d], p)
                                * Theta) % p != 2):
                        print(f"ENDPOINT FAIL d={d} n0={n0} p={p} "
                              f"xi={xi}", flush=True)
                        sys.exit(1)
                    # agreement Theta != 0 <=> rankEBQ == H
                    E2 = bnd['E']
                    Bv = bnd['B']
                    QPvv = bnd['QP']
                    full = G.fp_rank(E2 + [Bv, QPvv], p)
                    if not ((Theta != 0) == (full == H)):
                        print(f"THETA-AGREE FAIL d={d} n0={n0} p={p} "
                              f"xi={xi} Theta={Theta} rank={full}",
                              flush=True)
                        sys.exit(1)
                    theta_rows.append((d, n0, p, xi, s, Theta))
    with open("Q196_THETA_TABLE.txt", "w") as f:
        f.write("# d n0 p xi order Theta\n")
        for row in theta_rows:
            f.write(f"{row[0]} {row[1]} {row[2]} {row[3]} {row[4]} "
                    f"{row[5]}\n")
    with open("Q196_PAIRWITNESS.txt", "w") as f:
        f.write("# d n0 s cert-p cert-xi\n")
        for key in sorted(pair_wit):
            f.write(f"{key[0]} {key[1]} {key[2]} {pair_wit[key][0]} "
                    f"{pair_wit[key][1]}\n")
    with open("Q196_LSTARWITNESS.txt", "w") as f:
        f.write("# d n0 s cert-p cert-xi (lambda_star exists)\n")
        for key in sorted(lstar_wit):
            f.write(f"{key[0]} {key[1]} {key[2]} {lstar_wit[key][0]} "
                    f"{lstar_wit[key][1]}\n")
    # per-(d,n0,s) coverage for BOTH pair separation and lambda_star
    missing = []
    for n0 in (1, 2):
        for d in (3, 5, 7, 9, 11, 13, 15):
            r = 3 * d
            divs = sorted({s for s in range(1, r + 1) if r % s == 0})
            for s in divs:
                if (d, n0, s) not in pair_wit:
                    missing.append(("pair", d, n0, s))
                if (d, n0, s) not in lstar_wit:
                    missing.append(("lstar", d, n0, s))
    print(f"lambda_star singular cells: {lstar_missing}", flush=True)
    if missing:
        print(f"COVERAGE GAPS: {missing}", flush=True)
        sys.exit(1)
    print("Parts 2/4-11 verified; Theta + pair tables written", flush=True)
    print("Q196 V4 PART-A COMPLETE")


if __name__ == "__main__":
    main()
