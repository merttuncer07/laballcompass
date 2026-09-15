"""Target-Weighted Model Reducer, built from IM-178 -> IM-326."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from itertools import combinations
from typing import Any, Sequence

import numpy as np


@dataclass(frozen=True)
class ReductionResult:
    retained_states: tuple[str, ...]
    removed_states: tuple[str, ...]
    target_impulse_error: float
    relative_target_error: float
    evaluated_subsets: int

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class TargetWeightedModelReducer:
    def __init__(
        self,
        system_matrix: Sequence[Sequence[float]],
        input_matrix: Sequence[Sequence[float]],
        target_output_matrix: Sequence[Sequence[float]],
        state_names: Sequence[str] | None = None,
    ) -> None:
        self.A = np.asarray(system_matrix, dtype=float)
        self.B = np.asarray(input_matrix, dtype=float)
        self.C = np.asarray(target_output_matrix, dtype=float)
        if self.A.ndim != 2 or self.A.shape[0] != self.A.shape[1]:
            raise ValueError("system_matrix must be square")
        n = self.A.shape[0]
        if self.B.ndim != 2 or self.B.shape[0] != n:
            raise ValueError("input_matrix row count must match states")
        if self.C.ndim != 2 or self.C.shape[1] != n:
            raise ValueError("target_output_matrix column count must match states")
        if not all(np.all(np.isfinite(item)) for item in (self.A, self.B, self.C)):
            raise ValueError("System matrices must be finite")
        self.names = tuple(state_names or [f"state_{i}" for i in range(n)])
        if len(self.names) != n or len(set(self.names)) != n:
            raise ValueError("state_names must be unique and match state dimension")

    @staticmethod
    def _markov_sequence(A: np.ndarray, B: np.ndarray, C: np.ndarray, horizon: int) -> np.ndarray:
        if horizon < 1:
            raise ValueError("horizon must be positive")
        power = np.eye(A.shape[0])
        sequence = []
        for _ in range(horizon):
            sequence.append(C @ power @ B)
            power = power @ A
        return np.stack(sequence)

    def target_sequence(self, horizon: int) -> np.ndarray:
        return self._markov_sequence(self.A, self.B, self.C, horizon)

    def evaluate_subset(self, indices: Sequence[int], horizon: int) -> tuple[float, float]:
        indices = tuple(indices)
        if not indices:
            reduced = np.zeros_like(self.target_sequence(horizon))
        else:
            reduced = self._markov_sequence(
                self.A[np.ix_(indices, indices)],
                self.B[np.ix_(indices, range(self.B.shape[1]))],
                self.C[np.ix_(range(self.C.shape[0]), indices)],
                horizon,
            )
        full = self.target_sequence(horizon)
        error = float(np.linalg.norm(full - reduced))
        denominator = float(np.linalg.norm(full))
        relative = error / denominator if denominator > 0 else 0.0
        return error, relative

    def reduce(self, retain_count: int, horizon: int = 20) -> ReductionResult:
        n = self.A.shape[0]
        if not 0 <= retain_count <= n:
            raise ValueError("retain_count must be between zero and state dimension")
        best: tuple[float, tuple[int, ...], float] | None = None
        evaluated = 0
        for indices in combinations(range(n), retain_count):
            error, relative = self.evaluate_subset(indices, horizon)
            evaluated += 1
            row = (error, indices, relative)
            if best is None or row[0] < best[0]:
                best = row
        assert best is not None
        error, indices, relative = best
        retained = set(indices)
        return ReductionResult(
            retained_states=tuple(self.names[i] for i in indices),
            removed_states=tuple(self.names[i] for i in range(n) if i not in retained),
            target_impulse_error=error,
            relative_target_error=relative,
            evaluated_subsets=evaluated,
        )

    def energy_baseline(self, retain_count: int, horizon: int = 20) -> ReductionResult:
        n = self.A.shape[0]
        gramian = np.zeros((n, n))
        power = np.eye(n)
        for _ in range(horizon):
            gramian += power @ self.B @ self.B.T @ power.T
            power = self.A @ power
        indices = tuple(np.argsort(np.diag(gramian))[-retain_count:])
        error, relative = self.evaluate_subset(indices, horizon)
        retained = set(indices)
        return ReductionResult(
            retained_states=tuple(self.names[i] for i in indices),
            removed_states=tuple(self.names[i] for i in range(n) if i not in retained),
            target_impulse_error=error,
            relative_target_error=relative,
            evaluated_subsets=1,
        )
