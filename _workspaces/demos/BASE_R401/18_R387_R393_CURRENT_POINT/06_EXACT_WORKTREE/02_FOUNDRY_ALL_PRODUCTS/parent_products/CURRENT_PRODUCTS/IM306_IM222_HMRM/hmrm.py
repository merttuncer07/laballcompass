"""Hidden-Mode Resilience Monitor (HMRM)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ModeRisk:
    eigenvalue_magnitude: float
    modal_time_constant: float
    current_exposure: float
    recovery_steps: int
    joint_alert: bool


@dataclass(frozen=True)
class ResilienceAssessment:
    observed_scalar_distance: float
    scalar_only_alert: bool
    recovery_only_alert: bool
    joint_alert: bool
    modes: tuple[ModeRisk, ...]


def fit_transition(states: np.ndarray, ridge: float = 1e-8) -> np.ndarray:
    """Fit ``x[t+1] = A x[t]`` from a state trajectory."""
    data = np.asarray(states, dtype=float)
    if data.ndim != 2 or data.shape[0] < 3:
        raise ValueError("states must contain at least three time points")
    previous = data[:-1].T
    following = data[1:].T
    gram = previous @ previous.T + ridge * np.eye(previous.shape[0])
    return following @ previous.T @ np.linalg.inv(gram)


class HiddenModeResilienceMonitor:
    """Combine modal exposure and recovery horizon instead of alarming on either alone."""

    def __init__(
        self,
        minimum_exposure: float,
        minimum_recovery_steps: int,
        recovery_floor: float,
        scalar_alarm_distance: float,
    ) -> None:
        if minimum_exposure <= 0 or recovery_floor <= 0:
            raise ValueError("exposure thresholds must be positive")
        self.minimum_exposure = float(minimum_exposure)
        self.minimum_recovery_steps = int(minimum_recovery_steps)
        self.recovery_floor = float(recovery_floor)
        self.scalar_alarm_distance = float(scalar_alarm_distance)

    def assess(
        self,
        transition: np.ndarray,
        state_deviation: np.ndarray,
        observed_direction: np.ndarray,
        consequence_matrix: np.ndarray | None = None,
    ) -> ResilienceAssessment:
        matrix = np.asarray(transition, dtype=float)
        state = np.asarray(state_deviation, dtype=float)
        observed = np.asarray(observed_direction, dtype=float)
        consequence = np.eye(state.size) if consequence_matrix is None else np.atleast_2d(consequence_matrix)
        eigenvalues, eigenvectors = np.linalg.eig(matrix)
        if np.max(np.abs(eigenvalues.imag)) > 1e-8 or np.max(np.abs(eigenvectors.imag)) > 1e-8:
            raise ValueError("v0.1 requires a real diagonalizable modal representation")
        eigenvalues = eigenvalues.real
        eigenvectors = eigenvectors.real
        eigenvectors = eigenvectors / np.linalg.norm(eigenvectors, axis=0, keepdims=True)
        coefficients = np.linalg.solve(eigenvectors, state)
        risks: list[ModeRisk] = []
        for index, eigenvalue in enumerate(eigenvalues):
            magnitude = float(abs(eigenvalue))
            if magnitude >= 1.0:
                time_constant = float("inf")
            elif magnitude <= 1e-15:
                time_constant = 0.0
            else:
                time_constant = float(-1.0 / np.log(magnitude))
            consequence_gain = float(np.linalg.norm(consequence @ eigenvectors[:, index]))
            exposure = float(abs(coefficients[index]) * consequence_gain)
            if exposure <= self.recovery_floor:
                recovery_steps = 0
            elif magnitude >= 1.0:
                recovery_steps = 2**31 - 1
            elif magnitude <= 1e-15:
                recovery_steps = 1
            else:
                recovery_steps = int(np.ceil(np.log(self.recovery_floor / exposure) / np.log(magnitude)))
            joint = exposure >= self.minimum_exposure and recovery_steps >= self.minimum_recovery_steps
            risks.append(ModeRisk(magnitude, time_constant, exposure, recovery_steps, joint))
        scalar_distance = float(abs(observed @ state))
        scalar_alert = scalar_distance >= self.scalar_alarm_distance
        recovery_only = any(mode.modal_time_constant >= self.minimum_recovery_steps for mode in risks)
        return ResilienceAssessment(
            observed_scalar_distance=scalar_distance,
            scalar_only_alert=scalar_alert,
            recovery_only_alert=recovery_only,
            joint_alert=any(mode.joint_alert for mode in risks),
            modes=tuple(risks),
        )

