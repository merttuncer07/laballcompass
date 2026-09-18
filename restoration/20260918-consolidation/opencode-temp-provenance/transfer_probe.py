"""Transfer fit-test probe (Q196 V5, Part 13 investigation).

For one sector: build lambda_star, compute moments m_a, fit per-species
affine maps on first 4 steps, verify on remaining steps. Exact arithmetic.
"""
import sys

sys.path.insert(0, '.')
import q195_exact_gamma as G
import q196_boundary_closure as Q6
from VOLTERRA_RESONANT_FIXED_STATE_CERT_STANDALONE import schedule_L3


def fp_elim(rows, p):
    M = [list(map(lambda v: v % p, row)) for row in rows]
    n = len(M[0]) - 1
    piv = []
    r_ = 0
    for c in range(n):
        q = next((i for i in range(r_, len(M)) if M[i][c] % p != 0), None)
        if q is None:
            continue
        M[r_], M[q] = M[q], M[r_]
        inv = pow(M[r_][c], p - 2, p)
        M[r_] = [(v * inv) % p for v in M[r_]]
        for i in range(len(M)):
            if i != r_ and M[i][c] % p != 0:
                f = M[i][c]
                M[i] = [(a - f * b) % p for a, b in zip(M[i], M[r_])]
        piv.append(c)
        r_ += 1
    return M, piv


def lambda_star(d, n0, p, xi):
    r = 3 * d
    H = (r + 1) // 2
    inv2 = pow(2, p - 2, p)
    bnd = Q6.build_boundary(d, n0, p, xi, schedule_L3)
    Jm = bnd['Jm']
    rows = [[(Jm[i][j] - (1 if i == j else 0)) % p for j in range(r)]
            for i in range(r)]
    Lam, _ = Q6.fp_nullspace_rows(rows, p)
    rr, _, s, R, P = G.int_word(d, n0, schedule_L3)
    T, _ = G.fstar_chronology(d)

    def ring_vec(Rh):
        v = [0] * r
        for e, vv in Rh.items():
            q_, rem = divmod(e, r)
            v[rem] = (v[rem] + ((-1) ** q_) * (vv % p)) % p
        return v

    Cvec = []
    for i in range(1, len(T) - 1):
        Gam, _, _ = G.centered_gamma(R, P, T[i], T[i + 1], xi, p)
        Cvec.append(G.reduce_qr(Gam, p, r))
    Gb, _, _ = G.centered_gamma(R, P, T[0], T[1], xi, p)
    bv_in = G.reduce_qr(Gb, p, r)
    sysrows = []
    for c in Cvec + [bv_in]:
        sysrows.append([sum(Lam[i][j] * c[j] for j in range(r)) % p
                        for i in range(H)] + [0])
    Rrm1 = ring_vec(R[r - 1])
    sysrows.append([(sum(Lam[i][j] * Rrm1[j] for j in range(r))
                     - Lam[i][0] * inv2) % p for i in range(H)] + [1])
    M, piv = fp_elim([row[:] for row in sysrows], p)
    if len(piv) != H:
        return None
    sol = [0] * H
    for i, c in enumerate(piv):
        sol[c] = M[i][H] % p
    lam = [0] * r
    for i, ai in enumerate(sol):
        if ai:
            lam = [(x + ai * y) % p for x, y in zip(lam, Lam[i])]
    return lam


def fit_verify(pairs, p):
    """Fit y = t.x + f per output coord on first 4 pairs; verify rest."""
    outs = []
    for j in range(3):
        eqs = [x + [1] for x, y in pairs[:4]]
        M, piv = fp_elim([row + [yy[j]] for row, yy in
                          zip(eqs, [y for _, y in pairs[:4]])], p)
        if len(piv) < 4:
            return None
        sol = [0] * 4
        for i, c in enumerate(piv):
            sol[c] = M[i][4] % p
        tj, fj = sol[:3], sol[3]
        for (x, y) in pairs[4:]:
            if (sum(tj[k] * x[k] for k in range(3)) + fj) % p != y[j] % p:
                return None
        outs.append((tj, fj))
    return outs


if __name__ == "__main__":
    for (d, n0, p, xi) in [(15, 1, 271, 44), (11, 1, 199, 125)]:
        r = 3 * d
        lam = lambda_star(d, n0, p, xi)
        if lam is None:
            print(f"d={d}: NO LSTAR")
            continue
        ee = (d - 1) // 2
        mom = {}
        for a in range(d):
            mom[a] = [lam[a + d * t] % p for t in range(3)]
        for sgn, aa in [("+", [a for a in range(1, d) if a > ee]),
                        ("-", [a for a in range(1, d) if a <= ee])]:
            pairs = [(mom[a], mom[a - 1]) for a in aa]
            res = fit_verify(pairs, p)
            print(f"d={d} n0={n0} species {sgn} ({len(pairs)} steps): "
                  f"{'TRANSFER-EXISTS' if res else 'no-fit'}")
