"""Q196 canonical V2 implementation (orientation repair + canonical basis).

# RECONSTRUCTED BY MUSE — V2 NEW CODE (V1 package sealed, never modified).
# Frozen reuse (imported, hash-checked by driver): q195_exact_gamma (V3),
# schedule_L3 from the standalone cert.

§1: primal V_+ = left nullspace of (Jm - I), i.e. ker(Jm-I)^T, with
J(v) == v asserted per basis vector. V1 used the right nullspace; the
regression test below shows its basis is generally not J-fixed.
"""

import q195_exact_gamma as G
import q196_boundary_closure as Q6


def left_nullspace(M, p):
    """ker M^T for row-list M (primal fixed space convention)."""
    T = [[M[i][j] for i in range(len(M))] for j in range(len(M[0]))]
    basis, _ = Q6.fp_nullspace_rows(T, p)
    return basis


def check_J_fixed(Jm, v, p):
    return Q6.apply_Jmat(Jm, v, p) == [x % p for x in v]


def v1_orientation_regression(d, n0, p, xi, schedule_L3):
    """Returns (n_bad, n_total): V1 right-nullspace basis vectors failing
    J(v) == v. Demonstrates the V1 orientation bug."""
    r = 3 * d
    b = Q6.build_boundary(d, n0, p, xi, schedule_L3)
    bad = sum(1 for v in b['Vp'] if not check_J_fixed(b['Jm'], v, p))
    return bad, len(b['Vp'])


def canonical_basis(r, xi, p):
    """e_0 = 1; e_h = x^h - xi^h x^{r-h} for 1 <= h <= H-1. J-fixed."""
    H = (r + 1) // 2
    E = [[0] * r for _ in range(H)]
    E[0][0] = 1
    for h in range(1, H):
        E[h][h] = 1
        E[h][(r - h) % r] = (-pow(xi, h, p)) % p
    return E


def canonical_coords(f, H, p):
    """First H coefficients (valid for J-even f; verified by driver)."""
    return [f[k] % p for k in range(H)]


def mat_inv(A, p):
    """Exact inverse of square nonsingular A mod p (Gauss-Jordan)."""
    n = len(A)
    M = [list(map(lambda v: v % p, row)) + [1 if i == j else 0
                                            for j in range(n)]
         for i, row in enumerate(A)]
    for c in range(n):
        piv = next(i for i in range(c, n) if M[i][c] % p != 0)
        M[c], M[piv] = M[piv], M[c]
        inv = pow(M[c][c], p - 2, p)
        M[c] = [(v * inv) % p for v in M[c]]
        for i in range(n):
            if i != c and M[i][c] % p != 0:
                f = M[i][c]
                M[i] = [(a - f * b) % p for a, b in zip(M[i], M[c])]
    return [row[n:] for row in M]


def build_canonical(d, n0, p, xi, schedule_L3):
    """Canonical-coordinate Q196 objects for one sector."""
    r = 3 * d
    H = (r + 1) // 2
    b = Q6.build_boundary(d, n0, p, xi, schedule_L3)
    Jm = b['Jm']
    Vp = left_nullspace(
        [[(Jm[i][j] - (1 if i == j else 0)) % p for j in range(r)]
         for i in range(r)], p)
    assert len(Vp) == H
    for v in Vp:
        assert check_J_fixed(Jm, v, p), "primal basis not J-fixed"
    E0 = canonical_basis(r, xi, p)
    for v in E0:
        assert check_J_fixed(Jm, v, p), "canonical basis not J-fixed"
    assert G.fp_rank(E0, p) == H, "canonical basis not full rank"
    # reconstruction: J-even f == sum f_k e_k
    for v in Vp + b['E'] + [b['B'], b['QP']]:
        cc = canonical_coords(v, H, p)
        rec = [0] * r
        for k in range(H):
            if cc[k]:
                rec = [(a + cc[k] * e) % p
                       for a, e in zip(rec, E0[k])]
        assert rec == [x % p for x in v], "canonical coords fail"
    ME = [canonical_coords(y, H, p) for y in b['E']]
    assert len(ME) == H - 2
    return {'d': d, 'n0': n0, 'p': p, 'xi': xi, 'r': r, 'H': H,
            'base': b, 'ME': ME}
