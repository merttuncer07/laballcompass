from __future__ import annotations

import json
import itertools
import math
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent


def ridge(x: np.ndarray, y: np.ndarray, lam: float = 1e-6, weights=None) -> np.ndarray:
    if weights is not None:
        root = np.sqrt(np.asarray(weights))[:, None]
        x = x * root
        y = y * root[:, 0]
    gram = x.T @ x
    scale = float(np.trace(gram)) / max(1, gram.shape[0])
    return np.linalg.solve(gram + lam * max(scale, 1e-12) * np.eye(gram.shape[0]), x.T @ y)


# ---------------------------------------------------------------------------
# HM-04: Pugachev conditional-moment filter -> compiled two-pass correction


REGIMES = ("gaussian", "skew", "mixture")


def observation(x: np.ndarray, cubic: float) -> np.ndarray:
    return x + cubic * x**3


def observation_derivative(x: np.ndarray, cubic: float) -> np.ndarray:
    return 1.0 + 3.0 * cubic * x**2


def _standard_prior(rng: np.random.Generator, regime: str, size) -> np.ndarray:
    if regime == "gaussian":
        return rng.normal(size=size)
    if regime == "skew":
        sigma = 0.62
        raw = np.exp(rng.normal(scale=sigma, size=size))
        mean = math.exp(0.5 * sigma**2)
        variance = (math.exp(sigma**2) - 1.0) * math.exp(sigma**2)
        return (raw - mean) / math.sqrt(variance)
    if regime == "mixture":
        sign = rng.choice(np.array([-1.0, 1.0]), size=size)
        raw = 0.88 * sign + rng.normal(scale=0.42, size=size)
        return raw / math.sqrt(0.88**2 + 0.42**2)
    raise ValueError(regime)


def _noise_spec(regime: str):
    if regime == "gaussian":
        return ((1.0, 0.34),)
    if regime == "skew":
        return ((0.90, 0.24), (0.10, 1.65))
    if regime == "mixture":
        return ((0.84, 0.28), (0.16, 1.25))
    raise ValueError(regime)


def _noise_variance(regime: str) -> float:
    return float(sum(weight * sigma**2 for weight, sigma in _noise_spec(regime)))


def _sample_noise(rng: np.random.Generator, regime: str, size) -> np.ndarray:
    components = _noise_spec(regime)
    if len(components) == 1:
        return rng.normal(scale=components[0][1], size=size)
    choose = rng.random(size) >= components[0][0]
    out = rng.normal(scale=components[0][1], size=size)
    out[choose] = rng.normal(scale=components[1][1], size=int(np.sum(choose)))
    return out


def _normal_pdf(x: np.ndarray, sigma: float) -> np.ndarray:
    return np.exp(-0.5 * (x / sigma) ** 2) / (math.sqrt(2.0 * math.pi) * sigma)


def _noise_likelihood(residual: np.ndarray, regime: str) -> np.ndarray:
    return sum(weight * _normal_pdf(residual, sigma) for weight, sigma in _noise_spec(regime))


def sample_conditional_problem(
    rng: np.random.Generator,
    regime: str,
    count: int,
    cubic: float = 0.18,
):
    mean = rng.uniform(-1.35, 1.35, count)
    scale = np.exp(rng.uniform(math.log(0.28), math.log(1.05), count))
    state = mean + scale * _standard_prior(rng, regime, count)
    measured = observation(state, cubic) + _sample_noise(rng, regime, count)
    return mean, scale, measured, state


def conditional_basis(
    mean: np.ndarray,
    scale: np.ndarray,
    measured: np.ndarray,
    cubic: float,
    noise_variance: float,
) -> np.ndarray:
    slope = observation_derivative(mean, cubic)
    innovation_scale = np.sqrt((slope * scale) ** 2 + noise_variance)
    residual = np.clip((measured - observation(mean, cubic)) / innovation_scale, -6.0, 6.0)
    return np.column_stack(
        [
            np.ones_like(mean),
            mean,
            scale,
            residual,
            residual**2,
            residual**3,
            residual**4,
            np.tanh(residual),
            np.sign(residual) * np.sqrt(np.abs(residual)),
            mean * residual,
            scale * residual,
            mean * residual**2,
            scale * residual**2,
            mean**2 * residual,
            np.exp(-0.5 * residual**2),
        ]
    )


