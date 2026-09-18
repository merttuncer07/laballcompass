"""Q195 recovered collision harness (Step 5).

# RECONSTRUCTED BY MUSE FROM ACCESSIBLE UNIONALPHA CHAT + Q193/Q194 SOURCE
# NOT AN ORIGINAL SAVED UNIONALPHA FILE

Reconstructs the experiment UnionAlpha actually ran in chat (transcript
Blocks 6-13, 16-18): consecutive-interior suffix-difference code over the
ordered F* chronology, edge-reversal reflection, anti-periodic physical
projection, exact joint-kernel tests over Q.

Conventions (see Q195_CONVENTIONS.md):
- P = h_{d-1} = R_d at prefix time d (S1 12.1). The historical mistake
  (transcript Block 7) forced q_{d-1} to time d; the fix (Block 8) uses the
  natural h/q time maps with NO override.
- Gamma[a,b] = tildeQ_b - tildeQ_a is a UnionAlpha reconstruction of the
  source's Gamma (the source never writes the edge formula). Marked as such.
- Exact arithmetic only: integer object arrays + SymPy exact rank/nullspace.
"""

import numpy as np
import sympy as sp

# RECONSTRUCTED BY MUSE FROM ACCESSIBLE UNIONALPHA CHAT + Q193/Q194 SOURCE
# NOT AN ORIGINAL SAVED UNIONALPHA FILE
# physical_word mirrors filed q195_suffix_lift.physical_word
# (SHA-256 82f8b1a036668cba641bb97659f937d3e0af0ac17c680314f24649090f2b81e1):
# R_0 = 1, R_{k+1} = 1 + x^{s_k} R_k in Z[x]/(x^r+1), P cumulative phases.
def physical_word(d, n0, schedule_L3, poly_shift_mul):
    r, n, e, U, B, F, Fs, g = schedule_L3(d, n0)
    s = [n + g[k] for k in range(r)]
    R = [np.zeros(r, dtype=object)]
    R[0][0] = 1
    for sk in s:
        nxt = poly_shift_mul(R[-1], sk, r)
        nxt[0] += 1
        R.append(nxt)
    P = [0]
    for sk in s:
        P.append(P[-1] + sk)
    return r, n, s, R, P


# RECONSTRUCTED BY MUSE FROM ACCESSIBLE UNIONALPHA CHAT + Q193/Q194 SOURCE
# NOT AN ORIGINAL SAVED UNIONALPHA FILE
def surface_chronology(d):
    """Ordered F* prefix times T (transcript Block 8, fixed convention).

    ts[('h',a)] = r-2-2a, ts[('q',a)] = r-1-2a; P = ('h',d-1); F = all h
    plus q for a <= e, minus ('h',0). NO time override. Returns (T, keys).
    """
    r = 3 * d
    ts = {}
    for a in range(d):
        ts[('h', a)] = r - 2 - 2 * a
        ts[('q', a)] = r - 1 - 2 * a
    e = (d - 1) // 2
    F = [('h', a) for a in range(d)] + [('q', a) for a in range(e + 1)]
    F = [x for x in F if x != ('h', 0)]
    allS = [('h', d - 1)] + [x for x in F if x != ('h', d - 1)]
    ordered = sorted(set(allS), key=lambda x: ts[x])
    return [ts[x] for x in ordered], ordered


# RECONSTRUCTED BY MUSE FROM ACCESSIBLE UNIONALPHA CHAT + Q193/Q194 SOURCE
# NOT AN ORIGINAL SAVED UNIONALPHA FILE
def tildeQ(j, E, r):
    """Formal suffix row: sum_{i<j} [i->j]; edge (i,j) at index i*r+j."""
    v = np.zeros(E, dtype=object)
    for i in range(j):
        v[i * r + j] += 1
    return v


# RECONSTRUCTED BY MUSE FROM ACCESSIBLE UNIONALPHA CHAT + Q193/Q194 SOURCE
# NOT AN ORIGINAL SAVED UNIONALPHA FILE
def forward_code(T, E, r):
    """C~-> = span of consecutive interior differences (transcript Block 8)."""
    return [tildeQ(T[i + 1], E, r) - tildeQ(T[i], E, r)
            for i in range(len(T) - 2)]


