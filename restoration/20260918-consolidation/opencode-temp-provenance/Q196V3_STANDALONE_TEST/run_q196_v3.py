"""Q196 V3 driver: chronology lemma, z-system, phase walk, dual parameters,
anchor, agreement, d<=31 data. No floating point. Exit nonzero on any
failed exact assertion. V1/V2/V3-Q195 packages sealed (hash-checked inputs
only where vendored).
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


def check(name, cond):
    print(f"[{'ok' if cond else 'FAIL'}] {name}", flush=True)
    if not cond:
        sys.exit(1)


def closed_T(d):
    """Part E closed chronology: T_0 = d; T_i = d+2i-1 (1<=i<=e);
    then every integer 2d-1..3d-2."""
    e = (d - 1) // 2
    return [d] + [d + 2 * i - 1 for i in range(1, e + 1)] + list(
        range(2 * d - 1, 3 * d - 1))


def Ev(a, b):
    return 0 if b < a else b // 2 - (a - 1) // 2


def Od(a, b):
    return 0 if b < a else (b - a + 1) - Ev(a, b)


def G_closed(d, k):
    """Part I closed gap-sum (regions from the schedule)."""
    r = 3 * d
    Bv, Rv = r - 1, r
    if k <= d - 1:
        return k
    if k <= d + 1:
        return d - 1
    if k <= 2 * d - 1:
        return (d - 1) + Bv * Ev(d + 1, k - 1)
    if k <= 3 * d - 2:
        return ((d - 1) + Bv * Ev(d + 1, 2 * d - 2)
                + Bv * Ev(2 * d - 1, k - 1) + Rv * Od(2 * d - 1, k - 1))
    G32 = ((d - 1) + Bv * Ev(d + 1, 2 * d - 2) + Bv * Ev(2 * d - 1, 3 * d - 3)
           + Rv * Od(2 * d - 1, 3 * d - 3))
    return G32 + Rv * (k - (3 * d - 2))


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

    # Part E: closed chronology vs computed, d = 3..31
    for d in range(3, 32, 2):
        T, _ = G.fstar_chronology(d)
        check(f"Part-E chronology d={d}", T == closed_T(d))
    # Part E counts: head e-1 length-2 + rest length-1, total H-1 intervals
    for d in (5, 7, 9, 11, 13, 15):
        T = closed_T(d)
        gaps = [T[i + 1] - T[i] for i in range(len(T) - 1)]
        check(f"Part-E gaps in {{1,2}} d={d}",
              all(g in (1, 2) for g in gaps))

    # Part I: closed phase walk (value, mod, quo-parity), d = 3..11
    for d in (3, 5, 7, 9, 11):
        for n0 in (1, 2):
            r, n, e, U, B, F, Fs, g = schedule_L3(d, n0)
            Gacc, Pacc = 0, 0
            ok = True
            for k in range(r + 1):
                if k > 0:
                    Gacc += g[k - 1]
                    Pacc += n + g[k - 1]
                Pcf = k * n + G_closed(d, k)
                ok &= (Gacc == G_closed(d, k) and Pacc == Pcf)
            check(f"Part-I phase walk d={d} n0={n0}", ok)

    # Part F: exact z-system shape from closed chronology (all d odd <= 31)
    for d in range(3, 32, 2):
        e = (d - 1) // 2
        H = 3 * e + 2
        T = closed_T(d)
        Clen2 = [(T[i], T[i + 1]) for i in range(1, len(T) - 1)
                 if T[i + 1] - T[i] == 2]
        Clen1 = [(T[i], T[i + 1]) for i in range(1, len(T) - 1)
                 if T[i + 1] - T[i] == 1]
        exp2 = [(d + 2 * j - 1, d + 2 * j + 1) for j in range(1, e)]
        exp1first, exp1last = T[e], T[-1]
        check(f"Part-F C-intervals d={d}",
              Clen2 == exp2 and len(Clen1) == len(T) - 2 - (e - 1)
              and len(Clen2) + len(Clen1) == H - 2)
    # Part F: exact z-system shape from closed chronology (all d odd <= 31)
    for d in range(3, 32, 2):
        e = (d - 1) // 2
        H = 3 * e + 2
        T = closed_T(d)
        Clen2 = [(T[i], T[i + 1]) for i in range(1, len(T) - 1)
                 if T[i + 1] - T[i] == 2]
        Clen1 = [(T[i], T[i + 1]) for i in range(1, len(T) - 1)
                 if T[i + 1] - T[i] == 1]
        exp2 = [(d + 2 * j - 1, d + 2 * j + 1) for j in range(1, e)]
        check(f"Part-F C-intervals d={d}",
              Clen2 == exp2 and len(Clen1) == len(T) - 2 - (e - 1)
              and len(Clen2) + len(Clen1) == H - 2)
    print("Q196 V3 PART-A COMPLETE")

    # Shared dual-basis builder: TRUE invariant covectors lam with
    # lam . R_j = lam_j for all Jm rows R_j (RIGHT nullspace of Jm - I).
    # (The transpose system gives primal fixed VECTORS — wrong object
    # here; caught by the 2z identity check.)
    def dual_basis(d, n0, p, xi):
        r = 3 * d
        bnd = Q6.build_boundary(d, n0, p, xi, schedule_L3)
        Jm = bnd['Jm']
        rows = [[(Jm[i][j] - (1 if i == j else 0)) % p for j in range(r)]
                for i in range(r)]
        Lam, _ = Q6.fp_nullspace_rows(rows, p)
        if len(Lam) != (r + 1) // 2:
            return None
        r_, _, s, R, P = G.int_word(d, n0, schedule_L3)
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

    # Part G: lambda((I+J)b_in) = 2 z_{d+1} for both lams (all V4 cells).
    # b_in = R_{d+1} - 1/2 (unit interval, weight 1): checked as formal
    # identity first; then the 2z identity per dual basis vector.
    for n0 in (1, 2):
        for d in (3, 5, 7, 9, 11, 13, 15):
            r = 3 * d
            for p in PRIMES[r]:
                for xi in G.rth_roots(p, r):
                    r_, _, s, R, P = G.int_word(d, n0, schedule_L3)
                    T, _ = G.fstar_chronology(d)
                    Gb, _, _ = G.centered_gamma(R, P, T[0], T[1], xi, p)
                    Rd1 = {e: v % p for e, v in R[d + 1].items()}
                    form = G.padd(Rd1, {0: (-pow(2, p - 2, p)) % p}, p)
                    Gbred = {e: v % p for e, v in Gb.items()}
                    if not (form == Gbred):
                        print(f"G-FORM FAIL d={d} n0={n0} p={p} xi={xi}",
                              flush=True)
                        sys.exit(1)
                    db = dual_basis(d, n0, p, xi)
                    if db is None:
                        print(f"G-DUALDIM FAIL d={d} n0={n0} p={p} xi={xi}",
                              flush=True)
                        sys.exit(1)
                    lams, R2, P2, T2, bnd = db
                    bv = G.reduce_qr(Gb, p, r)
                    Jb = G.J_poly(dict(enumerate(bv)), xi, p, r)
                    Bv = [(a + b_) % p for a, b_ in zip(bv, Jb)]
                    rh = [0] * r
                    for e, vv in R[d + 1].items():
                        q_, rem = divmod(e, r)
                        rh[rem] = (rh[rem] + ((-1) ** q_) * (vv % p)) % p
                    for t in range(2):
                        lam = lams[t]
                        lB = sum(lam[j] * Bv[j] for j in range(r)) % p
                        l0 = lam[0] % p
                        z = (sum(lam[j] * rh[j] for j in range(r)) % p
                             - l0 * pow(2, p - 2, p)) % p
                        if lB != (2 * z) % p:
                            print(f"G-2Z FAIL d={d} n0={n0} p={p} "
                                  f"xi={xi} lam={t}", flush=True)
                            sys.exit(1)
    print("Part-G b_in unit form + 2z identity verified", flush=True)

    # Parts K-M: (alpha,beta) = (z_{d+1}, z_{d+2}) with TRUE z's
    # (minus l0/2), anchor linear form, det agreement with canonical Delta.
    # Canonical Delta recomputed here via V2 rho route (pivot-aware).
    nagree = ncoll = nalt = npiv = 0
    alt_rows = []
    anchor_rows = []
    for n0 in (1, 2):
        for d in (3, 5, 7, 9, 11, 13, 15):
            r = 3 * d
            H = (r + 1) // 2
            p = PRIMES[r][1]
            for xi in G.rth_roots(p, r):
                db = dual_basis(d, n0, p, xi)
                if db is None:
                    print(f"KM-DUALDIM FAIL d={d} n0={n0} p={p} xi={xi}",
                          flush=True)
                    sys.exit(1)
                lams, R, P, T, bnd = db
                inv2 = pow(2, p - 2, p)

                # true z_h(lam) = lam(R_h ring) - lam[0]/2
                def zh(lam, h):
                    tot = 0
                    for e, vv in R[h].items():
                        q_, rem = divmod(e, r)
                        tot = (tot + ((-1) ** q_) * (vv % p)
                               * lam[rem]) % p
                    return (tot - lam[0] * inv2) % p
                # Parametrization pair pool (Part K): preferred (z_{d+1},
                # z_{d+2}), then alternates, then exhaustive scan.
                E = None
                detE, used = 0, None
                pool = [(d + 1, d + 2), (d + 1, r - 1), (d + 1, r),
                        (d + 1, 0), (d + 1, H - 1)]
                for (h1, h2) in pool:
                    E = [[zh(lams[t], h1), zh(lams[t], h2)]
                         for t in range(2)]
                    detE = (E[0][0] * E[1][1] - E[0][1] * E[1][0]) % p
                    if detE != 0:
                        used = (h1, h2)
                        break
                if detE == 0:
                    for h1 in range(r + 1):
                        for h2 in range(h1 + 1, r + 1):
                            E = [[zh(lams[t], h1), zh(lams[t], h2)]
                                 for t in range(2)]
                            detE = (E[0][0] * E[1][1]
                                    - E[0][1] * E[1][0]) % p
                            if detE != 0:
                                used = (h1, h2)
                                break
                        if detE != 0:
                            break
                # Triangular M_Q196: lam(B) = 2*alpha + 0*beta always
                # (Part G); solve [A_Q,B_Q] with lam(Q) = A_Q a + B_Q b.
                AQb = None
                if detE != 0:
                    QP = bnd['QP']
                    qv = [sum(lams[t][j] * QP[j] for j in range(r)) % p
                          for t in range(2)]
                    inv = pow(detE, p - 2, p)
                    Einv = [[E[1][1] * inv % p, (-E[0][1]) * inv % p],
                            [(-E[1][0]) * inv % p, E[0][0] * inv % p]]
                    AQb = [(Einv[0][0] * qv[0] + Einv[0][1] * qv[1]) % p,
                           (Einv[1][0] * qv[0] + Einv[1][1] * qv[1]) % p]
                    anchor_rows.append((d, n0, p, xi, used, AQb[0], AQb[1],
                                        (2 * AQb[1]) % p))
                # Dual BOUNDARY matrix (Part M): lam_t(B), lam_t(Q).
                # Agreement target: detD != 0  <=>  canonical != 0.
                QP = bnd['QP']
                Bv = bnd['B']
                D = [[[sum(lams[t][j] * Bv[j] for j in range(r)) % p,
                       sum(lams[t][j] * QP[j] for j in range(r)) % p]
                      for t in range(2)]][0]
                detD = (D[0][0] * D[1][1] - D[0][1] * D[1][0]) % p
                AQs = [D[t][1] for t in range(2)]
                # canonical Delta (None where pivots break)
                c = QV.build_canonical(d, n0, p, xi, schedule_L3)
                ME = c['ME']
                piv = Q6.fp_row_pivots(ME, p)
                if piv == list(range(H - 2)):
                    A = [row[:H - 2] for row in ME]
                    U = [row[H - 2:] for row in ME]
                    Ai = QV.mat_inv(A, p)
                    AU = [[sum(Ai[i][k] * U[k][j] for k in range(H - 2))
                           % p for j in range(2)] for i in range(H - 2)]

                    def rho(v):
                        return [(v[H - 2 + j] - sum(
                            v[i] * AU[i][j] for i in range(H - 2))) % p
                            for j in range(2)]
                    be = rho([bnd['B'][k] % p for k in range(H)])
                    qq = rho([bnd['QP'][k] % p for k in range(H)])
                    DeltaC = (be[0] * qq[1] - be[1] * qq[0]) % p
                else:
                    DeltaC = None
                if DeltaC is None:
                    npiv += 1
                    continue
                nagree += 1
                if not ((detD != 0) == (DeltaC != 0)):
                    print(f"DET-AGREE FAIL d={d} n0={n0} p={p} xi={xi} "
                          f"dual={detD} canon={DeltaC}", flush=True)
                    sys.exit(1)
                if detD == 0:
                    ncoll += 1
                elif used != (d + 1, d + 2):
                    nalt += 1
                    alt_rows.append((d, n0, p, xi, used))
    print(f"Parts K-M: {nagree} agreement cells; collinear {ncoll}; "
          f"alternate-pair {nalt}; pivot-break-skipped {npiv}", flush=True)
    for row in alt_rows:
        print(f"  ALT-PAIR d={row[0]} n0={row[1]} p={row[2]} xi={row[3]} "
              f"pair={row[4]}", flush=True)
    with open("Q196_ANCHOR.txt", "w") as f:
        f.write("# d n0 p xi pair A_Q B_Q detM=2B_Q\n")
        for row in anchor_rows:
            f.write(f"{row[0]} {row[1]} {row[2]} {row[3]} {row[4]} "
                    f"{row[5]} {row[6]} {row[7]}\n")

    # Part B: per-(d,n0,s) leading-block witnesses (rank A == H-2).
    wit_lines = ["# d n0 s cert-p cert-xi rankA target"]
    for n0 in (1, 2):
        for d in (3, 5, 7, 9, 11, 13, 15):
            r = 3 * d
            H = (r + 1) // 2
            divs = sorted({s for s in range(1, r + 1) if r % s == 0})
            for s in divs:
                found = None
                for p in PRIMES[r]:
                    for xi in G.rth_roots(p, r):
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
                        if o != s:
                            continue
                        c = QV.build_canonical(d, n0, p, xi, schedule_L3)
                        A = [row[:H - 2] for row in c['ME']]
                        if G.fp_rank(A, p) == H - 2:
                            found = (p, xi)
                            break
                    if found:
                        break
                if found is None:
                    print(f"NO BLOCK WITNESS d={d} n0={n0} order {s}",
                          flush=True)
                    sys.exit(1)
                wit_lines.append(f"{d} {n0} {s} {found[0]} {found[1]} "
                                 f"{H - 2} {H - 2}")
    with open("Q196_BLOCKWITNESS.txt", "w") as f:
        f.write("\n".join(wit_lines) + "\n")
    print("Part-B leading-block witnesses complete", flush=True)

    partC_cyclotomic_detA()
    partN_D31_data()
    print("Q196 V3 ALL PARTS COMPLETE")


def partC_cyclotomic_detA():
    """Part C: det(A) != 0 over Q[X]/(Phi_s) for the six suspect sectors.

    A = leading (H-2)x(H-2) block of canonical-coordinate E rows, built
    with weight exponents mod s (formal primitive s-th root). Asserts
    full rank H-2 (equivalent to det != 0). Imports the V4 cyclotomic
    machinery (frozen file reuse, never modified).
    """
    import q195_charzero_finite_cert as V4C
    for (d, n0, s) in [(5, 1, 5), (3, 2, 9), (7, 2, 21),
                       (11, 2, 33), (15, 1, 45), (15, 2, 45)]:
        F = V4C.Cyclo(s)
        check(f"cyclo field s={s}", F.selftest())
        Fr, rows = V4C.cyclo_gamma_rows(d, n0, s, schedule_L3, full=False)
        r = 3 * d
        H = (r + 1) // 2
        # E rows = rows + J(rows); canonical coords = first H entries.
        # Reconstruction f = sum f_k e_k asserted per row (basis-rule
        # transfer check over Q(zeta_s); STOP on failure).
        Jrows = V4C.cyclo_J(rows, Fr, s, r)
        Erows = [[Fr.add(a, b) for a, b in zip(v, w)]
                 for v, w in zip(rows, Jrows)]
        z = [Fr.Fraction(0)] * Fr.m
        for v in Erows:
            rec = [list(z) for _ in range(r)]
            for k in range(H):
                ck = v[k]
                if any(x != 0 for x in ck):
                    if k == 0:
                        rec[0] = Fr.add(rec[0], ck)
                    else:
                        rec[k] = Fr.add(rec[k], ck)
                        t = Fr.mul(ck, Fr.gen(k))
                        t = Fr.neg(t)
                        rec[(r - k) % r] = Fr.add(rec[(r - k) % r], t)
            if not all(all((a - b) == 0 for a, b in zip(x, y))
                       for x, y in zip(rec, v)):
                print(f"CANON-RULE FAIL d={d} n0={n0} s={s}", flush=True)
                sys.exit(1)
        ME = [row[:H] for row in Erows]
        A = [row[:H - 2] for row in ME]
        check(f"cyclo detA full rank d={d} n0={n0} s={s}",
              Fr.rank(A) == H - 2)
    print("Part-C cyclotomic detA verified on all six sectors", flush=True)


def partN_D31_data():
    """Part N: exact data d = 3..31, both n0 (one prime each; inference).

    Records per (d, xi): pivot pattern, rankEBQ, canonical Delta (None
    where pivots break). No characteristic-zero claims beyond V4 range.
    """
    D31 = {51: 103, 57: 229, 63: 127, 69: 139, 75: 151,
           81: 163, 87: 349, 93: 373}
    for r_, pp in PRIMES.items():
        D31[r_] = pp[0]
    lines = ["# d n0 p xi Delta pivots-ok rankEBQ/H"]
    for n0 in (1, 2):
        for d in list(range(3, 32, 2)):
            r = 3 * d
            H = (r + 1) // 2
            p = D31[r]
            assert pow(2, p - 1, p) == 1 and pow(3, p - 1, p) == 1, p
            for xi in G.rth_roots(p, r):
                c = QV.build_canonical(d, n0, p, xi, schedule_L3)
                b = c['base']
                ME = c['ME']
                piv = Q6.fp_row_pivots(ME, p)
                pivok = (piv == list(range(H - 2)))
                rEBQ = G.fp_rank(b['E'] + [b['B'], b['QP']], p)
                if pivok:
                    A = [row[:H - 2] for row in ME]
                    U = [row[H - 2:] for row in ME]
                    Ai = QV.mat_inv(A, p)
                    AU = [[sum(Ai[i][k] * U[k][j] for k in range(H - 2))
                           % p for j in range(2)] for i in range(H - 2)]

                    def rho(v):
                        return [(v[H - 2 + j] - sum(
                            v[i] * AU[i][j] for i in range(H - 2))) % p
                            for j in range(2)]
                    be = rho([b['B'][k] % p for k in range(H)])
                    qq = rho([b['QP'][k] % p for k in range(H)])
                    Delta = (be[0] * qq[1] - be[1] * qq[0]) % p
                else:
                    Delta = '-'
                lines.append(f"{d} {n0} {p} {xi} {Delta} "
                             f"{int(pivok)} {rEBQ}/{H}")
    with open("Q196_D31_DATA.txt", "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Part-N data rows: {len(lines) - 1}", flush=True)


if __name__ == "__main__":
    main()