def raw_polynomial_basis(mean: np.ndarray, scale: np.ndarray, measured: np.ndarray) -> np.ndarray:
    variables = np.column_stack([mean, scale, measured])
    columns = [np.ones(len(mean))]
    for degree in range(1, 5):
        for ids in itertools.combinations_with_replacement(range(3), degree):
            value = np.ones(len(mean))
            for index in ids:
                value *= variables[:, index]
            columns.append(value)
    return np.column_stack(columns)


def fit_standardized_linear(design: np.ndarray, target: np.ndarray):
    center = design.mean(axis=0)
    spread = np.maximum(design.std(axis=0), 1e-8)
    center[0], spread[0] = 0.0, 1.0
    normalized = (design - center) / spread
    coefficient = ridge(normalized, target, 2e-5)
    return center, spread, coefficient


@dataclass
class ConditionalMomentCompiler:
    center: np.ndarray
    spread: np.ndarray
    coefficient: np.ndarray
    cubic: float
    noise_variance: float

    def predict(self, mean, scale, measured, cubic: float | None = None):
        active_cubic = self.cubic if cubic is None else cubic
        basis = conditional_basis(
            np.asarray(mean), np.asarray(scale), np.asarray(measured), active_cubic, self.noise_variance
        )
        normalized = (basis - self.center) / self.spread
        correction = normalized @ self.coefficient
        return np.asarray(mean) + np.asarray(scale) * correction


def compile_conditional_moment(
    mean: np.ndarray,
    scale: np.ndarray,
    measured: np.ndarray,
    state: np.ndarray,
    cubic: float,
    noise_variance: float,
    robust: bool,
) -> ConditionalMomentCompiler:
    basis = conditional_basis(mean, scale, measured, cubic, noise_variance)
    center = basis.mean(axis=0)
    spread = basis.std(axis=0)
    center[0], spread[0] = 0.0, 1.0
    spread = np.maximum(spread, 1e-8)
    normalized = (basis - center) / spread
    target = (state - mean) / scale
    coefficient = ridge(normalized, target, 2e-5)
    if robust:
        residual = target - normalized @ coefficient
        robust_scale = np.median(np.abs(residual - np.median(residual))) / 0.67449
        weight = 1.0 / (1.0 + (residual / max(2.5 * robust_scale, 1e-6)) ** 2)
        coefficient = ridge(normalized, target, 2e-5, weight)
    return ConditionalMomentCompiler(center, spread, coefficient, cubic, noise_variance)


def ekf_predict(mean, scale, measured, cubic: float, noise_variance: float):
    slope = observation_derivative(mean, cubic)
    gain = scale**2 * slope / (slope**2 * scale**2 + noise_variance)
    return mean + gain * (measured - observation(mean, cubic))


def ukf_predict(mean, scale, measured, cubic: float, noise_variance: float):
    points = np.column_stack([mean, mean + math.sqrt(3.0) * scale, mean - math.sqrt(3.0) * scale])
    weights = np.array([2.0 / 3.0, 1.0 / 6.0, 1.0 / 6.0])
    observed_points = observation(points, cubic)
    observed_mean = observed_points @ weights
    dz = observed_points - observed_mean[:, None]
    dx = points - mean[:, None]
    covariance = np.sum(weights[None, :] * dx * dz, axis=1)
    observed_variance = np.sum(weights[None, :] * dz**2, axis=1) + noise_variance
    return mean + covariance / np.maximum(observed_variance, 1e-12) * (measured - observed_mean)


