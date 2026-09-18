"""Q196 boundary-closure harness (faithful reconstruction of pending UnionAlpha
computation — NOT a recovered UnionAlpha result).

# RECONSTRUCTED BY MUSE FROM S1/Q193 SOURCE + FROZEN V3/V4 MACHINERY
# V1-V4 packages and q195_exact_gamma.py are NEVER modified here.

Reuses (imported, hash-checked by driver): int_word, centered_gamma,
reduce_qr, J_poly, fstar_chronology, fp_rank from q195_exact_gamma.
"""

import q195_exact_gamma as G


def polymod_mul(a, b, p, r):
    """Multiply length-r vectors mod (x^r + 1) over F_p."""
    out = [0] * r
    for i, x in enumerate(a):
        if x == 0:
            continue
        for j, y in enumerate(b):
            if y == 0:
                continue
            q_, rem = divmod(i + j, r)
            out[rem] = (out[rem] + ((-1) ** q_) * x * y) % p
    return out


def fp_nullspace_rows(M, p):
    """Basis for {x : M x = 0}, M given as row list. Exact mod p."""
    A = [list(map(lambda v: v % p, row)) for row in M]
    m = len(A)
    n = len(A[0]) if m else 0
    pivots, row_of = [], {}
    r_ = 0
    for c in range(n):
        piv = next((i for i in range(r_, m) if A[i][c] % p != 0), None)
        if piv is None:
            continue
        A[r_], A[piv] = A[piv], A[r_]
        inv = pow(A[r_][c], p - 2, p)
        A[r_] = [(v * inv) % p for v in A[r_]]
        for i in range(m):
            if i != r_ and A[i][c] % p != 0:
                f = A[i][c]
                A[i] = [(a - f * b) % p for a, b in zip(A[i], A[r_])]
        pivots.append(c)
        row_of[c] = r_
        r_ += 1
    free = [c for c in range(n) if c not in row_of]
    basis = []
    for f in free:
        x = [0] * n
        x[f] = 1
        for c in pivots:
            x[c] = (-A[row_of[c]][f]) % p
        basis.append(x)
    return basis, pivots


def J_matrix(r, xi, p):
    """Matrix rows of J_xi built from the verified J_poly (single source
    of truth): row h = J applied to basis vector e_h. (An earlier
    hand-written version put xi^h where xi^{(r-h)%r} belongs; both square
    to I, so only the in-V_+ membership check catches it.)"""
    M = []
    for h in range(r):
        e = {h: 1}
        M.append(G.J_poly(e, xi, p, r))
    return M


def apply_Jmat(Jm, v, p):
    """Apply J: J(v) = sum_j v_j * Jm[j] (rows are J-images of basis).
    NOTE: rows dotted against v (Jm v) is WRONG for nonsymmetric J;
    both square to I, so only cross-checks against J_poly catch it."""
    r = len(v)
    out = [0] * r
    for j in range(r):
        if v[j] % p:
            out = [(a + v[j] * b) % p for a, b in zip(out, Jm[j])]
    return out


def fp_row_pivots(rows, p):
    """Pivot columns of the row space (for faithful coordinate restriction)."""
    A = [list(map(lambda v: v % p, row)) for row in rows]
    m = len(A)
    n = len(A[0]) if m else 0
    pivots = []
    r_ = 0
    for c in range(n):
        piv = next((i for i in range(r_, m) if A[i][c] % p != 0), None)
        if piv is None:
            continue
        A[r_], A[piv] = A[piv], A[r_]
        inv = pow(A[r_][c], p - 2, p)
        A[r_] = [(v * inv) % p for v in A[r_]]
        for i in range(m):
            if i != r_ and A[i][c] % p != 0:
                f = A[i][c]
                A[i] = [(a - f * b) % p for a, b in zip(A[i], A[r_])]
        pivots.append(c)
        r_ += 1
    return pivots


# RECONSTRUCTED boundary objects for one (d, n0, p, xi) sector.
def build_boundary(d, n0, p, xi, schedule_L3):
    r, _, s, R, P = G.int_word(d, n0, schedule_L3)
    T, keys = G.fstar_chronology(d)
    H = (r + 1) // 2
    assert len(T) == H and len(set(T)) == len(T)

    def gvec(a, b):
        Gam, _, _ = G.centered_gamma(R, P, a, b, xi, p)
        return G.reduce_qr(Gam, p, r)

    def Jv(v):
        return G.J_poly(dict(enumerate(v)), xi, p, r)

    C = [gvec(T[i], T[i + 1]) for i in range(1, len(T) - 1)]
    assert len(C) == H - 2
    b_in = gvec(T[0], T[1])
    b_out = gvec(T[-1], r - 1)
    E = [[(c + j) % p for c, j in zip(v, Jv(v))] for v in C]
    B = [(c + j) % p for c, j in zip(b_in, Jv(b_in))]
    Bout = [(c + j) % p for c, j in zip(b_out, Jv(b_out))]

    # P-state vector + quadratic anchor Q^P = P * J(P)
    Pvec = [0] * r
    for e, vv in R[d].items():
        q_, rem = divmod(e, r)
        Pvec[rem] = (Pvec[rem] + ((-1) ** q_) * (vv % p)) % p
    JP = Jv(Pvec)
    QP = polymod_mul(Pvec, JP, p, r)

    Jm = J_matrix(r, xi, p)
    Vp, _ = fp_nullspace_rows(
        [[(Jm[i][j] - (1 if i == j else 0)) % p for j in range(r)]
         for i in range(r)], p)
    # pivot columns of the V_+ BASIS ITSELF (restriction is an iso on V_+;
    # pivots of the constraint matrix would be wrong here)
    piv = fp_row_pivots(Vp, p)
    assert len(piv) == len(Vp), (len(piv), len(Vp))
    Vm, _ = fp_nullspace_rows(
        [[(Jm[i][j] + (1 if i == j else 0)) % p for j in range(r)]
         for i in range(r)], p)

    def coords(y):
        return [y[c] % p for c in piv]

    return {'d': d, 'n0': n0, 'p': p, 'xi': xi, 'r': r, 'H': H,
            'C': C, 'b_in': b_in, 'b_out': b_out, 'E': E, 'B': B,
            'Bout': Bout, 'Pvec': Pvec, 'QP': QP, 'Jm': Jm,
            'Vp': Vp, 'Vm': Vm, 'piv': piv, 'coords': coords}
