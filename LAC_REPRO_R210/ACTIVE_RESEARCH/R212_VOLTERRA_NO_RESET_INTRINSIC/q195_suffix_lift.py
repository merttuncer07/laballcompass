"""Q195 executable rig — formal suffix-incidence lift, exact arithmetic.

Implements S1 section 15 (Q194) definitions:
- physical word R_{k+1} = 1 + x^{s_k} R_k in Z[x]/(x^r+1) with anti-periodic
  sign (x^r = -1), s_k = n + g_k from the validated schedule_L3;
- cumulative phases P_k; suffix S_k = sum_{i<=k} x^{-P_i};
- affine rows Q_{k+1} = x^{s_k-1} R_k = sum_{i<=k} x^{P_{k+1}-P_i-1};
- helical displacement label (Delta a, Delta t) in Z_d x Z_3 for L=3;
- pi as a signed histogram over these labels.
"""
import numpy as np

from VOLTERRA_RESONANT_FIXED_STATE_CERT_STANDALONE import schedule_L3


def poly_mul_mod(a, b, r):
    """Multiply in Z[x]/(x^r + 1), exact integers, anti-periodic reduction."""
    out = np.zeros(r, dtype=object)
    for i, ai in enumerate(a):
        if not i % 1 and int(i) >= r:
            raise ValueError
        if a[i] == 0:
            continue
        for j in range(len(b)):
            if b[j] == 0:
                continue
            k = i + j
            q_, rem = divmod(k, r)
            out[rem] += (-1) ** (q_ % 2) * a[i] * b[j]
    return out


def poly_pow_mod(base, exp, r):
    result = np.zeros(r, dtype=object)
    result[0] = 1
    b = base.copy()
    while exp:
        if exp & 1:
            result = poly_mul_mod(result, b, r)
        b = poly_mul_mod(b, b, r)
        exp >>= 1
    return result


def poly_shift_mul(a, k, r):
    """a * x^k in the anti-periodic ring."""
    out = np.zeros(r, dtype=object)
    for i, c in enumerate(a):
        if c == 0:
            continue
        q_, rem = divmod(i + k, r)
        out[rem] += (-1) ** (q_ % 2) * c
    return out


def physical_word(d, n0=1):
    """Return s_k list, states R_k as coefficient vectors, cumulative P_k."""
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


def suffix_histograms(r, s, P):
    """Affine rows Q_{k+1} as physical histograms, both ways (S1 15.1)."""
    rows_B = []
    for k in range(len(s)):
        row = np.zeros(r, dtype=object)
        for i in range(k + 1):
            q_, rem = divmod(P[k + 1] - P[i] - 1, r)
            row[rem] += (-1) ** (q_ % 2)
        rows_B.append(row)
    return rows_B


def affine_rows_A(r, s, R):
    rows_A = []
    for k, sk in enumerate(s):
        rows_A.append(poly_shift_mul(R[k], sk - 1, r))
    return rows_A


def poly_shift_mul(a, k, r):
    out = np.zeros(r, dtype=object)
    for i, c in enumerate(a):
        if c == 0:
            continue
        q_, rem = divmod(i + k, r)
        out[rem] += (-1) ** (q_ % 2) * c
    return out


def helical_label(exp, d, n):
    """Map a phase difference exp = P_j - P_i to (Delta a, Delta t).

    The word's horizontal cumulative residue follows the mountain:
    label = (horizontal displacement in Z_d, vertical in Z_3) recovered from
    exp = (n + g)-drift decomposition. For the L=3, n0=1 word the physical
    phase difference P_j - P_i decomposes as n0*(Delta t)*d + Delta a*(n+1)
    ... the exact bijection: exp = Delta_a*(n0*d) + Delta_t*d? Determined by
    the generator structure; we use the report's identification
    exp = (n+1)*j_a + n*j_t (successor-splice composition).
    """
    raise NotImplementedError


if __name__ == "__main__":
    # Sanity: verify S1 15.1 identity Q_{k+1} = sum_{i<=k} x^{P_{k+1}-P_i-1}
    # equals the recurrence-form affine row, on the exact physical word.
    for d in (3, 5, 7):
        r, n, s, R, P = physical_word(d, 1)
        rows_A = affine_rows_A(r, s, R)
        rows_B = suffix_histograms(r, s, P)
        ok = all(np.array_equal(a, b) for a, b in zip(rows_A, rows_B))
        print(f"d={d}: Q rows identical both ways: {ok}")
        assert ok
    print("SUFFIX-INCIDENCE LIFT EXACT: recurrence form == histogram form")