def importance_posterior_mean(
    rng: np.random.Generator,
    mean: np.ndarray,
    scale: np.ndarray,
    measured: np.ndarray,
    regime: str,
    cubic: float,
    particles: int = 2048,
) -> np.ndarray:
    out = np.zeros_like(mean)
    for begin in range(0, len(mean), 100):
        end = min(len(mean), begin + 100)
        eps = _standard_prior(rng, regime, (end - begin, particles))
        states = mean[begin:end, None] + scale[begin:end, None] * eps
        residual = measured[begin:end, None] - observation(states, cubic)
        likelihood = _noise_likelihood(residual, regime)
        weight_sum = np.sum(likelihood, axis=1)
        out[begin:end] = np.sum(likelihood * states, axis=1) / np.maximum(weight_sum, 1e-300)
    return out


def pugachev_trial(seed: int, regime: str, shifted: bool = False) -> dict:
    rng = np.random.default_rng(30000 + 101 * seed + REGIMES.index(regime))
    train = sample_conditional_problem(rng, regime, 30000, cubic=0.18)
    ols = compile_conditional_moment(*train, cubic=0.18, noise_variance=_noise_variance(regime), robust=False)
    robust = compile_conditional_moment(*train, cubic=0.18, noise_variance=_noise_variance(regime), robust=True)
    raw_center, raw_spread, raw_coefficient = fit_standardized_linear(
        raw_polynomial_basis(train[0], train[1], train[2]), train[3]
    )

    cubic_test = 0.24 if shifted else 0.18
    test = sample_conditional_problem(rng, regime, 1200, cubic=cubic_test)
    mean, scale, measured, state = test
    start = time.perf_counter()
    robust_pred = robust.predict(mean, scale, measured, cubic=cubic_test)
    compiled_us = 1e6 * (time.perf_counter() - start) / len(mean)
    ols_pred = ols.predict(mean, scale, measured, cubic=cubic_test)
    raw_design = raw_polynomial_basis(mean, scale, measured)
    raw_poly_pred = ((raw_design - raw_center) / raw_spread) @ raw_coefficient
    ekf = ekf_predict(mean, scale, measured, cubic_test, _noise_variance(regime))
    ukf = ukf_predict(mean, scale, measured, cubic_test, _noise_variance(regime))
    oracle = importance_posterior_mean(
        np.random.default_rng(80000 + seed), mean, scale, measured, regime, cubic_test
    )
    rmse = lambda pred: float(np.sqrt(np.mean((pred - state) ** 2)))
    return {
        "seed": seed,
        "regime": regime,
        "shifted_cubic": shifted,
        "ekf_rmse": rmse(ekf),
        "ukf_rmse": rmse(ukf),
        "compiled_ols_rmse": rmse(ols_pred),
        "compiled_robust_rmse": rmse(robust_pred),
        "raw_degree4_polynomial_rmse": rmse(raw_poly_pred),
        "importance_oracle_rmse": rmse(oracle),
        "compiled_microseconds_per_case": compiled_us,
    }


def run_pugachev() -> dict:
    cases = [
        pugachev_trial(seed, regime, shifted)
        for seed in range(6)
        for regime in REGIMES
        for shifted in (False, True)
    ]
    home = [c for c in cases if not c["shifted_cubic"]]
    shifted = [c for c in cases if c["shifted_cubic"]]
    non_gaussian = [c for c in home if c["regime"] != "gaussian"]
    compiled_ukf = sum(c["compiled_robust_rmse"] < c["ukf_rmse"] for c in non_gaussian)
    compiled_ekf = sum(c["compiled_robust_rmse"] < c["ekf_rmse"] for c in non_gaussian)
    within_oracle = sum(
        c["compiled_robust_rmse"] <= 1.12 * c["importance_oracle_rmse"] for c in home
    )
    robust_ols = sum(c["compiled_robust_rmse"] < c["compiled_ols_rmse"] for c in home)
    compiled_raw = sum(c["compiled_robust_rmse"] < c["raw_degree4_polynomial_rmse"] for c in home)
    shift_ukf = sum(c["compiled_robust_rmse"] < c["ukf_rmse"] for c in shifted)
    return {
        "cases": cases,
        "summary": {
            "home_case_count": len(home),
            "non_gaussian_compiled_beats_ukf": compiled_ukf,
            "non_gaussian_compiled_beats_ekf": compiled_ekf,
            "home_within_12pct_of_importance_oracle": within_oracle,
            "robust_second_pass_beats_ols": robust_ols,
            "compiled_beats_larger_raw_degree4_polynomial": compiled_raw,
            "shifted_compiled_beats_ukf": shift_ukf,
            "mean_home_ekf_rmse": float(np.mean([c["ekf_rmse"] for c in home])),
            "mean_home_ukf_rmse": float(np.mean([c["ukf_rmse"] for c in home])),
            "mean_home_compiled_rmse": float(np.mean([c["compiled_robust_rmse"] for c in home])),
            "mean_home_oracle_rmse": float(np.mean([c["importance_oracle_rmse"] for c in home])),
            "mean_home_raw_degree4_polynomial_rmse": float(
                np.mean([c["raw_degree4_polynomial_rmse"] for c in home])
            ),
            "median_compiled_microseconds_per_case": float(
                np.median([c["compiled_microseconds_per_case"] for c in cases])
            ),
            "status": (
                "CONDITIONAL_EXPECTATION_COMPILED_NON_GAUSSIAN_CAPABILITY_SHIFT_OPEN"
                if compiled_ukf >= 9 and within_oracle >= 12 and compiled_raw >= 12
                else "NOT_BROKEN"
            ),
        },
    }


