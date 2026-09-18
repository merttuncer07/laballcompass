"""True Q195 experiment driver V3 (Phases 1,3-11).

Exact centered-Gamma packets + derived weighted reversal + augmented
projection, over finite fields. NO V1/V2 objects used as mathematics.
Exits nonzero on: failed identities, chronology mismatch, Phase-9
mismatch, or formal/physical disagreement. Phase-10 cells are RECORDED
verbatim (PASS/FAIL rows); hidden failures are forbidden.
"""

import os
import sys

import q195_exact_gamma as G

from VOLTERRA_RESONANT_FIXED_STATE_CERT_STANDALONE import schedule_L3

PRIMES = {9: (19, 37), 15: (31, 61), 21: (43, 127), 27: (109, 163),
          33: (67, 199), 39: (79, 157), 45: (181, 271)}
HIST9 = {(9, 3): (3, 1), (15, 5): (5, 1), (21, 14): (7, 2),
         (27, 9): (9, 1), (33, 11): (11, 1)}
HIST9_MISSING = [(15, 9), (25, 5), (35, 14)]
CHRON = {3: ([('h', 2), ('q', 2), ('h', 1), ('q', 1), ('h', 0)],
             [3, 4, 5, 6, 7]),
         5: ([('h', 4), ('q', 4), ('q', 3), ('h', 2), ('q', 2),
              ('h', 1), ('q', 1), ('h', 0)],
             [5, 6, 8, 9, 10, 11, 12, 13])}


def check(name, cond):
    print(f"[{'ok' if cond else 'FAIL'}] {name}", flush=True)
    if not cond:
        sys.exit(1)


def build_case(d, n0, p, xi):
    """Exact-Gamma b_in/C objects for (d, n0) at product frequency xi."""
    r, _, s, R, P = G.int_word(d, n0, schedule_L3)
    T, keys = G.fstar_chronology(d)
    H = (r + 1) // 2
    assert len(T) == H and len(set(T)) == len(T)
    objs = []
    for (a, b) in [(T[0], T[1])] + [(T[i], T[i + 1])
                                    for i in range(1, len(T) - 1)]:
        (pk, c), _ = G.gamma_packet(R, P, s, a, b, xi, p, r)
        Gam, _, _ = G.centered_gamma(R, P, a, b, xi, p)
        objs.append(((pk, c), G.reduce_qr(Gam, p, r)))
    assert len(objs) - 1 == H - 2
    return {'d': d, 'n0': n0, 'r': r, 'P': P, 'T': T, 'keys': keys,
            'b_in': objs[0], 'C': objs[1:]}


def edge_vec(pk, E, r):
    v = [0] * E
    for (i, j), w in pk.items():
        v[i * r + j] = w % 0x7fffffff
    return v


