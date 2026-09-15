from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

from omitted_chain_compiler import (
    OmittedEventChainCompiler,
    estimate_transition,
    invert_observed_transition,
    log_loss,
    observed_transition,
    row_stochastic,
)


HERE = Path(__file__).resolve().parent


def jsonable(v):
    if isinstance(v, dict):
        return {str(k): jsonable(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [jsonable(x) for x in v]
    if isinstance(v, np.ndarray):
        return v.tolist()
    if isinstance(v, (np.integer, np.floating)):
        return v.item()
    return v


def make_chain(seed: int, family: str, n_states: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    if family == "sticky":
        p = 0.62 * np.eye(n_states) + 0.38 * rng.dirichlet(np.ones(n_states), n_states)
    elif family == "cycle":
        p = np.full((n_states, n_states), 0.015)
        for i in range(n_states):
            p[i, i] += rng.uniform(0.10, 0.30)
            p[i, (i + 1) % n_states] += rng.uniform(0.48, 0.72)
            p[i, (i + 2) % n_states] += rng.uniform(0.03, 0.12)
        p /= p.sum(axis=1, keepdims=True)
    elif family == "sparse":
        p = np.zeros((n_states, n_states))
        for i in range(n_states):
            targets = rng.choice(n_states, size=min(3, n_states), replace=False)
            p[i, targets] = rng.dirichlet(np.ones(len(targets)) * 0.7)
            p[i, i] += 0.12
        p /= p.sum(axis=1, keepdims=True)
    else:
        raw = rng.gamma(0.6, 1.0, size=(n_states, n_states)) + 0.03
        p = raw / raw.sum(axis=1, keepdims=True)
    return p


def simulate(p: np.ndarray, n: int, rng: np.random.Generator) -> np.ndarray:
    out = np.empty(n, dtype=np.int64)
    out[0] = int(rng.integers(p.shape[0]))
    cdf = np.cumsum(p, axis=1)
    u = rng.random(n - 1)
    for t in range(1, n):
        out[t] = int(np.searchsorted(cdf[out[t - 1]], u[t - 1], side="right"))
    return out


def retain(states: np.ndarray, omission: float, rng: np.random.Generator) -> np.ndarray:
    mask = rng.random(len(states)) >= omission
    mask[0] = True
    mask[-1] = True
    return states[mask]


def stationary(p: np.ndarray) -> np.ndarray:
    n = len(p)
    a = np.vstack([p.T - np.eye(n), np.ones(n)])
    b = np.concatenate([np.zeros(n), [1.0]])
    return row_stochastic(np.linalg.lstsq(a, b, rcond=None)[0][None, :])[0]


def hitting(p: np.ndarray, start: int = 0, target: int | None = None) -> float:
    target = len(p) - 1 if target is None else target
    keep = [i for i in range(len(p)) if i != target]
    t = np.linalg.solve(np.eye(len(keep)) - p[np.ix_(keep, keep)], np.ones(len(keep)))
    return float(t[keep.index(start)])


def metric_bundle(phat: np.ndarray, p: np.ndarray, test: np.ndarray) -> dict:
    true_hit = hitting(p)
    return {
        "matrix_frobenius": float(np.linalg.norm(phat - p)),
        "true_step_log_loss": log_loss(phat, test),
        "stationary_l1": float(np.abs(stationary(phat) - stationary(p)).sum()),
        "hitting_relative_error": float(abs(hitting(phat) - true_hit) / true_hit),
    }


def tune_naive(retained_states: np.ndarray, n_states: int) -> tuple[np.ndarray, float]:
    split = int(len(retained_states) * 0.7)
    fit, dev = retained_states[:split], retained_states[split - 1 :]
    best = (float("inf"), None)
    for alpha in (0.05, 0.25, 1.0, 4.0, 12.0):
        q = estimate_transition(fit, n_states, alpha)
        candidate = (log_loss(q, dev), alpha)
        if candidate < best:
            best = candidate
    return estimate_transition(retained_states, n_states, best[1]), best[1]


def one_case(seed: int, family: str, n_states: int, omission: float, n_true: int) -> dict:
    p = make_chain(seed, family, n_states)
    rng = np.random.default_rng(40_000 + seed * 97 + int(omission * 100))
    train = simulate(p, n_true, rng)
    test = simulate(p, 20_000, rng)
    observed = retain(train, omission, rng)

    naive, naive_alpha = tune_naive(observed, n_states)
    raw_q = estimate_transition(observed, n_states, 0.25)
    raw_inverse = invert_observed_transition(raw_q, omission, project=True)
    compiler = OmittedEventChainCompiler(omission).fit(observed, n_states)

    misspecified = {}
    for delta in (-0.10, -0.05, 0.05, 0.10):
        supplied = float(np.clip(omission + delta, 0.0, 0.94))
        model = OmittedEventChainCompiler(supplied).fit(observed, n_states)
        misspecified[f"{delta:+.2f}"] = metric_bundle(model.transition_, p, test)

    return {
        "seed": seed,
        "family": family,
        "n_states": n_states,
        "omission": omission,
        "n_true": n_true,
        "n_retained": int(len(observed)),
        "naive_alpha": naive_alpha,
        "compiler_diagnostics": compiler.diagnostics(),
        "naive": metric_bundle(naive, p, test),
        "raw_full_inverse": metric_bundle(raw_inverse, p, test),
        "regularized_compiler": metric_bundle(compiler.transition_, p, test),
        "misspecified_omission": misspecified,
    }


def identifiability_probe() -> dict:
    p = make_chain(902, "sticky", 4)
    true_r = 0.55
    q = observed_transition(p, true_r)
    rows = []
    for assumed_r in np.linspace(0.0, 0.82, 42):
        candidate = invert_observed_transition(q, float(assumed_r), project=False)
        feasible = bool(candidate.min() >= -1e-10 and np.max(np.abs(candidate.sum(axis=1) - 1)) < 1e-9)
        forward_error = (
            float(np.max(np.abs(observed_transition(candidate, float(assumed_r)) - q)))
            if feasible
            else None
        )
        rows.append(
            {
                "assumed_omission": float(assumed_r),
                "feasible_chain": feasible,
                "forward_error": forward_error,
                "distance_from_true_p": float(np.linalg.norm(candidate - p)),
            }
        )
    feasible = [r for r in rows if r["feasible_chain"]]
    return {
        "true_omission": true_r,
        "feasible_assumed_rates": len(feasible),
        "feasible_range": [
            min(r["assumed_omission"] for r in feasible),
            max(r["assumed_omission"] for r in feasible),
        ],
        "max_forward_error_among_feasible": max(r["forward_error"] for r in feasible),
        "interpretation": "retained-state transition likelihood cannot select omission rate along this feasible algebraic path",
        "rows": rows,
    }


def speed_probe() -> dict:
    p = make_chain(77, "dense", 12)
    q = observed_transition(p, 0.65)
    times = []
    for _ in range(200):
        start = time.perf_counter()
        invert_observed_transition(q, 0.65)
        times.append(time.perf_counter() - start)
    return {
        "n_states": 12,
        "median_compile_microseconds": float(np.median(times) * 1e6),
        "max_population_error": float(
            np.max(np.abs(invert_observed_transition(q, 0.65, project=False) - p))
        ),
    }


def summarize(cases: list[dict]) -> dict:
    names = ("raw_full_inverse", "regularized_compiler")
    out = {}
    for name in names:
        out[name] = {
            "matrix_wins_vs_naive": sum(
                c[name]["matrix_frobenius"] < c["naive"]["matrix_frobenius"] for c in cases
            ),
            "logloss_wins_vs_naive": sum(
                c[name]["true_step_log_loss"] < c["naive"]["true_step_log_loss"] for c in cases
            ),
            "stationary_wins_vs_naive": sum(
                c[name]["stationary_l1"] < c["naive"]["stationary_l1"] for c in cases
            ),
            "hitting_wins_vs_naive": sum(
                c[name]["hitting_relative_error"] < c["naive"]["hitting_relative_error"]
                for c in cases
            ),
            "median_logloss_gain": float(
                np.median(
                    [c["naive"]["true_step_log_loss"] - c[name]["true_step_log_loss"] for c in cases]
                )
            ),
            "median_matrix_error_ratio": float(
                np.median([c[name]["matrix_frobenius"] / c["naive"]["matrix_frobenius"] for c in cases])
            ),
        }
    out["n_cases"] = len(cases)
    strengths = (0.0, 0.25, 0.5, 0.75, 0.90, 0.97, 0.995)
    out["selected_strength_counts"] = {
        str(s): sum(c["compiler_diagnostics"]["selected_inversion_strength"] == s for c in cases)
        for s in strengths
    }
    return out


def main():
    started = time.perf_counter()
    cases = []
    families = ("sticky", "cycle", "sparse", "dense")
    omissions = (0.20, 0.50, 0.75)
    sizes = (3_000, 15_000)
    for seed in range(12):
        family = families[seed % len(families)]
        n_states = 4 if seed % 2 == 0 else 7
        for omission in omissions:
            for n_true in sizes:
                cases.append(one_case(seed, family, n_states, omission, n_true))
    result = {
        "round": "R193_MARKOV_OMITTED_EVENT_COMPILER",
        "cases": cases,
        "summary": summarize(cases),
        "identifiability": identifiability_probe(),
        "speed": speed_probe(),
        "elapsed_seconds": time.perf_counter() - started,
    }
    (HERE / "R193_RESULT.json").write_text(json.dumps(jsonable(result), indent=2), encoding="utf-8")
    print(json.dumps(result["summary"], indent=2))
    print(json.dumps(result["identifiability"], indent=2)[:700])
    print(json.dumps(result["speed"], indent=2))
    print(f"elapsed_seconds={result['elapsed_seconds']:.3f}")


if __name__ == "__main__":
    main()