# RECONSTRUCTED BY MUSE FROM ACCESSIBLE UNIONALPHA CHAT + Q193/Q194 SOURCE
# NOT AN ORIGINAL SAVED UNIONALPHA FILE
def J_vec(v, E, r):
    """Weighted edge reversal J_xi: [i->j] -> [j->i] (transcript Block 13)."""
    w = np.zeros(E, dtype=object)
    for idx, c in enumerate(v):
        if c == 0:
            continue
        i, j = divmod(idx, r)
        w[j * r + i] += c
    return w


# RECONSTRUCTED BY MUSE FROM ACCESSIBLE UNIONALPHA CHAT + Q193/Q194 SOURCE
# NOT AN ORIGINAL SAVED UNIONALPHA FILE
def pi_row(i, j, P, r):
    """Physical projection of edge [i->j]: signed x^{P_j-P_i-1} histogram."""
    D = P[j] - P[i] - 1
    q_, rem = divmod(D, r)
    row = np.zeros(r, dtype=object)
    row[rem] += (-1) ** (q_ % 2)
    return row


# RECONSTRUCTED BY MUSE FROM ACCESSIBLE UNIONALPHA CHAT + Q193/Q194 SOURCE
# NOT AN ORIGINAL SAVED UNIONALPHA FILE
def pi_vec(v, P, r, rev=False):
    out = np.zeros(r, dtype=object)
    for idx, c in enumerate(v):
        if c == 0:
            continue
        i, j = divmod(idx, r)
        a, b = (j, i) if rev else (i, j)
        out = out + c * pi_row(a, b, P, r)
    return out


def _sp(M):
    return sp.Matrix(np.asarray(M, dtype=int).tolist())


def exact_rank(M):
    return _sp(M).rank()


def exact_nullity(M):
    return _sp(M).nullspace()


# RECONSTRUCTED BY MUSE FROM ACCESSIBLE UNIONALPHA CHAT + Q193/Q194 SOURCE
# NOT AN ORIGINAL SAVED UNIONALPHA FILE
def build_case(d, n0, schedule_L3, poly_shift_mul):
    """Full per-case construction (transcript Block 8).

    Returns dict with r, T, keys, C_fwd, C_rev, A_fwd, A_rev, P, s.
    """
    r, n, s, R, P = physical_word(d, n0, schedule_L3, poly_shift_mul)
    T, keys = surface_chronology(d)
    assert len(set(T)) == len(T), f"repeated surface time: {T}"
    E = (r + 1) * r
    C_fwd = forward_code(T, E, r)
    C_rev = [J_vec(g, E, r) for g in C_fwd]
    A_fwd = np.array([pi_vec(g, P, r) for g in C_fwd]).T
    A_rev = np.array([pi_vec(g, P, r, rev=True) for g in C_fwd]).T
    return {'d': d, 'n0': n0, 'r': r, 'n': n, 's': s, 'P': P, 'T': T,
            'keys': keys, 'E': E, 'C_fwd': C_fwd, 'C_rev': C_rev,
            'A_fwd': A_fwd, 'A_rev': A_rev}


# RECONSTRUCTED BY MUSE FROM ACCESSIBLE UNIONALPHA CHAT + Q193/Q194 SOURCE
# NOT AN ORIGINAL SAVED UNIONALPHA FILE
def negative_control_enlarged_code(T, E, r):
    """All-pairwise interval generators (transcript Block 11)."""
    return [tildeQ(T[b], E, r) - tildeQ(T[a], E, r)
            for a in range(len(T)) for b in range(a + 1, len(T))]


