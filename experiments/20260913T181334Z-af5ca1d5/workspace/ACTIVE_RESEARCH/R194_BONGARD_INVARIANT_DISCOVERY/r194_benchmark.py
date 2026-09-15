from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

from invariant_scout import SparseInvariantScout, affine_quotient, balanced_accuracy, lifted_library


HERE = Path(__file__).resolve().parent
RELATIONS = ("linear_balance", "product_equality", "energy_balance", "orthogonality", "determinant")


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


def canonical_vector(rng: np.random.Generator, family: str, positive: bool) -> np.ndarray:
    d = rng.normal(size=5)
    bounded = lambda: rng.choice([-1.0, 1.0]) * rng.uniform(0.65, 1.8)
    if family == "linear_balance":
        d[3] = d[0] + d[1] - d[2]
    elif family == "product_equality":
        d[0], d[1], d[2] = bounded(), bounded(), bounded()
        d[3] = d[0] * d[1] / d[2]
    elif family == "energy_balance":
        d[0:2] *= 1.7
        radius = np.sqrt(d[0] ** 2 + d[1] ** 2)
        d[2] = rng.uniform(-0.75, 0.75) * radius
        d[3] = rng.choice([-1.0, 1.0]) * np.sqrt(max(radius**2 - d[2] ** 2, 1e-6))
    elif family == "orthogonality":
        d[0], d[1], d[2] = bounded(), bounded(), bounded()
        d[3] = -d[0] * d[1] / d[2]
    elif family == "determinant":
        d[0], d[1], d[2] = bounded(), bounded(), bounded()
        d[3] = d[1] * d[2] / d[0]
    elif family == "threshold_nonrelation":
        wanted = 1.0 if positive else -1.0
        d[0] = wanted * rng.uniform(0.15, 2.0)
        return d
    else:
        raise ValueError(family)
    if not positive:
        d[3] += rng.choice([-1.0, 1.0]) * rng.uniform(0.45, 1.25)
    return d


def generate_scenes(
    seed: int,
    family: str,
    n: int,
    positive: bool,
    noise: float,
    transform_range: float = 8.0,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    rows = []
    for _ in range(n):
        d = canonical_vector(rng, family, positive)
        z = np.concatenate([d, [0.0]])
        scale = float(np.exp(rng.uniform(-np.log(transform_range), np.log(transform_range))))
        shift = rng.uniform(-12.0, 12.0)
        z = scale * z + shift
        z += rng.normal(scale=noise * scale, size=len(z))
        rows.append(z)
    return np.asarray(rows)


def relation_truth(family: str) -> dict[str, float]:
    if family == "linear_balance":
        return {"d0": 1, "d1": 1, "d2": -1, "d3": -1}
    if family == "product_equality":
        return {"d0*d1": 1, "d2*d3": -1}
    if family == "energy_balance":
        return {"d0^2": 1, "d1^2": 1, "d2^2": -1, "d3^2": -1}
    if family == "orthogonality":
        return {"d0*d1": 1, "d2*d3": 1}
    if family == "determinant":
        return {"d0*d3": 1, "d1*d2": -1}
    return {}


def support_recovery(model: SparseInvariantScout, family: str) -> tuple[float, float]:
    relation = model.relation()
    if relation is None:
        return 0.0, 0.0
    found = {name: coeff for name, coeff in relation}
    truth = relation_truth(family)
    support_f1 = 2 * len(set(found) & set(truth)) / max(len(found) + len(truth), 1)
    union = sorted(set(found) | set(truth))
    a = np.array([found.get(k, 0.0) for k in union])
    b = np.array([truth.get(k, 0.0) for k in union])
    cosine = float(abs(np.dot(a, b)) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12))
    return float(support_f1), cosine