# ---------------------------------------------------------------------------
# HM-09: Aizerman potential functions -> signed Gaussian moment condensation


def moons(rng: np.random.Generator, count: int, angle: float):
    label = rng.choice(np.array([-1.0, 1.0]), size=count)
    theta = rng.uniform(0.0, math.pi, count)
    x = np.empty((count, 2))
    positive = label > 0
    x[positive, 0] = np.cos(theta[positive])
    x[positive, 1] = np.sin(theta[positive])
    x[~positive, 0] = 1.0 - np.cos(theta[~positive])
    x[~positive, 1] = -np.sin(theta[~positive]) - 0.18
    x += rng.normal(scale=0.20, size=x.shape)
    rotation = np.array(
        [[math.cos(angle), -math.sin(angle)], [math.sin(angle), math.cos(angle)]]
    )
    return x @ rotation.T, label


class PotentialMemory:
    def __init__(self, budget: int | None, method: str, variance: float = 0.11, decay: float = 0.998):
        self.budget = budget
        self.method = method
        self.base_variance = variance
        self.decay = decay
        self.centers = np.empty((0, 2))
        self.weights = np.empty(0)
        self.variances = np.empty(0)

    def add(self, point: np.ndarray, label: float):
        self.weights *= self.decay
        self.centers = np.vstack([self.centers, point])
        self.weights = np.append(self.weights, label)
        self.variances = np.append(self.variances, self.base_variance)
        while self.budget is not None and len(self.weights) > self.budget:
            if self.method == "fifo":
                self._remove(0)
            elif self.method in ("centroid", "moment"):
                self._merge_closest_same_sign(preserve_variance=self.method == "moment")
            else:
                raise ValueError(self.method)

    def _remove(self, index: int):
        self.centers = np.delete(self.centers, index, axis=0)
        self.weights = np.delete(self.weights, index)
        self.variances = np.delete(self.variances, index)

    def _merge_closest_same_sign(self, preserve_variance: bool):
        best = None
        for sign in (-1, 1):
            ids = np.flatnonzero(np.sign(self.weights) == sign)
            if len(ids) < 2:
                continue
            points = self.centers[ids]
            distance = np.sum((points[:, None, :] - points[None, :, :]) ** 2, axis=2)
            distance[np.tril_indices(len(ids))] = np.inf
            flat = int(np.argmin(distance))
            left, right = np.unravel_index(flat, distance.shape)
            candidate = (float(distance[left, right]), int(ids[left]), int(ids[right]))
            if best is None or candidate[0] < best[0]:
                best = candidate
        if best is None:
            self._remove(int(np.argmin(np.abs(self.weights))))
            return
        _, i, j = best
        wi, wj = abs(self.weights[i]), abs(self.weights[j])
        total = wi + wj
        center = (wi * self.centers[i] + wj * self.centers[j]) / total
        if preserve_variance:
            vi = self.variances[i] + np.sum((self.centers[i] - center) ** 2) / 2.0
            vj = self.variances[j] + np.sum((self.centers[j] - center) ** 2) / 2.0
            variance = (wi * vi + wj * vj) / total
        else:
            variance = self.base_variance
        signed_total = math.copysign(total, self.weights[i])
        keep, remove = min(i, j), max(i, j)
        self.centers[keep] = center
        self.weights[keep] = signed_total
        self.variances[keep] = variance
        self._remove(remove)

    def score(self, x: np.ndarray) -> np.ndarray:
        distance = np.sum((x[:, None, :] - self.centers[None, :, :]) ** 2, axis=2)
        density = np.exp(-distance / (2.0 * self.variances[None, :]))
        density /= np.maximum(self.variances[None, :], 1e-9)
        return density @ self.weights


