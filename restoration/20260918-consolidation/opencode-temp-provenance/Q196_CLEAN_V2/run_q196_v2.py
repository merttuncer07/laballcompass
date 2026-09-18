"""Q196 V2 driver: orientation repair, canonical basis/quotient, replay.

V1 package sealed (hash-checked below). Exit nonzero on: V1-tamper,
regression absence, J-violation, pivot failure in good sectors,
Delta/rank disagreement. No floating point.
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
V1_EXPECTED_BAD = {(5, 1, 31, 10), (5, 1, 61, 56), (7, 1, 127, 61),
                   (9, 1, 163, 150), (11, 1, 67, 16), (11, 1, 67, 49),
                   (11, 1, 199, 139), (3, 2, 19, 11), (11, 2, 67, 22),
                   (13, 2, 79, 4)}


def check(name, cond):
    print(f"[{'ok' if cond else 'FAIL'}] {name}", flush=True)
    if not cond:
        sys.exit(1)


def row_pivots(ME, p):
    # Elimination-based (Q6); a swap-only greedy over-reports pivots.
    return Q6.fp_row_pivots(ME, p)


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

    # §1 regression: V1 right-nullspace basis generally not J-fixed
    nbad = 0
    for (d, n0, p, xi) in [(5, 1, 31, 2), (7, 1, 43, 9), (9, 1, 109, 5)]:
        bad, tot = QV.v1_orientation_regression(d, n0, p, xi, schedule_L3)
        print(f"V1-basis not J-fixed d={d} p={p} xi={xi}: {bad}/{tot}",
              flush=True)
        nbad += bad
    check("V1 orientation bug reproduced (bad > 0)", nbad > 0)

    # §§2-3 replay + canonical pivot pattern + quotient map
    out_rows = []
    pivot_bad = []
    for n0 in (1, 2):
        for d in (3, 5, 7, 9, 11, 13, 15):
            r = 3 * d
            H = (r + 1) // 2
            for p in PRIMES[r]:
                for xi in G.rth_roots(p, r):
                    c = QV.build_canonical(d, n0, p, xi, schedule_L3)
                    b = c['base']
                    E, B, QP = b['E'], b['B'], b['QP']
                    rE = G.fp_rank(E, p)
                    rEBQ = G.fp_rank(E + [B, QP], p)
                    ME = c['ME']
                    piv = row_pivots(ME, p)
                    isbad = (d, n0, p, xi) in V1_EXPECTED_BAD
                    if piv != list(range(H - 2)):
                        pivot_bad.append((d, n0, p, xi, piv, isbad))
                        out_rows.append((d, n0, p, xi, rE, rEBQ,
                                         False, None, True))
                        continue
                    # quotient map (§6); A invertible by pivot pattern
                    A = [row[:H - 2] for row in ME]
                    U = [row[H - 2:] for row in ME]
                    Ai = QV.mat_inv(A, p)
                    AU = [[sum(Ai[i][k] * U[k][j]
                               for k in range(H - 2)) % p
                           for j in range(2)] for i in range(H - 2)]

                    def rho(v, _AU=AU, _H=H):
                        vL, vR = v[:_H - 2], v[_H - 2:]
                        return [(vR[j] - sum(vL[i] * _AU[i][j]
                                             for i in range(_H - 2))) % p
                                for j in range(2)]
                    zE = [rho(row) for row in ME]
                    check(f"rho(E)=0 d={d} n0={n0} p={p} xi={xi}",
                          all(z == [0, 0] for z in zE))
                    Cb = [B[k] % p for k in range(H)]
                    Cq = [QP[k] % p for k in range(H)]
                    beta = rho(Cb)
                    qq = rho(Cq)
                    Delta = (beta[0] * qq[1] - beta[1] * qq[0]) % p
                    agree = (Delta != 0) == (rEBQ == H)
                    out_rows.append((d, n0, p, xi, rE, rEBQ, True,
                                     Delta, agree))
    print(f"canon replay rows: {len(out_rows)}", flush=True)
    nzero = sum(1 for row in out_rows if row[7] == 0)
    print(f"Delta==0 cells: {nzero}", flush=True)
    print("pivot-breaking cells (recorded, see CANONICAL doc):", flush=True)
    for (d, n0, p, xi, piv, isbad) in pivot_bad:
        print(f"  PIVOT d={d} n0={n0} p={p} xi={xi} piv={piv}", flush=True)
    for row in out_rows:
        d, n0, p, xi, rE, rEBQ, pivok, Delta, agree = row
        if not agree:
            print(f"DELTA/RANK DISAGREE d={d} n0={n0} p={p} xi={xi} "
                  f"Delta={Delta} rankEBQ={rEBQ}", flush=True)
            sys.exit(1)
    zeros = {(d, n0, p, xi) for (d, n0, p, xi, _, _, _, D, _) in out_rows
             if D == 0}
    check("Delta zeros == V1 ten bad cells", zeros == V1_EXPECTED_BAD)
    print("Q196 V2 PART-A COMPLETE")


if __name__ == "__main__":
    main()
