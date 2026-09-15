"""Volcano Interior-Coupling Optimizer (VICO) v0.1."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class MonotonicityViolation:
    scenario: int
    low_coupling: float
    high_coupling: float
    low_value: float
    high_value: float
    required_direction: str
    violation: float


@dataclass(frozen=True)
class CouplingResult:
    couplings: tuple[float, ...]
    scenario_throughputs: tuple[tuple[float, ...], ...]
    aggregate_throughput: tuple[float, ...]
    selected_index: int
    selected_coupling: float
    selected_aggregate_throughput: float
    selected_worst_case_regret: float
    scenario_optimal_couplings: tuple[float, ...]
    activation_nondecreasing: bool
    release_nonincreasing: bool
    activation_violation: MonotonicityViolation | None
    release_violation: MonotonicityViolation | None
    interior_selected: bool
    selection_mode: str
    status: str

    def to_dict(self) -> dict:
        result = asdict(self)
        result["activation_violation"] = (
            None if self.activation_violation is None else asdict(self.activation_violation)
        )
        result["release_violation"] = (
            None if self.release_violation is None else asdict(self.release_violation)
        )
        return result


def _as_scenarios(values: Sequence[float] | Sequence[Sequence[float]], n: int, name: str) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    if array.ndim == 1:
        array = array[None, :]
    if array.ndim != 2 or array.shape[1] != n or not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must be a finite vector or scenario-by-coupling matrix")
    if np.any(array <= 0):
        raise ValueError(f"{name} must contain positive rates")
    return array


def _worst_violation(
    values: np.ndarray, couplings: np.ndarray, direction: str, tolerance: float
) -> tuple[bool, MonotonicityViolation | None]:
    worst = 0.0
    witness = None
    for scenario in range(values.shape[0]):
        for index in range(values.shape[1] - 1):
            change = float(values[scenario, index + 1] - values[scenario, index])
            violation = -change if direction == "NONDECREASING" else change
            if violation > worst:
                worst = violation
                witness = MonotonicityViolation(
                    scenario=scenario,
                    low_coupling=float(couplings[index]),
                    high_coupling=float(couplings[index + 1]),
                    low_value=float(values[scenario, index]),
                    high_value=float(values[scenario, index + 1]),
                    required_direction=direction,
                    violation=float(violation),
                )
    return worst <= tolerance, None if worst <= tolerance else witness


def optimize_coupling(
    couplings: Sequence[float],
    activation_rates: Sequence[float] | Sequence[Sequence[float]],
    release_rates: Sequence[float] | Sequence[Sequence[float]],
    *,
    scenario_weights: Sequence[float] | None = None,
    selection_mode: str = "EXPECTED_THROUGHPUT",
    tolerance: float = 1e-10,
) -> CouplingResult:
    """Select coupling when activation and release are serial opposing bottlenecks.

    Each completed unit must pass both stages, so scenario throughput is the harmonic serial rate
    ``1 / (1 / activation_rate + 1 / release_rate)``. Selection can maximize weighted expected
    throughput or minimize maximum scenario regret.
    """

    x = np.asarray(couplings, dtype=float)
    if x.ndim != 1 or x.size < 3 or not np.all(np.isfinite(x)) or np.any(np.diff(x) <= 0):
        raise ValueError("couplings must be a finite strictly increasing vector of length >= 3")
    if tolerance < 0:
        raise ValueError("tolerance must be nonnegative")
    activation = _as_scenarios(activation_rates, x.size, "activation_rates")
    release = _as_scenarios(release_rates, x.size, "release_rates")
    if activation.shape != release.shape:
        raise ValueError("activation and release must have the same number of scenarios")

    scenario_count = activation.shape[0]
    if scenario_weights is None:
        weights = np.full(scenario_count, 1.0 / scenario_count)
    else:
        weights = np.asarray(scenario_weights, dtype=float)
        if weights.shape != (scenario_count,) or np.any(weights < 0) or not np.all(np.isfinite(weights)) or weights.sum() <= 0:
            raise ValueError("scenario_weights must be finite, nonnegative, and have positive sum")
        weights = weights / weights.sum()

    activation_ok, activation_witness = _worst_violation(
        activation, x, "NONDECREASING", tolerance
    )
    release_ok, release_witness = _worst_violation(release, x, "NONINCREASING", tolerance)
    throughputs = 1.0 / (1.0 / activation + 1.0 / release)
    expected = weights @ throughputs
    scenario_best = np.max(throughputs, axis=1)
    regrets = scenario_best[:, None] - throughputs
    worst_regret = np.max(regrets, axis=0)

    mode = selection_mode.upper()
    if mode == "EXPECTED_THROUGHPUT":
        selected = int(np.argmax(expected))
    elif mode == "MINIMAX_REGRET":
        best_regret = np.min(worst_regret)
        candidates = np.flatnonzero(np.isclose(worst_regret, best_regret, atol=tolerance, rtol=0))
        selected = int(candidates[np.argmax(expected[candidates])])
    else:
        raise ValueError("selection_mode must be EXPECTED_THROUGHPUT or MINIMAX_REGRET")

    interior = 0 < selected < x.size - 1
    if not activation_ok or not release_ok:
        status = "OPPOSING_BOTTLENECK_ASSUMPTION_FAILED_WITH_WITNESS"
    elif interior:
        status = "INTERIOR_COUPLING_OPTIMUM_FOUND"
    else:
        status = "SEARCH_RANGE_MISSES_INTERIOR_OPTIMUM"

    scenario_indices = np.argmax(throughputs, axis=1)
    return CouplingResult(
        couplings=tuple(map(float, x)),
        scenario_throughputs=tuple(tuple(map(float, row)) for row in throughputs),
        aggregate_throughput=tuple(map(float, expected)),
        selected_index=selected,
        selected_coupling=float(x[selected]),
        selected_aggregate_throughput=float(expected[selected]),
        selected_worst_case_regret=float(worst_regret[selected]),
        scenario_optimal_couplings=tuple(map(float, x[scenario_indices])),
        activation_nondecreasing=activation_ok,
        release_nonincreasing=release_ok,
        activation_violation=activation_witness,
        release_violation=release_witness,
        interior_selected=interior,
        selection_mode=mode,
        status=status,
    )