def aizerman_trial(seed: int, budget: int, drift: bool):
    rng = np.random.default_rng(50000 + 17 * seed + budget + 1000 * int(drift))
    models = {
        "full": PotentialMemory(None, "fifo"),
        "fifo": PotentialMemory(budget, "fifo"),
        "centroid": PotentialMemory(budget, "centroid"),
        "moment": PotentialMemory(budget, "moment"),
    }
    blocks, block_size = 12, 100
    for block in range(blocks):
        angle = 0.72 * block / (blocks - 1) if drift else 0.0
        x, y = moons(rng, block_size, angle)
        for point, label in zip(x, y):
            for model in models.values():
                model.add(point, label)
    final_angle = 0.72 if drift else 0.0
    test_x, test_y = moons(rng, 3000, final_angle)
    accuracy = {
        name: float(np.mean(np.where(model.score(test_x) >= 0, 1.0, -1.0) == test_y))
        for name, model in models.items()
    }
    return {
        "seed": seed,
        "budget": budget,
        "drift": drift,
        **{f"{name}_accuracy": value for name, value in accuracy.items()},
        "full_support": len(models["full"].weights),
        "bounded_support": len(models["moment"].weights),
    }


def run_aizerman() -> dict:
    cases = [
        aizerman_trial(seed, budget, drift)
        for seed in range(8)
        for budget in (8, 16, 32)
        for drift in (False, True)
    ]
    moment_fifo = sum(c["moment_accuracy"] > c["fifo_accuracy"] for c in cases)
    moment_centroid = sum(c["moment_accuracy"] > c["centroid_accuracy"] for c in cases)
    within_full = sum(c["moment_accuracy"] >= c["full_accuracy"] - 0.03 for c in cases)
    return {
        "cases": cases,
        "summary": {
            "case_count": len(cases),
            "moment_beats_fifo": moment_fifo,
            "moment_beats_centroid_merge": moment_centroid,
            "moment_within_3pct_of_full": within_full,
            "mean_full_accuracy": float(np.mean([c["full_accuracy"] for c in cases])),
            "mean_fifo_accuracy": float(np.mean([c["fifo_accuracy"] for c in cases])),
            "mean_centroid_accuracy": float(np.mean([c["centroid_accuracy"] for c in cases])),
            "mean_moment_accuracy": float(np.mean([c["moment_accuracy"] for c in cases])),
            "support_reduction": float(1.0 - cases[0]["bounded_support"] / cases[0]["full_support"]),
            "status": (
                "SUPPORT_GROWTH_BOUNDED_MOMENT_EDGE_UNPROVEN"
                if within_full >= 36 and moment_fifo >= 24
                else "NOT_BROKEN"
            ),
        },
    }


def run_all() -> dict:
    started = time.perf_counter()
    result = {"pugachev": run_pugachev(), "aizerman": run_aizerman()}
    result["elapsed_seconds"] = time.perf_counter() - started
    return result


if __name__ == "__main__":
    result = run_all()
    path = HERE / "R197_RESULT.json"
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({key: value["summary"] for key, value in result.items() if isinstance(value, dict)}, indent=2))
    print(f"wrote {path}")
