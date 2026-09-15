from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import sys
from typing import Sequence

import numpy as np

_REPO = Path(__file__).resolve().parents[3]
_FOUNDRY_PRODUCTS = _REPO / "02_FOUNDRY_ALL_PRODUCTS" / "products"
_SACPS_PARENT = _REPO / "02_FOUNDRY_ALL_PRODUCTS" / "parent_products" / "RETRO_PRODUCTS" / "R037_SUPPORT_COVARIANCE_SACPS"
for p in (_FOUNDRY_PRODUCTS, _SACPS_PARENT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from P138_SPIA.spia import acquire_for_search_policy  # noqa: E402
from P138_SPIA.parents.aicc import InformationChannel  # noqa: E402
from sacps import estimate_support_aware_covariance  # noqa: E402


@dataclass(frozen=True)
class SCSPIAResult:
    current_policy: str
    chosen_channel: str | None
    ranked_channels: tuple[dict, ...]
    selected_shrinkage: float
    tangent_condition_number: float
    tangent_minimum_eigenvalue: float
    tangent_unsupported_max_absolute_covariance: float
    simplex_tangent_residual: float
    covariance: tuple[tuple[float, ...], ...]
    status: str

    def to_dict(self) -> dict:
        return asdict(self)


def simplex_tangent_basis(n: int) -> np.ndarray:
    if n < 2:
        raise ValueError("simplex dimension must be at least 2")
    raw = np.zeros((n, n - 1), dtype=float)
    for i in range(n - 1):
        raw[i, i] = 1.0
        raw[-1, i] = -1.0
    q, _ = np.linalg.qr(raw)
    return q[:, : n - 1]


def _validate_beliefs(rows: Sequence[Sequence[float]], *, name: str, min_rows: int = 3) -> np.ndarray:
    x = np.asarray(rows, dtype=float)
    if x.ndim != 2 or x.shape[0] < min_rows or x.shape[1] < 2:
        raise ValueError(f"{name} must be a case-by-location matrix with at least {min_rows} rows")
    if not np.all(np.isfinite(x)) or np.any(x < -1e-12):
        raise ValueError(f"{name} must contain finite non-negative probabilities")
    if not np.allclose(x.sum(axis=1), 1.0, atol=1e-8):
        raise ValueError(f"{name} rows must sum to one")
    return x


def support_calibrated_search_policy_acquisition(
    training_beliefs: Sequence[Sequence[float]],
    support_mask: Sequence[Sequence[bool]],
    belief_mean: Sequence[float],
    *,
    policies,
    channels: Sequence[InformationChannel],
    holdout_beliefs: Sequence[Sequence[float]] | None = None,
    shrinkage_grid: Sequence[float] = tuple(np.linspace(0.0, 1.0, 21)),
    eigenvalue_floor: float = 1e-10,
    maximum_condition_number: float = 1e8,
    policy_kwargs: dict | None = None,
) -> SCSPIAResult:
    """Estimate supported belief covariance in simplex-tangent coordinates, then run P138.

    The support mask is declared in an orthonormal (n-1)-dimensional tangent
    coordinate system.  SACPS estimates/shrinks covariance there.  Lifting by
    B C B^T guarantees zero row/column sums, so the resulting covariance obeys
    P138's probability-simplex contract by construction.
    """
    train = _validate_beliefs(training_beliefs, name="training_beliefs")
    n = train.shape[1]
    mean = np.asarray(belief_mean, dtype=float)
    if mean.shape != (n,) or not np.all(np.isfinite(mean)) or np.any(mean < -1e-12) or not np.isclose(mean.sum(), 1.0, atol=1e-8):
        raise ValueError("belief_mean must be a finite probability vector matching training_beliefs")
    hold = None
    if holdout_beliefs is not None:
        hold = _validate_beliefs(holdout_beliefs, name="holdout_beliefs", min_rows=2)
        if hold.shape[1] != n:
            raise ValueError("holdout_beliefs dimension mismatch")

    B = simplex_tangent_basis(n)
    mask = np.asarray(support_mask, dtype=bool)
    if mask.shape != (n - 1, n - 1):
        raise ValueError("support_mask must be (n-1)x(n-1) in tangent coordinates")

    train_z = train @ B
    hold_z = None if hold is None else hold @ B
    est = estimate_support_aware_covariance(
        train_z,
        mask,
        holdout_returns=hold_z,
        shrinkage_grid=shrinkage_grid,
        eigenvalue_floor=eigenvalue_floor,
        maximum_condition_number=maximum_condition_number,
    )
    Cz = np.asarray(est.covariance, dtype=float)
    C = B @ Cz @ B.T
    C = 0.5 * (C + C.T)
    tangent_residual = float(max(np.max(np.abs(C.sum(axis=0))), np.max(np.abs(C.sum(axis=1)))))

    spia = acquire_for_search_policy(
        mean,
        C,
        policies=policies,
        channels=list(channels),
        policy_kwargs=policy_kwargs,
    )
    return SCSPIAResult(
        current_policy=spia.current_policy,
        chosen_channel=spia.chosen_channel,
        ranked_channels=spia.ranked_channels,
        selected_shrinkage=est.selected_shrinkage,
        tangent_condition_number=est.condition_number,
        tangent_minimum_eigenvalue=est.minimum_eigenvalue,
        tangent_unsupported_max_absolute_covariance=est.unsupported_max_absolute_covariance,
        simplex_tangent_residual=tangent_residual,
        covariance=tuple(tuple(map(float, row)) for row in C),
        status="SUPPORTED_TANGENT_COVARIANCE_SEARCH_POLICY_ACQUISITION_COMPLETE",
    )