def polynomial_ridge(train_z, train_y, test_z, seed: int):
    f, _ = lifted_library(train_z)
    ft, _ = lifted_library(test_z)
    rng = np.random.default_rng(seed)
    pos, neg = np.flatnonzero(train_y == 1), np.flatnonzero(train_y == 0)
    rng.shuffle(pos)
    rng.shuffle(neg)
    fit_idx = np.concatenate([pos[: len(pos) // 2], neg[: len(neg) // 2]])
    dev_idx = np.concatenate([pos[len(pos) // 2 :], neg[len(neg) // 2 :]])
    best = (-1.0, None)
    for ridge in (0.001, 0.01, 0.1, 1.0, 10.0):
        a = np.column_stack([np.ones(len(fit_idx)), f[fit_idx]])
        reg = ridge * np.eye(a.shape[1])
        reg[0, 0] = 0.0
        beta = np.linalg.solve(a.T @ a + reg, a.T @ train_y[fit_idx])
        pred = (np.column_stack([np.ones(len(dev_idx)), f[dev_idx]]) @ beta >= 0.5).astype(np.int8)
        score = balanced_accuracy(pred, train_y[dev_idx])
        if score > best[0]:
            best = (score, ridge)
    a = np.column_stack([np.ones(len(f)), f])
    reg = best[1] * np.eye(a.shape[1])
    reg[0, 0] = 0.0
    beta = np.linalg.solve(a.T @ a + reg, a.T @ train_y)
    return (np.column_stack([np.ones(len(ft)), ft]) @ beta >= 0.5).astype(np.int8)


def rbf_ridge(train_z, train_y, test_z, seed: int):
    x = affine_quotient(train_z)
    xt = affine_quotient(test_z)
    rng = np.random.default_rng(seed + 91)
    pos, neg = np.flatnonzero(train_y == 1), np.flatnonzero(train_y == 0)
    rng.shuffle(pos)
    rng.shuffle(neg)
    fit_idx = np.concatenate([pos[: len(pos) // 2], neg[: len(neg) // 2]])
    dev_idx = np.concatenate([pos[len(pos) // 2 :], neg[len(neg) // 2 :]])

    def kernel(a, b, gamma):
        dist = ((a[:, None, :] - b[None, :, :]) ** 2).sum(axis=2)
        return np.exp(-gamma * dist)

    best = (-1.0, None, None)
    for gamma in (0.1, 0.3, 1.0, 3.0):
        kfit = kernel(x[fit_idx], x[fit_idx], gamma)
        kdev = kernel(x[dev_idx], x[fit_idx], gamma)
        for ridge in (0.01, 0.1, 1.0):
            alpha = np.linalg.solve(kfit + ridge * np.eye(len(fit_idx)), train_y[fit_idx])
            pred = (kdev @ alpha >= 0.5).astype(np.int8)
            score = balanced_accuracy(pred, train_y[dev_idx])
            if score > best[0]:
                best = (score, gamma, ridge)
    k = kernel(x, x, best[1])
    alpha = np.linalg.solve(k + best[2] * np.eye(len(x)), train_y)
    return (kernel(xt, x, best[1]) @ alpha >= 0.5).astype(np.int8)


def one_relation_case(seed: int, family: str, noise: float, n_each: int) -> dict:
    train_pos = generate_scenes(seed * 100 + 1, family, n_each, True, noise)
    train_neg = generate_scenes(seed * 100 + 2, family, n_each, False, noise)
    test_pos = generate_scenes(seed * 100 + 3, family, 500, True, noise, transform_range=30.0)
    test_neg = generate_scenes(seed * 100 + 4, family, 500, False, noise, transform_range=30.0)
    train_z = np.vstack([train_pos, train_neg])
    train_y = np.concatenate([np.ones(n_each, dtype=np.int8), np.zeros(n_each, dtype=np.int8)])
    test_z = np.vstack([test_pos, test_neg])
    test_y = np.concatenate([np.ones(500, dtype=np.int8), np.zeros(500, dtype=np.int8)])

    model = SparseInvariantScout().fit(train_z, train_y)
    pred = model.predict(test_z)
    invariant_accuracy = 0.0 if model.abstained_ else balanced_accuracy(pred, test_y)
    poly = polynomial_ridge(train_z, train_y, test_z, seed)
    rbf = rbf_ridge(train_z, train_y, test_z, seed)
    f1, cosine = support_recovery(model, family)
    return {
        "seed": seed,
        "family": family,
        "noise": noise,
        "n_each": n_each,
        "invariant_accuracy": invariant_accuracy,
        "polynomial_accuracy": balanced_accuracy(poly, test_y),
        "rbf_accuracy": balanced_accuracy(rbf, test_y),
        "support_f1": f1,
        "coefficient_cosine": cosine,
        "diagnostics": model.diagnostics(),
    }


def one_nonrelation_case(seed: int, noise: float = 0.02) -> dict:
    family = "threshold_nonrelation"
    n_each = 16
    pos = generate_scenes(90_000 + seed * 10, family, n_each, True, noise)
    neg = generate_scenes(90_001 + seed * 10, family, n_each, False, noise)
    z = np.vstack([pos, neg])
    y = np.concatenate([np.ones(n_each, dtype=np.int8), np.zeros(n_each, dtype=np.int8)])
    model = SparseInvariantScout().fit(z, y)
    return {"seed": seed, "diagnostics": model.diagnostics()}


def summarize(cases: list[dict], nonrelations: list[dict]) -> dict:
    n = len(cases)
    nonabstained = [c for c in cases if not c["diagnostics"]["abstained"]]
    return {
        "n_relation_cases": n,
        "nonabstained_relation_cases": len(nonabstained),
        "wins_vs_both_strong_baselines": sum(
            c["invariant_accuracy"] > max(c["polynomial_accuracy"], c["rbf_accuracy"])
            for c in cases
        ),
        "mean_invariant_accuracy": float(np.mean([c["invariant_accuracy"] for c in cases])),
        "mean_polynomial_accuracy": float(np.mean([c["polynomial_accuracy"] for c in cases])),
        "mean_rbf_accuracy": float(np.mean([c["rbf_accuracy"] for c in cases])),
        "exact_support_recovery": sum(c["support_f1"] > 0.999 for c in cases),
        "mean_coefficient_cosine": float(np.mean([c["coefficient_cosine"] for c in cases])),
        "nonrelation_abstentions": sum(c["diagnostics"]["abstained"] for c in nonrelations),
        "n_nonrelation_controls": len(nonrelations),
    }


def main():
    started = time.perf_counter()
    cases = []
    noises = (0.005, 0.02, 0.05)
    for seed in range(4):
        for family in RELATIONS:
            for noise in noises:
                cases.append(one_relation_case(seed, family, noise, n_each=16))
    nonrelations = [one_nonrelation_case(seed) for seed in range(24)]
    result = {
        "round": "R194_BONGARD_INVARIANT_DISCOVERY",
        "cases": cases,
        "nonrelation_controls": nonrelations,
        "summary": summarize(cases, nonrelations),
        "elapsed_seconds": time.perf_counter() - started,
    }
    (HERE / "R194_RESULT.json").write_text(json.dumps(jsonable(result), indent=2), encoding="utf-8")
    print(json.dumps(result["summary"], indent=2))
    print(f"elapsed_seconds={result['elapsed_seconds']:.3f}")


if __name__ == "__main__":
    main()
