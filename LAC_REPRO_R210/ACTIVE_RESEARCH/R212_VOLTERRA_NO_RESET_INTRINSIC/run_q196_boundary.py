"""Q196 boundary-closure driver V1 (faithful reconstruction of pending work).

NOT a recovered UnionAlpha result. Reuses frozen V3 code (hash-checked).
Outcomes RECORDED verbatim (PASS/FAIL rows); harness-identity failures
(J^2, V dims, P formula) exit nonzero. No floating point.
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


def det2(M, p):
    return (M[0][0] * M[1][1] - M[0][1] * M[1][0]) % p


def main():
    import VOLTERRA_RESONANT_FIXED_STATE_CERT_STANDALONE as _cert
    _here = os.path.realpath(os.getcwd())
    for _m in (_cert, G, Q6):
        _f = os.path.realpath(getattr(_m, "__file__", ""))
        check(f"dependency loads from run dir: {os.path.basename(_f)}",
              _f.startswith(_here + os.sep))
    with open(G.__file__, "rb") as f:
        check("frozen V3 harness hash", hashlib.sha256(f.read()).hexdigest()
              == FROZEN_GAMMA_SHA)

    # P-formula cross-check (§6) for every tested (d, n0)
    for n0 in (1, 2):
        for d in (3, 5, 7, 9, 11, 13, 15):
            r, n, s, R, P = G.int_word(d, n0, schedule_L3)
            form = {0: 1}
            for j in range(d):
                e = n + j * (n + 1)
                form[e] = form.get(e, 0) + 1
            check(f"P formula d={d} n0={n0}",
                  {e: v for e, v in R[d].items()} == form)

    # Full sector grid
    rows = []
    for n0 in (1, 2):
        for d in (3, 5, 7, 9, 11, 13, 15):
            r = 3 * d
            H = (r + 1) // 2
            for p in PRIMES[r]:
                for xi in G.rth_roots(p, r):
                    b = Q6.build_boundary(d, n0, p, xi, schedule_L3)
                    check(f"J^2 d={d} n0={n0} p={p} xi={xi}",
                          all(Q6.apply_Jmat(
                              b['Jm'], Q6.apply_Jmat(
                                  b['Jm'],
                                  [1 if i == h else 0 for i in range(r)],
                                  p), p)
                              == [1 if i == h else 0 for i in range(r)]
                              for h in range(r)))
                    rv = [(h * 7 + 3) % p for h in range(r)]
                    check(f"Jmat==Jpoly d={d} n0={n0} p={p} xi={xi}",
                          Q6.apply_Jmat(b['Jm'], rv, p) == G.J_poly(
                              dict(enumerate(rv)), xi, p, r))
                    dimV = len(b['Vp'])
                    check(f"dimV+={H} d={d} n0={n0} p={p} xi={xi}",
                          dimV == H)
                    E, B, QP = b['E'], b['B'], b['QP']
                    rE = G.fp_rank(E, p)
                    rEB = G.fp_rank(E + [B], p)
                    rEQ = G.fp_rank(E + [QP], p)
                    rEBQ = G.fp_rank(E + [B, QP], p)
                    defect = dimV - rE
                    # B, QP in V+ ?
                    JB = Q6.apply_Jmat(b['Jm'], B, p)
                    JQ = Q6.apply_Jmat(b['Jm'], QP, p)
                    inV = (JB == [x % p for x in B]
                           and JQ == [x % p for x in QP])
                    # annihilator basis of E inside dual of V+
                    Ec = [b['coords'](y) for y in E]
                    null, _ = Q6.fp_nullspace_rows(Ec, p)
                    detv, lam = None, None
                    if len(null) == 2 and rEBQ == rE + 2:
                        lam = null
                        Bc, Qc = b['coords'](B), b['coords'](QP)
                        M = [[sum(l[i] * Bc[i] for i in range(H)) % p
                              for l in lam],
                             [sum(l[i] * Qc[i] for i in range(H)) % p
                              for l in lam]]
                        # M rows = lambdas, cols = (B, QP)
                        M = [[M[0][0], M[1][0]], [M[0][1], M[1][1]]]
                        detv = det2(
                            [[M[0][0], M[0][1]], [M[1][0], M[1][1]]], p)
                    # b_out diagnostic (§14)
                    Bout = b['Bout']
                    rEBO = G.fp_rank(E + [B, QP, Bout], p)
                    rEO = G.fp_rank(E + [Bout], p)
                    rows.append((d, n0, p, xi, dimV, rE, rEB, rEQ,
                                 rEBQ, defect, inV, detv, rEBO, rEO))
    with open("Q196_FINITE_TABLE.txt", "w") as f:
        f.write("# dim V+ | rank E=(I+J)C | rank(E+B) | rank(E+Q_P) | "
                "rank(E+B+Q_P) | defect dimension | boundary determinant\n")
        for row in rows:
            (d, n0, p, xi, dimV, rE, rEB, rEQ, rEBQ, defect, inV,
             detv, rEBO, rEO) = row
            f.write(f"d={d} n0={n0} p={p} xi={xi} dimV+={dimV} "
                    f"rankE={rE} rankEB={rEB} rankEQ={rEQ} "
                    f"rankEBQ={rEBQ} defect={defect} inV+={inV} "
                    f"det={'-' if detv is None else detv} "
                    f"rankEBO={rEBO} rankEO={rEO}\n")
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

    def divisors(n):
        ds = set()
        i = 1
        while i * i <= n:
            if n % i == 0:
                ds.add(i)
                ds.add(n // i)
            i += 1
        return sorted(ds)

    # char-0 certification (§12, CORRECTED criterion): per cyclotomic order
    # s|r, one passing exact-order-s cell certifies the sector (V4 lemma).
    # Isolated modular zeros with passing same-order witnesses are bad
    # reductions, recorded — not hidden, not promoted.
    cert = True
    for n0 in (1, 2):
        for d in (3, 5, 7, 9, 11, 13, 15):
            r = 3 * d
            H = (r + 1) // 2
            for s in divisors(r):
                wit = [row for row in rows if row[0] == d and row[1] == n0
                       and order_in_r(row[3], r, row[2]) == s
                       and row[5] == H - 2 and row[8] == H
                       and row[11] not in (None, 0)]
                okcell = len(wit) > 0
                cert &= okcell
                if not okcell:
                    print(f"Q196 NO GOOD REDUCTION d={d} n0={n0} "
                          f"order {s}", flush=True)
    print("Q196 per-order char-0 coverage: "
          f"{'COMPLETE' if cert else 'INCOMPLETE'}", flush=True)
    nq = sum(1 for row in rows
             if row[5] == (3 * row[0] + 1) // 2 - 2 and row[8]
             == (3 * row[0] + 1) // 2 and row[11] not in (None, 0))
    print(f"Q196 cells with defect 2 + full span + nonzero det: "
          f"{nq}/{len(rows)}", flush=True)
    if not cert:
        print("Q196 FINITE RECONSTRUCTION: UNCOVERED SECTORS — NO CLAIM",
              flush=True)
        sys.exit(1)
    print("Q196 BOUNDARY RECONSTRUCTION: ALL SECTORS COVERED (finite)")


if __name__ == "__main__":
    main()