# RECONSTRUCTED BY MUSE FROM ACCESSIBLE UNIONALPHA CHAT + Q193/Q194 SOURCE
# NOT AN ORIGINAL SAVED UNIONALPHA FILE
def edge_bin_stats(P, r, n0_unused=None):
    """Edge -> signed-bin census (transcript Block 10)."""
    from collections import Counter
    bins = {}
    for i in range(r + 1):
        for j in range(i + 1, r + 1):
            D = P[j] - P[i] - 1
            q_, rem = divmod(D, r)
            bins[(i, j)] = (rem, (-1) ** (q_ % 2))
    cnt = Counter(bins.values())
    multi = {k: v for k, v in cnt.items() if v > 1}
    return len(bins), len(cnt), (max(multi.values()) if multi else 1)


# RECONSTRUCTED BY MUSE FROM ACCESSIBLE UNIONALPHA CHAT + Q193/Q194 SOURCE
# NOT AN ORIGINAL SAVED UNIONALPHA FILE
def gap_label(gk, r):
    """Helical step label from gap value (transcript Block 16).

    1 -> (1,0); 0 -> (0,1); r-1 -> (-1,1); r or 2r -> (0,2).
    Raises on any other gap value (no invention beyond chat).
    """
    if gk == 1:
        return (1, 0)
    if gk == 0:
        return (0, 1)
    if gk == r - 1:
        return (-1, 1)
    if gk == r or gk == 2 * r:
        return (0, 2)
    raise ValueError(f"gap value outside chat map: {gk}")


# RECONSTRUCTED BY MUSE FROM ACCESSIBLE UNIONALPHA CHAT + Q193/Q194 SOURCE
# NOT AN ORIGINAL SAVED UNIONALPHA FILE
def integrate_walk(d, n0, schedule_L3):
    """Grid-coordinate walk from (0,0) (transcript Block 17)."""
    r = 3 * d
    n = d * n0
    _, _, _, _, _, _, _, g = schedule_L3(d, n0)
    coords = [(0, 0)]
    labels = []
    for k in range(r):
        da, dt = gap_label(g[k], r)
        labels.append((da, dt))
        a, t = coords[-1]
        coords.append(((a + da) % d, (t + dt) % 3))
    return coords, labels


# RECONSTRUCTED BY MUSE FROM ACCESSIBLE UNIONALPHA CHAT + Q193/Q194 SOURCE
# NOT AN ORIGINAL SAVED UNIONALPHA FILE
def edge_histograms(P, r):
    """Unsigned + signed full-cycle edge histograms (transcript Block 18)."""
    H = [0] * r
    S = [0] * r
    for i in range(r + 1):
        for j in range(i + 1, r + 1):
            D = P[j] - P[i] - 1
            q_, rem = divmod(D, r)
            H[rem] += 1
            S[rem] += (-1) ** (q_ % 2)
    return H, S


# RECONSTRUCTED BY MUSE FROM ACCESSIBLE UNIONALPHA CHAT + Q193/Q194 SOURCE
# NOT AN ORIGINAL SAVED UNIONALPHA FILE
def c_delta_representation(v, coords_prefix, P, r, d):
    """Width-3 c_delta representation for one formal vector v.

    NEW construction (chat never built this; Step 16 asks for it):
    edge [i->j] carries walk-displacement
    (delta, t) = ((a_j-a_i) mod d, (t_j-t_i) mod 3) from the recovered
    prefix walk; c[delta][t] sums its signed weight. Summing c over all
    (delta, t) through the edge->bin map regroups exactly the physical
    projection; the driver asserts this regroup identity.
    Returns (c, projected) with c[delta] = [c0, c1, c2].
    """
    c = [[0, 0, 0] for _ in range(d)]
    proj = [0] * r
    E = (r + 1) * r
    assert len(v) == E
    for idx, coeff in enumerate(v):
        if coeff == 0:
            continue
        i, j = divmod(idx, r)
        (ai, ti) = coords_prefix[i]
        (aj, tj) = coords_prefix[j]
        delta = (aj - ai) % d
        t = (tj - ti) % 3
        D = P[j] - P[i] - 1
        q_, rem = divmod(D, r)
        w = int(coeff) * ((-1) ** (q_ % 2))
        c[delta][t] += w
        proj[rem] += w
    return c, proj

