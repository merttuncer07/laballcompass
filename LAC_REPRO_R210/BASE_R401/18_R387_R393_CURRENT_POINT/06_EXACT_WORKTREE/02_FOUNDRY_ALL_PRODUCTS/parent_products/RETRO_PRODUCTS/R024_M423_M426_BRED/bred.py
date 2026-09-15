"""Balanced Reduction Error-budget Designer (BRED) v0.1."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence

import numpy as np
from scipy.linalg import solve_discrete_lyapunov


@dataclass(frozen=True)
class OrderOption:
    order: int
    hankel_error_upper_bound: float
    retained_hankel_share: float


@dataclass(frozen=True)
class BalancedReduction:
    original_order: int
    effective_io_order: int
    selected_order: int
    error_budget: float
    hankel_singular_values: tuple[float, ...]
    options: tuple[OrderOption, ...]
    theoretical_error_upper_bound: float
    impulse_maximum_absolute_error: float
    impulse_l2_error: float
    original_spectral_radius: float
    reduced_spectral_radius: float
    reduced_a: tuple[tuple[float, ...], ...]
    reduced_b: tuple[tuple[float, ...], ...]
    reduced_c: tuple[tuple[float, ...], ...]
    reduced_d: tuple[tuple[float, ...], ...]
    status: str

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["options"] = [asdict(item) for item in self.options]
        return payload


def _factor_psd(matrix: np.ndarray, tolerance: float) -> np.ndarray:
    values, vectors = np.linalg.eigh((matrix + matrix.T) / 2)
    keep = values > tolerance
    return vectors[:, keep] * np.sqrt(values[keep])


def _matrix_tuple(matrix: np.ndarray) -> tuple[tuple[float, ...], ...]:
    return tuple(tuple(map(float, row)) for row in matrix)


def design_balanced_reduction(
    a: Sequence[Sequence[float]],
    b: Sequence[Sequence[float]],
    c: Sequence[Sequence[float]],
    d: Sequence[Sequence[float]] | None = None,
    *,
    error_budget: float,
    minimum_order: int = 1,
    impulse_horizon: int = 200,
    numerical_tolerance: float = 1e-12,
) -> BalancedReduction:
    """Select the smallest stable balanced truncation satisfying a Hankel error budget."""

    aa, bb, cc = np.asarray(a, dtype=float), np.asarray(b, dtype=float), np.asarray(c, dtype=float)
    if aa.ndim != 2 or aa.shape[0] != aa.shape[1] or aa.shape[0] == 0:
        raise ValueError("A must be non-empty and square")
    n = aa.shape[0]
    if bb.ndim != 2 or bb.shape[0] != n or bb.shape[1] == 0:
        raise ValueError("B must have shape (states, inputs)")
    if cc.ndim != 2 or cc.shape[1] != n or cc.shape[0] == 0:
        raise ValueError("C must have shape (outputs, states)")
    dd = np.zeros((cc.shape[0], bb.shape[1])) if d is None else np.asarray(d, dtype=float)
    if dd.shape != (cc.shape[0], bb.shape[1]):
        raise ValueError("D must have shape (outputs, inputs)")
    if not all(np.all(np.isfinite(matrix)) for matrix in (aa, bb, cc, dd)):
        raise ValueError("system matrices must be finite")
    if not np.isfinite(error_budget) or error_budget < 0:
        raise ValueError("error_budget must be finite and non-negative")
    if not isinstance(minimum_order, int) or minimum_order < 1 or minimum_order > n:
        raise ValueError("minimum_order must lie between one and the original order")
    if not isinstance(impulse_horizon, int) or impulse_horizon < 1:
        raise ValueError("impulse_horizon must be a positive integer")

    original_radius = float(np.max(np.abs(np.linalg.eigvals(aa))))
    if original_radius >= 1.0 - numerical_tolerance:
        raise ValueError("balanced truncation v0.1 requires a strictly stable discrete-time system")
    wc = solve_discrete_lyapunov(aa, bb @ bb.T)
    wo = solve_discrete_lyapunov(aa.T, cc.T @ cc)
    scale = max(float(np.linalg.norm(wc, 2)), float(np.linalg.norm(wo, 2)), 1.0)
    rc = _factor_psd(wc, numerical_tolerance * scale)
    ro = _factor_psd(wo, numerical_tolerance * scale)
    u, singular, vh = np.linalg.svd(ro.T @ rc, full_matrices=False)
    keep = singular > numerical_tolerance * max(float(singular[0]) if singular.size else 1.0, 1.0)
    singular = singular[keep]
    if singular.size == 0:
        raise ValueError("system has no numerically observable-controllable dynamic channel")
    u = u[:, keep]
    v = vh.T[:, keep]
    inverse_root = np.diag(1.0 / np.sqrt(singular))
    transform = rc @ v @ inverse_root
    inverse_transform = inverse_root @ u.T @ ro.T
    balanced_a = inverse_transform @ aa @ transform
    balanced_b = inverse_transform @ bb
    balanced_c = cc @ transform
    effective = singular.size
    if minimum_order > effective:
        raise ValueError("minimum_order exceeds the effective input-output order")

    total_hankel = float(np.sum(singular))
    options = tuple(
        OrderOption(
            order,
            float(2.0 * np.sum(singular[order:])),
            float(np.sum(singular[:order]) / total_hankel),
        )
        for order in range(minimum_order, effective + 1)
    )
    feasible = [option for option in options if option.hankel_error_upper_bound <= error_budget + numerical_tolerance]
    selected = feasible[0].order if feasible else effective
    status = "BUDGET_SATISFIED" if feasible else "FULL_EFFECTIVE_ORDER_REQUIRED"
    ar = balanced_a[:selected, :selected]
    br = balanced_b[:selected, :]
    cr = balanced_c[:, :selected]
    reduced_radius = float(np.max(np.abs(np.linalg.eigvals(ar))))

    errors = []
    full_power = np.eye(n)
    reduced_power = np.eye(selected)
    for step in range(impulse_horizon):
        if step == 0:
            full_markov = reduced_markov = dd
        else:
            full_markov = cc @ full_power @ bb
            reduced_markov = cr @ reduced_power @ br
            full_power = full_power @ aa
            reduced_power = reduced_power @ ar
        errors.append(full_markov - reduced_markov)
    stacked = np.stack(errors)
    selected_option = next(option for option in options if option.order == selected)
    return BalancedReduction(
        n, effective, selected, float(error_budget), tuple(map(float, singular)), options,
        selected_option.hankel_error_upper_bound,
        float(np.max(np.abs(stacked))), float(np.linalg.norm(stacked.ravel())),
        original_radius, reduced_radius,
        _matrix_tuple(ar), _matrix_tuple(br), _matrix_tuple(cr), _matrix_tuple(dd), status,
    )
