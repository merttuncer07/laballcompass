"""R212 single decisive validation.

Runs every verified component of the R212 round in one process and writes
one named artifact: R212_VALIDATION.txt. No state-file edits; this script
and its output file are the end-to-end verification record.
"""
import io
import json
from contextlib import redirect_stdout
from pathlib import Path

import numpy as np

import intrinsic_no_reset as inr

HERE = Path(__file__).resolve().parent
results = []


def record(name, ok, detail=""):
    results.append({"name": name, "pass": bool(name is None or True) if False else bool(ok_val), "detail": detail} if False else {"name": name, "pass": bool(ok_val), "detail": detail})


def check(name, fn):
    try:
        detail = fn()
        results.append({"name": name, "pass": True, "detail": detail or ""})
    except Exception as exc:  # noqa: BLE001
        results.append({"name": name, "pass": False, "detail": f"{type(exc).__name__}: {exc}"})


def intrinsic_core():
    rng = np.random.default_rng(211)
    worst = 0.0
    for m in (4, 6, 9, 12):
        for _ in range(40):
            v = rng.normal(size=m); v /= np.linalg.norm(v)
            H = rng.normal() * np.outer(v, v)
            ell = rng.normal(size=m); b = rng.normal()
            if abs(np.ones(m) @ H @ np.ones(m)) < 1e-4:
                continue
            def f(z):
                return b + float(ell @ z) + float(z @ H @ z)
            W = np.array([f(z) for z in inr.sliding_windows(inr.rank_one_trajectory(m), m)])
            assert len(W) == inr.intrinsic_dimension(m, 1)
            b_hat, ell_hat, H_hat = inr.rank_one_recover(W, m)
            worst = max(worst, float(np.max(np.abs(H_hat - H))),
                        float(np.max(np.abs(ell_hat - ell))), abs(b_hat - b))
    assert worst < 1e-9, worst
    return f"160 rank-one cases, worst err {worst:.2e}"


def closure():
    rng = np.random.default_rng(5)
    worst = 0.0; tested = 0
    for _ in range(300):
        m = int(rng.integers(6, 14)); r = int(rng.integers(2, 5))
        Q, _ = np.linalg.qr(rng.normal(size=(m, r)))
        H = (Q * rng.normal(size=r)) @ Q.T
        Om = np.linalg.svd(rng.normal(size=(m - r, m)))[2].T[:, m - r:]
        if abs(np.linalg.det(Om.T @ H @ Om)) < 1e-3:
            continue
        worst = max(worst, float(np.max(np.abs(inr.rank_r_closure(H, Om) - H))))
        tested += 1
    assert worst < 1e-9, worst
    return f"{tested} valid charts, worst err {worst:.2e}"


def antipodal():
    for r in (5, 7, 9):
        T = inr.anti_periodic_T(r)
        assert np.allclose(np.linalg.matrix_power(T, r), -np.eye(r))
        assert np.allclose(np.linalg.matrix_power(T, 2 * r), np.eye(r))
        rng2 = np.random.default_rng(r)
        Hs = rng2.normal(size=(r, r)); Hs = (Hs + Hs.T) / 2
        ell = rng2.normal(size=r); b0 = rng2.normal()
        def f(z):
            return b0 + float(ell @ z) + float(z @ Hs @ z)
        aff, quad = inr.antipodal_separation(f, T, rng2.normal(size=r))
        assert np.allclose(aff[:r], -aff[r:]) and np.allclose(quad[:r], quad[r:])
    return "affine odd / quadratic even, exact, r=5,7,9"


def _run_script(name, marker):
    import subprocess
    import sys
    proc = subprocess.run(
        [sys.executable, "-B", str(HERE / name)],
        capture_output=True, text=True, timeout=1200,
    )
    out = proc.stdout + proc.stderr
    assert proc.returncode == 0, f"{name} exited {proc.returncode}: {out[-400:]}"
    assert marker in out, f"marker missing; tail: {out.strip().splitlines()[-1:]}"
    return out.strip().splitlines()[-1]


def phasezero_replay():
    return _run_script("phasezero_replay.py", "PHASE-ZERO SELF-CONTAINED REPLAY: PASS")


def bipartite():
    return _run_script("phasezero_bipartite_unimodular_standalone.py",
                       "PHASE-ZERO BIPARTITE UNIMODULAR STANDALONE CHECK: PASS")


def cubic_cert():
    return _run_script("resonant_boundary_cubic_cert.py",
                       "RESONANT SIX-BOUNDARY CUBIC CERTIFICATES: PASS")


def fixed_state_cert():
    return _run_script("VOLTERRA_RESONANT_FIXED_STATE_CERT_STANDALONE.py",
                       "ALL RESONANT FIXED-STATE CERTIFICATES PASS")


check("intrinsic_core", intrinsic_core)
check("rank_r_closure", closure)
check("antipodal_separation", antipodal)
check("phasezero_replay", phasezero_replay)
check("bipartite_unimodular", bipartite)
check("cubic_cert", cubic_cert)
check("fixed_state_cert", fixed_state_cert)

out = {"round": "R212", "date": "2026-09-18",
       "all_pass": all(r["pass"] for r in results), "results": results}
(HERE / "R212_VALIDATION.txt").write_text(
    "\n".join(f"{'PASS' if r['pass'] else 'FAIL'}  {r['name']}: {r['detail']}" for r in results)
    + f"\n\nALL {len(results)} CHECKS {'PASS' if out['all_pass'] else 'FAIL'}\n")
print((HERE / "R212_VALIDATION.txt").read_text())
