"""Decision Transient Risk Monitor (DTRM), built from IM-299 -> IM-127."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
from scipy.linalg import expm


@dataclass(frozen=True)
class DecisionRiskResult:
    decision_pair: str
    nominal_gap: float
    uncertainty_radius: float
    directional_peak_gain: float
    peak_time: float
    transient_action_flip_index: float
    worst_gap_erosion: float
    certified_lower_gap: float
    status: str
    worst_initial_perturbation: list[float]
    propagation_mode: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FiniteHorizonEnvelope:
    initial_error: float
    growth_rate: float
    disturbance_bound: float
    horizon: float
    peak_state_error_bound: float
    peak_decision_error_bound: float
    nominal_gap: float
    action_flip_index_bound: float
    status: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def gronwall_decision_envelope(
    initial_error: float,
    growth_rate: float,
    disturbance_bound: float,
    horizon: float,
    decision_contrast_norm: float,
    nominal_gap: float,
) -> FiniteHorizonEnvelope:
    """Bound decision error when d||e||/dt <= L||e|| + disturbance_bound."""

    nonnegative = (initial_error, disturbance_bound, horizon, decision_contrast_norm)
    if any(value < 0 or not np.isfinite(value) for value in nonnegative):
        raise ValueError("Error, disturbance, horizon, and contrast values must be finite non-negative")
    if nominal_gap <= 0 or not np.isfinite(nominal_gap) or not np.isfinite(growth_rate):
        raise ValueError("nominal_gap must be positive and growth_rate finite")

    if abs(growth_rate) < 1e-14:
        end_bound = initial_error + disturbance_bound * horizon
    else:
        growth = float(np.exp(growth_rate * horizon))
        end_bound = initial_error * growth + disturbance_bound * (growth - 1.0) / growth_rate
    peak_state = max(initial_error, end_bound)
    peak_decision = decision_contrast_norm * peak_state
    index = peak_decision / nominal_gap
    return FiniteHorizonEnvelope(
        initial_error,
        growth_rate,
        disturbance_bound,
        horizon,
        peak_state,
        peak_decision,
        nominal_gap,
        index,
        "ENVELOPE_CERTIFIES_ACTION" if index < 1.0 else "ENVELOPE_CANNOT_EXCLUDE_ACTION_FLIP",
    )


def _matrix(value: Sequence[Sequence[float]], name: str) -> np.ndarray:
    matrix = np.asarray(value, dtype=float)
    if matrix.ndim != 2 or not np.all(np.isfinite(matrix)):
        raise ValueError(f"{name} must be a finite matrix")
    return matrix


def _vector(value: Sequence[float], size: int, name: str) -> np.ndarray:
    vector = np.asarray(value, dtype=float)
    if vector.shape != (size,) or not np.all(np.isfinite(vector)):
        raise ValueError(f"{name} must be a finite vector of length {size}")
    return vector


class DecisionTransientRiskMonitor:
    """Map bounded present uncertainty to finite-horizon action-flip risk."""

    def __init__(
        self,
        uncertainty_map: Sequence[Sequence[float]],
        uncertainty_radius: float,
        horizon: float,
        grid_points: int = 4001,
    ) -> None:
        self.W = _matrix(uncertainty_map, "uncertainty_map")
        if uncertainty_radius <= 0 or not np.isfinite(uncertainty_radius):
            raise ValueError("uncertainty_radius must be finite and positive")
        if horizon <= 0 or not np.isfinite(horizon):
            raise ValueError("horizon must be finite and positive")
        if grid_points < 2:
            raise ValueError("grid_points must be at least two")
        self.radius = float(uncertainty_radius)
        self.horizon = float(horizon)
        self.times = np.linspace(0.0, horizon, grid_points)

    def _finish(
        self,
        name: str,
        gap: float,
        rows: Sequence[np.ndarray],
        mode: str,
    ) -> DecisionRiskResult:
        if gap <= 0 or not np.isfinite(gap):
            raise ValueError("nominal_gap must be finite and positive")
        gains = np.asarray([np.linalg.norm(row, ord=2) for row in rows])
        peak_index = int(np.argmax(gains))
        peak_gain = float(gains[peak_index])
        peak_row = np.asarray(rows[peak_index])
        if peak_gain > 0:
            latent_direction = -self.radius * peak_row / peak_gain
        else:
            latent_direction = np.zeros(self.W.shape[1])
        initial_perturbation = self.W @ latent_direction
        erosion = self.radius * peak_gain
        lower_gap = float(gap - erosion)
        index = float(erosion / gap)
        if index < 1.0 - 1e-12:
            status = "CERTIFIED_WITHIN_LINEAR_SHELL"
        elif index > 1.0 + 1e-12:
            status = "ACTION_FLIP_DIRECTION_EXISTS"
        else:
            status = "BOUNDARY_REQUIRES_REFINEMENT"
        return DecisionRiskResult(
            decision_pair=name,
            nominal_gap=float(gap),
            uncertainty_radius=self.radius,
            directional_peak_gain=peak_gain,
            peak_time=float(self.times[peak_index]),
            transient_action_flip_index=index,
            worst_gap_erosion=float(erosion),
            certified_lower_gap=lower_gap,
            status=status,
            worst_initial_perturbation=initial_perturbation.tolist(),
            propagation_mode=mode,
        )

    def analyze_common_flow(
        self,
        system_matrix: Sequence[Sequence[float]],
        decision_contrast: Sequence[float],
        nominal_gap: float,
        name: str = "preferred_vs_runner_up",
    ) -> DecisionRiskResult:
        A = _matrix(system_matrix, "system_matrix")
        if A.shape[0] != A.shape[1] or A.shape[0] != self.W.shape[0]:
            raise ValueError("System and uncertainty-map dimensions do not match")
        contrast = _vector(decision_contrast, A.shape[0], "decision_contrast")
        rows = [contrast @ expm(A * time) @ self.W for time in self.times]
        return self._finish(name, nominal_gap, rows, "common_flow")

    def analyze_action_branches(
        self,
        system_a: Sequence[Sequence[float]],
        output_a: Sequence[float],
        system_b: Sequence[Sequence[float]],
        output_b: Sequence[float],
        nominal_gap: float,
        name: str = "action_a_vs_action_b",
    ) -> DecisionRiskResult:
        A_a = _matrix(system_a, "system_a")
        A_b = _matrix(system_b, "system_b")
        if A_a.shape != A_b.shape or A_a.shape[0] != A_a.shape[1]:
            raise ValueError("Action-branch system matrices must be square and equal-sized")
        if A_a.shape[0] != self.W.shape[0]:
            raise ValueError("System and uncertainty-map dimensions do not match")
        q_a = _vector(output_a, A_a.shape[0], "output_a")
        q_b = _vector(output_b, A_b.shape[0], "output_b")
        rows = [
            (q_a @ expm(A_a * time) - q_b @ expm(A_b * time)) @ self.W
            for time in self.times
        ]
        return self._finish(name, nominal_gap, rows, "action_branch_difference")


def analyze_config(config: Mapping[str, Any]) -> dict[str, Any]:
    monitor = DecisionTransientRiskMonitor(
        uncertainty_map=config["uncertainty_map"],
        uncertainty_radius=float(config["uncertainty_radius"]),
        horizon=float(config["horizon"]),
        grid_points=int(config.get("grid_points", 4001)),
    )
    mode = config["mode"]
    if mode == "common_flow":
        result = monitor.analyze_common_flow(
            config["system_matrix"],
            config["decision_contrast"],
            float(config["nominal_gap"]),
            config.get("name", "preferred_vs_runner_up"),
        )
    elif mode == "action_branches":
        result = monitor.analyze_action_branches(
            config["system_a"],
            config["output_a"],
            config["system_b"],
            config["output_b"],
            float(config["nominal_gap"]),
            config.get("name", "action_a_vs_action_b"),
        )
    else:
        raise ValueError("mode must be common_flow or action_branches")
    return result.as_dict()


def run_file(input_path: Path, output_path: Path | None = None) -> dict[str, Any]:
    config = json.loads(input_path.read_text(encoding="utf-8"))
    result = analyze_config(config)
    if output_path is not None:
        output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result
