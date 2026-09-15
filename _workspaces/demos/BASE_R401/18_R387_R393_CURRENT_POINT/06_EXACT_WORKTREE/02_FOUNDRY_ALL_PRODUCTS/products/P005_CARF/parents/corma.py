"""Controllability, Observability, and Realization Minimality Auditor v0.1."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class StateSpaceAudit:
    states: int
    inputs: int
    outputs: int
    horizon: int
    stable: bool
    spectral_radius: float
    controllability_rank: int
    observability_rank: int
    minimal_io_dimension: int
    redundant_state_count: int
    controllable_observable: int
    controllable_unobservable: int
    uncontrollable_observable: int
    uncontrollable_unobservable: int
    controllability_singular_values: tuple[float, ...]
    observability_singular_values: tuple[float, ...]
    hankel_singular_values: tuple[float, ...]
    controllability_gramian_eigenvalues: tuple[float, ...]
    observability_gramian_eigenvalues: tuple[float, ...]
    status: str

    def to_dict(self) -> dict:
        return asdict(self)


def _rank(values: np.ndarray, tolerance: float | None) -> int:
    singular = np.linalg.svd(values, compute_uv=False)
    if singular.size == 0:
        return 0
    threshold = tolerance
    if threshold is None:
        threshold = max(values.shape) * np.finfo(float).eps * singular[0]
    return int(np.sum(singular > threshold))


def audit_state_space(
    a: Sequence[Sequence[float]],
    b: Sequence[Sequence[float]],
    c: Sequence[Sequence[float]],
    *,
    horizon: int | None = None,
    rank_tolerance: float | None = None,
) -> StateSpaceAudit:
    """Audit a discrete-time LTI realization x+=Ax+Bu, y=Cx."""

    aa, bb, cc = np.asarray(a, dtype=float), np.asarray(b, dtype=float), np.asarray(c, dtype=float)
    if aa.ndim != 2 or aa.shape[0] != aa.shape[1] or aa.shape[0] == 0:
        raise ValueError("A must be a non-empty square matrix")
    n = aa.shape[0]
    if bb.ndim != 2 or bb.shape[0] != n or bb.shape[1] == 0:
        raise ValueError("B must have shape (states, inputs) with at least one input")
    if cc.ndim != 2 or cc.shape[1] != n or cc.shape[0] == 0:
        raise ValueError("C must have shape (outputs, states) with at least one output")
    if not all(np.all(np.isfinite(matrix)) for matrix in (aa, bb, cc)):
        raise ValueError("system matrices must be finite")
    if rank_tolerance is not None and (not np.isfinite(rank_tolerance) or rank_tolerance < 0):
        raise ValueError("rank_tolerance must be finite and non-negative")
    steps = n if horizon is None else horizon
    if not isinstance(steps, int) or steps < n:
        raise ValueError("horizon must be an integer at least equal to the state dimension")

    controllability_blocks = []
    observability_blocks = []
    power = np.eye(n)
    for _ in range(steps):
        controllability_blocks.append(power @ bb)
        observability_blocks.append(cc @ power)
        power = power @ aa
    controllability = np.hstack(controllability_blocks)
    observability = np.vstack(observability_blocks)
    hankel = observability @ controllability

    controllability_rank = _rank(controllability, rank_tolerance)
    observability_rank = _rank(observability, rank_tolerance)
    minimal = _rank(hankel, rank_tolerance)
    co = minimal
    cno = controllability_rank - minimal
    nco = observability_rank - minimal
    ncno = n - co - cno - nco
    if min(co, cno, nco, ncno) < 0:
        raise ArithmeticError("inconsistent numerical ranks; provide an explicit rank_tolerance")

    wc = controllability @ controllability.T
    wo = observability.T @ observability
    spectral_radius = float(np.max(np.abs(np.linalg.eigvals(aa))))
    if minimal == n:
        status = "MINIMAL_REALIZATION"
    elif minimal == 0:
        status = "NO_INPUT_OUTPUT_DYNAMIC_CHANNEL"
    else:
        status = "REDUCIBLE_REALIZATION"
    return StateSpaceAudit(
        states=n,
        inputs=bb.shape[1],
        outputs=cc.shape[0],
        horizon=steps,
        stable=spectral_radius < 1.0,
        spectral_radius=spectral_radius,
        controllability_rank=controllability_rank,
        observability_rank=observability_rank,
        minimal_io_dimension=minimal,
        redundant_state_count=n - minimal,
        controllable_observable=co,
        controllable_unobservable=cno,
        uncontrollable_observable=nco,
        uncontrollable_unobservable=ncno,
        controllability_singular_values=tuple(map(float, np.linalg.svd(controllability, compute_uv=False))),
        observability_singular_values=tuple(map(float, np.linalg.svd(observability, compute_uv=False))),
        hankel_singular_values=tuple(map(float, np.linalg.svd(hankel, compute_uv=False))),
        controllability_gramian_eigenvalues=tuple(map(float, np.linalg.eigvalsh(wc)[::-1])),
        observability_gramian_eigenvalues=tuple(map(float, np.linalg.eigvalsh(wo)[::-1])),
        status=status,
    )
