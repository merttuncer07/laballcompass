"""
Certificate 1: Rank-one serial theorem (report Theorem 3.1 / "Theorem 1")
Certificate 2: Generic rank-r closure H = Y(Omega^T Y)^{-1} Y^T (Theorem 4.1 / "Theorem 2")

Both are elementary linear-algebra claims and are fully reconstructable from
the report's explicit formulas, with no missing definitions. We verify them
by direct construction + simulation over many random instances.
"""
import numpy as np

rng = np.random.default_rng(0)

def check_rank_one(m, trials=200):
    s = np.ones(m)
    xk = [np.concatenate([np.ones(k), np.zeros(m - k)]) for k in range(m + 1)]
    ok = 0
    for _ in range(trials):
        v = rng.normal(size=m)
        v = v / np.linalg.norm(v)
        lam = rng.normal()
        H = lam * np.outer(v, v)
        ell = rng.normal(size=m)
        b = rng.normal()

        def f(z):
            return b + ell @ z + z @ H @ z

        if abs(s @ H @ s) < 1e-6:
            continue  # off chart, skip

        P = np.array([f(xk[k]) for k in range(m + 1)])
        N = np.array([f(xk[k] - s) for k in range(m + 1)])
        d = P - N

        # (Hs)_k = (d_k - d_{k-1})/2 for k=1..m ; index 0 entry not directly given by formula,
        # but Hs has m entries indexed 1..m in the paper's k=1..m convention (1-indexed).
        q = np.zeros(m)
        for k in range(1, m + 1):
            q[k - 1] = (d[k] - d[k - 1]) / 2.0

        H_true_s = H @ s
        if not np.allclose(q, H_true_s, atol=1e-6):
            print("  Hs reconstruction MISMATCH", q, H_true_s)
            continue

        H_rec = np.outer(q, q) / (s @ q)
        if not np.allclose(H_rec, H, atol=1e-6):
            print("  H reconstruction MISMATCH")
            continue

        b_rec = f(np.zeros(m))
        ell_rec = np.zeros(m)
        for k in range(1, m + 1):
            Hkk = H[k - 1, k - 1]
            cross = 2 * sum(H[k - 1, j - 1] for j in range(1, k))
            ell_rec[k - 1] = P[k] - P[k - 1] - Hkk - cross

        if not (np.isclose(b_rec, b, atol=1e-6) and np.allclose(ell_rec, ell, atol=1e-6)):
            print("  affine part MISMATCH", b_rec, b, ell_rec, ell)
            continue

        ok += 1
    return ok, trials


def check_rank_r_closure(m, r, trials=200):
    ok = 0
    for _ in range(trials):
        # random symmetric rank-r H
        Vfull = rng.normal(size=(m, r))
        H = Vfull @ Vfull.T
        # scale/shift eigenvalues so it's not accidentally PSD-degenerate in a bad way
        H = H - 0.3 * np.eye(m) @ np.zeros((m, m))  # no-op, keep PSD (rank r generically)
        Omega = rng.normal(size=(m, r))
        A = Omega.T @ H @ Omega
        if abs(np.linalg.det(A)) < 1e-8:
            continue
        Y = H @ Omega
        H_rec = Y @ np.linalg.inv(Omega.T @ Y) @ Y.T
        if np.allclose(H_rec, H, atol=1e-6):
            ok += 1
        else:
            print("  closure MISMATCH, resid norm =", np.linalg.norm(H_rec - H))
    return ok, trials


if __name__ == "__main__":
    print("=== Rank-one serial theorem ===")
    for m in [1, 2, 3, 5, 8]:
        ok, trials = check_rank_one(m, trials=100)
        print(f"m={m}: {ok}/{trials} instances verified exactly")

    print("\n=== Generic rank-r closure theorem ===")
    for (m, r) in [(4, 1), (5, 2), (6, 3), (8, 4), (10, 6)]:
        ok, trials = check_rank_r_closure(m, r, trials=100)
        print(f"m={m}, r={r}: {ok}/{trials} instances verified exactly")
