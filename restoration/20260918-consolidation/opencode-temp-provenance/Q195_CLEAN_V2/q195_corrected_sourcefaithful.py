"""Q195 source-faithful harness, provisional reversal (Phase B4-B5, B9).

# RECONSTRUCTED BY MUSE FROM S1/Q193 SOURCE + PHASE-A PREHISTORY
# NOT AN ORIGINAL SAVED UNIONALPHA FILE
# STATUS: provisional diagnostic object. Uses plain coefficient-preserving
# edge reversal ONLY because the exact J_xi weight was NOT recovered
# (Phase A verdict). NOT the Q195 test. See Q195_SOURCE_CORRECTION.md.

Conventions (forced identification): (a,1) = h_a, (a,2) = q_a.
F* = {q_1..q_{d-1}} | {h_0..h_e} | {h_{d-1}=P}; t(h_a) = r-2-2a,
t(q_a) = r-1-2a. C = span of consecutive interior intervals starting at
T_1 (b_in excluded, last interval included); b_in, C, b_out separate.
Gamma[a,b] = tildeQ_b - tildeQ_a: NEW RECONSTRUCTION (not source).
"""

import numpy as np
import sympy as sp


# RECONSTRUCTED BY MUSE — mirrors filed q195_suffix_lift.physical_word
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


# RECONSTRUCTED BY MUSE — source-faithful F* (Phase B4)
def fstar_chronology(d):
    """Return (T, keys, b_in_pair, b_out_pair) with T_0 = P = h_{d-1}."""
    r = 3 * d
    e = (d - 1) // 2
    t = lambda kind, a: (r - 2 - 2 * a) if kind == 'h' else (r - 1 - 2 * a)
    keys = ([('q', a) for a in range(1, d)]
            + [('h', a) for a in range(e + 1)]
            + [('h', d - 1)])
    assert len(set(keys)) == len(keys), f"F* keys not distinct: {keys}"
    ordered = sorted(keys, key=lambda x: t(*x))
    T = [t(*x) for x in ordered]
    assert len(set(T)) == len(T), f"F* times not distinct: {T}"
    H = (r + 1) // 2
    assert len(T) == H, f"|F*| = {len(T)}, source requires H = {H}"
    return T, ordered, (ordered[0], ordered[1]), (ordered[-1], ('q', 0))


# RECONSTRUCTED BY MUSE — formal edge machinery (as V1, unchanged semantics)
def tildeQ(j, E, r):
    v = np.zeros(E, dtype=object)
    for i in range(j):
        v[i * r + j] += 1
    return v


def J_plain(v, E, r):
    """PROVISIONAL plain reversal [i->j]->[j->i]. NOT exact J_xi."""
    w = np.zeros(E, dtype=object)
    for idx, c in enumerate(v):
        if c == 0:
            continue
        i, j = divmod(idx, r)
        w[j * r + i] += c
    return w


def pi_row(i, j, P, r):
    D = P[j] - P[i] - 1
    q_, rem = divmod(D, r)
    row = np.zeros(r, dtype=object)
    row[rem] += (-1) ** (q_ % 2)
    return row


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


# RECONSTRUCTED BY MUSE — source-faithful common core (Phase B5)
def build_corrected_case(d, n0, schedule_L3, poly_shift_mul):
    r, n, s, R, P = physical_word(d, n0, schedule_L3, poly_shift_mul)
    T, keys, b_in_pair, b_out_pair = fstar_chronology(d)
    E = (r + 1) * r
    H = (r + 1) // 2
    C = [tildeQ(T[i + 1], E, r) - tildeQ(T[i], E, r)
         for i in range(1, len(T) - 1)]
    assert len(C) == H - 2 == 3 * ((d - 1) // 2), (len(C), H)
    b_in = tildeQ(T[1], E, r) - tildeQ(T[0], E, r)
    t_q0 = r - 1
    b_out = tildeQ(t_q0, E, r) - tildeQ(T[-1], E, r)
    Cr = [J_plain(g, E, r) for g in C]
    Af = np.array([pi_vec(g, P, r) for g in C]).T
    Ar = np.array([pi_vec(g, P, r, rev=True) for g in C]).T
    return {'d': d, 'n0': n0, 'r': r, 'P': P, 'T': T, 'keys': keys,
            'E': E, 'H': H, 'C': C, 'Cr': Cr, 'b_in': b_in, 'b_out': b_out,
            'A_fwd': Af, 'A_rev': Ar}
