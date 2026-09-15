"""Calibration Width Controller (CWC)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class IntervalObservation:
    lower: float
    upper: float
    covered: bool
    width: float
    interval_score: float
    coverage_error: float


def interval_score(outcome: float, lower: float, upper: float, alpha: float) -> float:
    score = upper - lower
    if outcome < lower:
        score += (2.0 / alpha) * (lower - outcome)
    elif outcome > upper:
        score += (2.0 / alpha) * (outcome - upper)
    return float(score)


class CalibrationWidthController:
    """PI feedback on decomposed coverage error, operating in log-width space."""

    def __init__(
        self,
        target_coverage: float = 0.9,
        proportional_gain: float = 0.10,
        integral_gain: float = 0.004,
        coverage_memory: float = 0.04,
        integral_leak: float = 0.98,
        initial_multiplier: float = 1.645,
        multiplier_bounds: tuple[float, float] = (0.05, 20.0),
    ) -> None:
        self.target = float(target_coverage)
        self.kp = float(proportional_gain)
        self.ki = float(integral_gain)
        self.memory = float(coverage_memory)
        self.leak = float(integral_leak)
        self.minimum, self.maximum = map(float, multiplier_bounds)
        self.log_multiplier = float(np.log(initial_multiplier))
        self.coverage_ewma = self.target
        self.integral = 0.0

    @property
    def multiplier(self) -> float:
        return float(np.exp(self.log_multiplier))

    def interval(self, center: float, base_scale: float) -> tuple[float, float]:
        half_width = self.multiplier * float(base_scale)
        return float(center - half_width), float(center + half_width)

    def observe(self, outcome: float, center: float, base_scale: float) -> IntervalObservation:
        lower, upper = self.interval(center, base_scale)
        covered = lower <= outcome <= upper
        self.coverage_ewma = (1.0 - self.memory) * self.coverage_ewma + self.memory * float(covered)
        error = self.target - self.coverage_ewma
        self.integral = self.leak * self.integral + error
        self.log_multiplier += self.kp * error + self.ki * self.integral
        self.log_multiplier = float(np.clip(self.log_multiplier, np.log(self.minimum), np.log(self.maximum)))
        alpha = 1.0 - self.target
        return IntervalObservation(
            lower,
            upper,
            covered,
            upper - lower,
            interval_score(outcome, lower, upper, alpha),
            error,
        )


class RawIntervalScoreController:
    """Stochastic gradient control using the undecomposed instantaneous interval score."""

    def __init__(
        self,
        target_coverage: float = 0.9,
        learning_rate: float = 0.006,
        initial_half_width: float = 1.645,
        width_bounds: tuple[float, float] = (0.05, 20.0),
    ) -> None:
        self.target = float(target_coverage)
        self.alpha = 1.0 - self.target
        self.learning_rate = float(learning_rate)
        self.half_width = float(initial_half_width)
        self.minimum, self.maximum = map(float, width_bounds)

    def observe(self, outcome: float, center: float, base_scale: float = 1.0) -> IntervalObservation:
        # base_scale is accepted for interface parity; this controller acts on absolute width.
        lower, upper = center - self.half_width, center + self.half_width
        covered = lower <= outcome <= upper
        gradient = 2.0 if covered else 2.0 - 2.0 / self.alpha
        self.half_width = float(
            np.clip(self.half_width - self.learning_rate * gradient, self.minimum, self.maximum)
        )
        return IntervalObservation(
            float(lower),
            float(upper),
            covered,
            float(upper - lower),
            interval_score(outcome, lower, upper, self.alpha),
            self.target - float(covered),
        )


def summarize(observations: list[IntervalObservation], target: float, window: int = 100) -> dict[str, float]:
    hits = np.array([item.covered for item in observations], dtype=float)
    widths = np.array([item.width for item in observations])
    scores = np.array([item.interval_score for item in observations])
    kernel = np.ones(window) / window
    rolling = np.convolve(hits, kernel, mode="valid")
    return {
        "coverage": float(np.mean(hits)),
        "rolling_coverage_rmse": float(np.sqrt(np.mean((rolling - target) ** 2))),
        "mean_width": float(np.mean(widths)),
        "width_step_variability": float(np.std(np.diff(widths))),
        "mean_interval_score": float(np.mean(scores)),
    }

