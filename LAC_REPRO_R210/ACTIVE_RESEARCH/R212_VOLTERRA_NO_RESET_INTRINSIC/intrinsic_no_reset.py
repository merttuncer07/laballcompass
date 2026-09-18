"""R212: intrinsic-count no-reset identification, executable core.

Implements the ALAN Volterra line's proved constructions as runnable code:
- rank-one serial theorem: 2m+1 sliding-window outputs -> (b, ell, H), rank 1,
  chart s^T H s != 0 (verified exact in R212 audit).
- rank-r closure: H = Y (Omega^T Y)^{-1} Y^T on det(Omega^T H Omega) != 0.
- anti-periodic recurrence T^r = -I state walk and 2r antipodal separation.
"""

from __future__ import annotations

import numpy as np


def sliding_windows(u, m):
    u = np.asarray(u, dtype=float)
    return np.array([u[t:t + m] for t in range(len(u) - m + 1)])


def rank_one_trajectory(m):
    """m copies of -1, m zeros, m copies of +1 -> 2m+1 = D_{m,1} windows."""
    return np.concatenate([-np.ones(m), np.zeros(m), np.ones(m)])


def rank_one_recover(windows, m):
    """Recover (b, ell, H-hat via q) from raw window outputs only.

    windows: outputs f(z_t) for the 2m+1 consecutive windows, in walk order.
    Returns q = H s (with H the rank-1 kernel), then H = q q^T / (s^T q).
    """
    s = np.ones(m)
    P = windows[m:]              # f(y_k), k = 0..m   (z_{m+k} = y_k)
    N = windows[:m]              # f(y_k - s), k = 0..m-1
    d = P[:m] - N
    d_m = windows[-1] - windows[m]          # f(y_m) - f(y_m - s) = f(s) - f(0)
    q = np.empty(m)
    for k in range(1, m):
        q[m - k] = (d[k] - d[k - 1]) / 2.0    # y_k - y_{k-1} = e_{m-k}
    q[0] = (d_m - d[m - 1]) / 2.0             # y_m - y_{m-1} = e_0
    H = np.outer(q, q) / (s @ q)
    ell = np.empty(m)
    Hr = H
    for k in range(1, m + 1):
        pos = m - k
        ell[pos] = P[k] - P[k - 1] - Hr[pos, pos] - 2.0 * np.sum(Hr[pos, pos + 1:])
    b = P[0]
    return b, ell, H


def rank_r_closure(H, Omega):
    Y = H @ Omega
    return Y @ np.linalg.inv(Omega.T @ Y) @ Y.T


def anti_periodic_T(r):
    T = np.zeros((r, r))
    T[0, r - 1] = -1.0
    for i in range(1, r):
        T[i, i - 1] = 1.0
    return T


def antipodal_separation(f, T, R):
    r = T.shape[0]
    out_aff, out_quad = [], []
    for t in range(2 * r):
        zt = np.linalg.matrix_power(T, int(t)) @ R
        out_aff.append((f(zt) - f(-zt)) / 2.0)
        out_quad.append((f(zt) + f(-zt)) / 2.0 - f(np.zeros(r)))
    return np.array(out_aff), np.array(out_quad)


def intrinsic_dimension(m, r):
    return 1 + m + m * r - r * (r - 1) // 2