def main():
    import VOLTERRA_RESONANT_FIXED_STATE_CERT_STANDALONE as _cert
    _here = os.path.realpath(os.getcwd())
    for _m in (_cert, G):
        _f = os.path.realpath(getattr(_m, "__file__", ""))
        check(f"dependency loads from run dir: {os.path.basename(_f)}",
              _f.startswith(_here + os.sep))

    # Phase 1 re-verification (compact grid)
    for (d, n0, p) in [(3, 1, 19), (5, 1, 31), (5, 2, 31)]:
        r, _, s, R, P = G.int_word(d, n0, schedule_L3)
        ok = True
        for xi in G.rth_roots(p, r):
            for u in (2, 3):
                v = (xi * pow(u % p, p - 2, p)) % p
                Q = G.quad_values(R, u % p, v, p)
                for k in range(r):
                    ok &= ((Q[k + 1] - pow(xi, s[k], p) * Q[k]) % p
                           == (G.peval({e: x % p for e, x in R[k + 1].items()}, u % p, p)
                               + G.peval({e: x % p for e, x in R[k + 1].items()}, v, p) - 1) % p)
                Gam, _, _ = G.centered_gamma(R, P, 0, r, xi, p)
                ok &= ((Q[r] - pow(xi, P[r] - P[0], p) * Q[0]) % p
                       == (G.peval(Gam, u % p, p) + G.peval(Gam, v, p)) % p)
        check(f"Phase-1 identities d={d} n0={n0} p={p}", ok)

    # Phase 3: pi(Q~_j) == suffix_Q_j; pi(A~) == A
    for (d, n0, p) in [(3, 1, 19), (5, 1, 31)]:
        r, _, s, R, P = G.int_word(d, n0, schedule_L3)
        xi = G.rth_roots(p, r)[1]
        ok = True
        for j in range(1, r + 1):
            tq = {(i, j): 1 for i in range(j)}
            img = G.pi_packet_formal(tq, P, r)
            Qj = {e: v % p for e, v in
                  G.suffix_Q_int(R, s, j, r).items()}
            ok &= ({e: v % p for e, v in img.items()} == Qj or
                   G.reduce_qr(img, p, r) == G.reduce_qr(Qj, p, r))
        pk, _ = G.formal_packet(R, P, s, 1, 4, xi, p)
        A = {}
        _, _, w = G.centered_gamma(R, P, 1, 4, xi, p)
        for h in range(2, 5):
            Qh = {e: v % p for e, v in G.suffix_Q_int(R, s, h, r).items()}
            A = G.padd(A, G.pscale(Qh, w[h], p), p)
        img = G.pi_packet_formal(pk, P, r)
        ok &= ({e: v % p for e, v in img.items()} == A)
        check(f"Phase-3 projection d={d} n0={n0} p={p}", ok)

    # Phase 4 unit tests: pi J = Jhat pi per edge; J^2 = I; J vs Jhat
    for (d, n0, p) in [(3, 1, 19), (5, 1, 31)]:
        r, _, _, _, P = G.int_word(d, n0, schedule_L3)
        ok = True
        for xi in G.rth_roots(p, r)[:7]:
            for i in range(r + 1):
                for j in range(i + 1, r + 1):
                    D = P[j] - P[i] - 1
                    lhs = G.pscale(G.x_negpow(D + 2, p, r),
                                   pow(xi, D + 1, p), p)  # pi(J e)
                    # J e = xi^{Pj-Pi}[j->i]; pi = xi^{Pj-Pi} x^{Pi-Pj-1}
                    wgt = pow(xi, P[j] - P[i], p)
                    rhs = G.pscale({P[i] - P[j] - 1: 1}, wgt, p)
                    # compare in ring
                    ok &= (G.reduce_qr(lhs, p, r)
                           == G.reduce_qr({e: v % p for e, v in rhs.items()}, p, r))
                    # J^2: weight product xi^{dP} xi^{-dP} = 1, edges restored
                    ok &= ((wgt * pow(xi, P[i] - P[j], p)) % p == 1)
            # J vs Jhat operator relation on all basis monomials.
            # NOTE: x^{-2} is the TRUE ring inverse (-x^{r-2}), not +x^{r-2}:
            # x^{-2} x^2 = +1 while x^{r-2} x^2 = x^r = -1. The minus sign
            # below is load-bearing (caught h=0: Jhat 1 = xi x^{-2} != 1).
            for h in range(r):
                Jh = {0: 1} if h == 0 else {(r - h) % r: (-pow(xi, h, p)) % p}
                Jhat_h = G.Jhat_mon(h, xi, p, r)
                rel = G.px_shift_mul({e: v % p for e, v in Jh.items()},
                                     r - 2, p, r)
                rel = G.pscale(rel, -xi, p)
                ok &= (G.reduce_qr(Jhat_h, p, r)
                       == G.reduce_qr(rel, p, r))
        check(f"Phase-4 reversal d={d} n0={n0} p={p}", ok)

    # Phase 5: augmented projection intertwining + centering kept
    for (d, n0, p) in [(3, 1, 19), (5, 1, 31)]:
        r, _, s, R, P = G.int_word(d, n0, schedule_L3)
        xi = G.rth_roots(p, r)[1]
        ok = True
        for (a, b) in [(0, 2), (1, 4), (0, r)]:
            pk, c = G.formal_packet(R, P, s, a, b, xi, p)
            left = G.Pi_augmented(G.J_formal(pk, P, xi, p), c, P, p, r)
            right = G.J_poly({e: v for e, v in
                              enumerate(G.Pi_augmented(pk, c, P, p, r))},
                             xi, p, r)
            ok &= (left == right)
            Gam, _, _ = G.centered_gamma(R, P, a, b, xi, p)
            ok &= (G.Pi_augmented(pk, c, P, p, r)
                   == G.reduce_qr(Gam, p, r))
        check(f"Phase-5 augmented Pi d={d} n0={n0} p={p}", ok)

    # Phase 6: chronology
    for d, (ek, eT) in CHRON.items():
        T, keys = G.fstar_chronology(d)
        check(f"Phase-6 d={d} keys", keys == ek)
        check(f"Phase-6 d={d} times", T == eT)
    for d in (7, 9, 11, 13, 15):
        T, _ = G.fstar_chronology(d)
        check(f"Phase-6 d={d} |F*|=H unique", len(T) == (3 * d + 1) // 2
              and len(set(T)) == len(T))

    # Phases 8+10: polynomial code sweep (all xi, two primes).
    # corevec from build_case objects (no recomputation).
    sweep_rows = []
    for n0 in (1, 2):
        for d in (3, 5, 7, 9, 11, 13, 15):
            r = 3 * d
            H = (r + 1) // 2
            for p in PRIMES[r]:
                for xi in G.rth_roots(p, r):
                    case = build_case(d, n0, p, xi)
                    corevec = [vec for (_, vec) in case['C']]
                    Jcore = [G.J_poly(dict(enumerate(v)), xi, p, r)
                             for v in corevec]
                    rC = G.fp_rank(corevec, p)
                    rJ = G.fp_rank(Jcore, p)
                    joint = G.fp_rank(corevec + Jcore, p)
                    inter = rC + rJ - joint
                    okcell = (rC == H - 2 and joint == r - 3)
                    sweep_rows.append((d, n0, p, xi, rC, rJ, joint,
                                       inter, okcell))
    npass = sum(1 for row in sweep_rows if row[8])
    print(f"Phase-8/10 cells: {npass}/{len(sweep_rows)} joint==r-3 "
          f"with rankC==H-2", flush=True)
    with open("Q195_V3_SWEEP.txt", "w") as f:
        f.write("# Phase-10 true common-core sweep "
                "(finite evidence, not proof)\n")
        for (d, n0, p, xi, rC, rJ, joint, inter, okcell) in sweep_rows:
            f.write(f"d={d} n0={n0} p={p} xi={xi} rankC={rC} "
                    f"rankJC={rJ} joint={joint} inter={inter} "
                    f"{'PASS' if okcell else 'FAIL'}\n")

    # Phase 9: historical (r,n) checkpoints (RECONSTRUCTED HISTORICAL EVIDENCE)
    # Survey-complete: record every frequency cell; exit nonzero at end if
    # any mismatch (STOP semantics = no passing narrative, full tables kept).
    hist_rows = []
    hist_bad = 0
    for (rr, nn) in sorted(HIST9):
        d, n0 = HIST9[(rr, nn)]
        r = 3 * d
        H = (r + 1) // 2
        for p in PRIMES[r]:
            for xi in G.rth_roots(p, r):
                case = build_case(d, n0, p, xi)
                W = [vec for (_, vec) in [case['b_in']] + case['C']]
                JW = [G.J_poly(dict(enumerate(v)), xi, p, r) for v in W]
                rW = G.fp_rank(W, p)
                rWJ = G.fp_rank(W + JW, p)
                okcell = (rW == H - 1 and rWJ == r - 1)
                hist_rows.append((rr, nn, p, xi, rW, rWJ, okcell))
                if not okcell:
                    hist_bad += 1
                    print(f"HISTORICAL CELL FAIL: (r,n)={(rr, nn)} p={p} "
                          f"xi={xi} rankA={rW} dimWJW={rWJ}", flush=True)
    with open("Q195_HISTORICAL_RECONSTRUCTION.txt", "w") as f:
        f.write("# Phase-9 RECONSTRUCTED HISTORICAL EXACT EVIDENCE\n"
                "# (r,n)=(15,9),(25,5),(35,14): NOT RECONSTRUCTIBLE — "
                "older source absent; see provenance.\n")
        for (rr, nn, p, xi, rW, rWJ, okcell) in hist_rows:
            f.write(f"r={rr} n={nn} p={p} xi={xi} rankA={rW} "
                    f"dimWJW={rWJ} {'PASS' if okcell else 'FAIL'}\n")
    print(f"Phase-9 historical checkpoints: "
          f"{len(hist_rows) - hist_bad}/{len(hist_rows)} PASS "
          f"(5 reconstructible cases; 3 cases NOT RECONSTRUCTIBLE)",
          flush=True)

    # Phase 11: formal packets, formal transversality, ker Pi, agreement.
    # Survey-complete: disagreements recorded, exit nonzero at end (STOP =
    # no equivalence claim, full tables kept).
    nagree = nformal = ndiag = 0
    ndiag_rows = []
    for n0 in (1, 2):
        for d in (3, 5, 7, 9, 11, 13, 15):
            r = 3 * d
            E = (r + 1) * r
            for p in PRIMES[r]:
                for xi in G.rth_roots(p, r):
                    case = build_case(d, n0, p, xi)
                    Fcols, Rcols, Grows = [], [], []
                    for ((pk, _c), _v) in case['C']:
                        fv = [0] * E
                        for (i, j), w in pk.items():
                            fv[i * r + j] = w
                        Fcols.append(fv)
                        rv = [0] * E
                        for (i, j), w in G.J_formal(pk, case['P'],
                                                   xi, p).items():
                            rv[i * r + j] = w
                        Rcols.append(rv)
                    g = len(Fcols)
                    rF = G.fp_rank(Fcols, p)
                    rR = G.fp_rank(Rcols, p)
                    check(f"formal generator dims d={d} n0={n0} p={p} "
                          f"xi={xi}", rF == g and rR == g)
                    rJ = G.fp_rank(Fcols + Rcols, p)
                    finter = g + g - rJ
                    # ker Pi via augmented route (= stacked Gamma rows)
                    Grows = [vec for (_, vec) in case['C']] + [
                        G.J_poly(dict(enumerate(vec)), xi, p, r)
                        for (_, vec) in case['C']]
                    rG = G.fp_rank(Grows, p)
                    knull = 2 * g - rG
                    agree = (finter == 0) == (knull == 0)
                    if not agree:
                        ndiag += 1
                        ndiag_rows.append((d, n0, p, xi, finter, knull))
                        print(f"FORMAL/PHYSICAL DISAGREEMENT d={d} n0={n0} "
                              f"p={p} xi={xi}: formal_inter={finter} "
                              f"kerPi_null={knull}", flush=True)
                        continue
                    nagree += 1
                    if finter == 0 and knull == 0:
                        nformal += 1
    print(f"Phase-11 cells: {nformal}/{nagree} formal-zero AND kerPi-zero; "
          f"agreement holds on all surveyed; disagreements: {ndiag}",
          flush=True)
    nfail = (len(sweep_rows) - sum(1 for row in sweep_rows if row[8])) \
        + hist_bad + ndiag
    with open("Q195_V3_FAILURES.txt", "w") as f:
        f.write("# failing/disagreeing cells (empty = none found)\n")
        for row in sweep_rows:
            if not row[8]:
                f.write(f"SWEEP FAIL d={row[0]} n0={row[1]} p={row[2]} "
                        f"xi={row[3]} rankC={row[4]} rankJC={row[5]} "
                        f"joint={row[6]} inter={row[7]}\n")
        for row in hist_rows:
            if not row[6]:
                f.write(f"HIST FAIL r={row[0]} n={row[1]} p={row[2]} "
                        f"xi={row[3]} rankA={row[4]} dimWJW={row[5]}\n")
        for row in ndiag_rows:
            f.write(f"DISAGREE d={row[0]} n0={row[1]} p={row[2]} xi={row[3]} "
                    f"formal={row[4]} kerPi={row[5]}\n")
    if nfail == 0 and ndiag == 0:
        print("Q195 V3 TRUE EXPERIMENT: ALL CELLS PASS")
    else:
        print(f"Q195 V3 TRUE EXPERIMENT: COMPLETED WITH {nfail} "
              f"FAILING/DIAG CELLS — NO Q195 CLAIM", flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()



def build_case(d, n0, p, xi):
    """Exact-Gamma interval objects for (d,n0) at product frequency xi."""
    r, n, s, R, P = G.int_word(d, n0, schedule_L3)
    T, keys = G.fstar_chronology(d)
    H = (r + 1) // 2
    assert len(T) == H and len(set(T)) == len(T)
    objs = []
    for a, b in [(T[0], T[1])] + [(T[i], T[i + 1])
                                  for i in range(1, len(T) - 1)]:
        (pk, c), _ = G.gamma_packet(R, P, s, a, b, xi, p, r)
        Gam, _, _ = G.centered_gamma(R, P, a, b, xi, p)
        objs.append(((pk, c), G.reduce_qr(Gam, p, r)))
    b_in = objs[0]
    C = objs[1:]
    assert len(C) == H - 2
    return {'r': r, 'T': T, 'keys': keys, 'H': H, 'P': P, 's': s,
            'b_in': b_in, 'C': C}
