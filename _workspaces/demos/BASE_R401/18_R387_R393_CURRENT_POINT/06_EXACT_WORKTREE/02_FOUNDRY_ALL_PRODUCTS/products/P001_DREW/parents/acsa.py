"""Adaptive Candidate Selection Auditor (ACSA) v0.1."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class SelectionAudit:
    candidate_names: tuple[str, ...]
    selected_candidate: str
    holdout_best_candidate: str
    selection_mean_losses: tuple[float, ...]
    holdout_mean_losses: tuple[float, ...]
    candidate_generalization_gaps: tuple[float, ...]
    selected_selection_loss: float
    selected_holdout_loss: float
    selected_generalization_gap: float
    selected_holdout_regret: float
    family_worst_absolute_gap: float
    pointwise_standard_error: float
    pointwise_95_radius: float
    selected_holdout_loss_bootstrap_interval_95: tuple[float, float]
    selection_bootstrap_frequencies: tuple[float, ...]
    selection_fragility: float
    status: str

    def to_dict(self) -> dict:
        return asdict(self)


def audit_adaptive_selection(
    selection_losses: Sequence[Sequence[float]],
    holdout_losses: Sequence[Sequence[float]],
    *,
    candidate_names: Sequence[str] | None = None,
    bootstrap_samples: int = 1000,
    random_seed: int = 0,
    material_regret: float = 0.0,
) -> SelectionAudit:
    """Audit the candidate chosen on one sample against an untouched sample.

    Rows are cases and columns are candidates. Lower loss is better. The audit does not delete or
    reject candidates: it exposes the price of adaptive selection and retains every candidate's
    out-of-sample result.
    """

    selection = np.asarray(selection_losses, dtype=float)
    holdout = np.asarray(holdout_losses, dtype=float)
    if selection.ndim != 2 or holdout.ndim != 2 or selection.shape[1] != holdout.shape[1]:
        raise ValueError("selection and holdout losses must be case-by-candidate matrices with matching columns")
    if selection.shape[0] < 2 or holdout.shape[0] < 2 or selection.shape[1] < 1:
        raise ValueError("both samples need at least two cases and one candidate")
    if not np.all(np.isfinite(selection)) or not np.all(np.isfinite(holdout)):
        raise ValueError("losses must be finite")
    if not isinstance(bootstrap_samples, int) or bootstrap_samples < 100:
        raise ValueError("bootstrap_samples must be an integer >= 100")
    if material_regret < 0:
        raise ValueError("material_regret must be nonnegative")

    p = selection.shape[1]
    names = tuple(candidate_names) if candidate_names is not None else tuple(f"candidate_{j}" for j in range(p))
    if len(names) != p or len(set(names)) != p or any(not str(name) for name in names):
        raise ValueError("candidate_names must be unique nonempty labels matching the columns")

    selection_means = selection.mean(axis=0)
    holdout_means = holdout.mean(axis=0)
    selected = int(np.argmin(selection_means))
    holdout_best = int(np.argmin(holdout_means))
    gaps = holdout_means - selection_means
    selected_regret = float(holdout_means[selected] - holdout_means[holdout_best])

    selected_holdout = holdout[:, selected]
    standard_error = float(np.std(selected_holdout, ddof=1) / np.sqrt(holdout.shape[0]))
    pointwise_radius = 1.96 * standard_error

    rng = np.random.default_rng(random_seed)
    holdout_bootstrap = np.empty(bootstrap_samples)
    selection_counts = np.zeros(p, dtype=int)
    for b in range(bootstrap_samples):
        holdout_indices = rng.integers(0, holdout.shape[0], holdout.shape[0])
        selection_indices = rng.integers(0, selection.shape[0], selection.shape[0])
        holdout_bootstrap[b] = np.mean(selected_holdout[holdout_indices])
        boot_means = np.mean(selection[selection_indices, :], axis=0)
        selection_counts[int(np.argmin(boot_means))] += 1

    interval = tuple(map(float, np.quantile(holdout_bootstrap, [0.025, 0.975])))
    frequencies = selection_counts / bootstrap_samples
    fragility = float(1.0 - frequencies[selected])
    if selected_regret > material_regret:
        status = "ADAPTIVE_SELECTION_REGRET_DETECTED"
    elif fragility > 0.5:
        status = "SELECTION_UNSTABLE_ACROSS_RESAMPLES"
    else:
        status = "SELECTED_CANDIDATE_SURVIVES_HOLDOUT_AUDIT"

    return SelectionAudit(
        candidate_names=tuple(map(str, names)),
        selected_candidate=str(names[selected]),
        holdout_best_candidate=str(names[holdout_best]),
        selection_mean_losses=tuple(map(float, selection_means)),
        holdout_mean_losses=tuple(map(float, holdout_means)),
        candidate_generalization_gaps=tuple(map(float, gaps)),
        selected_selection_loss=float(selection_means[selected]),
        selected_holdout_loss=float(holdout_means[selected]),
        selected_generalization_gap=float(gaps[selected]),
        selected_holdout_regret=selected_regret,
        family_worst_absolute_gap=float(np.max(np.abs(gaps))),
        pointwise_standard_error=standard_error,
        pointwise_95_radius=float(pointwise_radius),
        selected_holdout_loss_bootstrap_interval_95=interval,
        selection_bootstrap_frequencies=tuple(map(float, frequencies)),
        selection_fragility=fragility,
        status=status,
    )
