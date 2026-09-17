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
    selection_rule: str = "minimum_mean_loss_then_column_order"
    loss_estimand: str = "pooled_case_mean"
    resampling_method: str = "iid_rows"
    standard_error_method: str = "iid_sample_mean"
    selection_unit_count: int = 0
    holdout_unit_count: int = 0
    holdout_largest_unit_fraction: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


def _group_rows(ids, row_count, label):
    """Retain first-seen order and compare IDs without lossy string conversion."""
    if isinstance(ids, (str, bytes)):
        raise ValueError(f"{label} must contain one group ID per row")
    try:
        values = list(ids)
    except TypeError as exc:
        raise ValueError(f"{label} must contain one group ID per row") from exc
    if len(values) != row_count:
        raise ValueError(f"{label} must contain one group ID per row")
    groups = {}
    for row, value in enumerate(values):
        if isinstance(value, (int, np.integer)) and not isinstance(value, (bool, np.bool_)):
            key = ("integer", int(value))
        elif isinstance(value, str) and value.strip():
            key = ("string", value)
        else:
            raise ValueError(f"{label} IDs must be nonempty strings or integers; missing IDs are not allowed")
        groups.setdefault(key, []).append(row)
    if len(groups) < 5:
        raise ValueError(f"{label} needs at least five distinct groups for grouped inference")
    return groups.keys(), tuple(np.asarray(rows, dtype=int) for rows in groups.values())


def _resampled_rows(rng, row_count, groups):
    if groups is None:
        return rng.integers(0, row_count, row_count)
    draws = rng.integers(0, len(groups), len(groups))
    # Whole groups retain multiplicity and all their rows, including unequal sizes.
    return np.concatenate([groups[g] for g in draws])


def audit_adaptive_selection(
    selection_losses: Sequence[Sequence[float]],
    holdout_losses: Sequence[Sequence[float]],
    *,
    candidate_names: Sequence[str] | None = None,
    bootstrap_samples: int = 1000,
    random_seed: int = 0,
    material_regret: float = 0.0,
    selection_tiebreak_scores: Sequence[Sequence[float]] | None = None,
    selection_groups: Sequence[str | int] | None = None,
    holdout_groups: Sequence[str | int] | None = None,
) -> SelectionAudit:
    """Audit the candidate chosen on one sample against an untouched sample.

    Rows are cases and columns are candidates. Lower loss is better. The audit does not delete or
    reject candidates: it exposes the price of adaptive selection and retains every candidate's
    out-of-sample result.

    Optional case-by-candidate tiebreak scores are maximized only when mean
    selection losses are exactly equal. They must use selection data only.
    The same row indices resample loss and score together. By default rows are
    resampled independently. Supply both group arrays to resample whole source
    groups and use a cluster sandwich SE. IDs must share a namespace and must
    not overlap across partitions. This does not establish group independence.
    The estimand remains the pooled case mean, not the mean of group means.
    Models and supplied losses are fixed: no retraining or sequential replay
    is performed. The 1.96*SE radius is only a pointwise normal approximation.
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
    if not np.isfinite(material_regret) or material_regret < 0:
        raise ValueError("material_regret must be finite and nonnegative")

    if (selection_groups is None) != (holdout_groups is None):
        raise ValueError("selection_groups and holdout_groups must be supplied together")
    selection_blocks = holdout_blocks = None
    if selection_groups is not None:
        selection_keys, selection_blocks = _group_rows(selection_groups, selection.shape[0], "selection_groups")
        holdout_keys, holdout_blocks = _group_rows(holdout_groups, holdout.shape[0], "holdout_groups")
        if set(selection_keys).intersection(holdout_keys):
            raise ValueError("selection and holdout group IDs must be disjoint in a common namespace")

    tiebreak = None
    if selection_tiebreak_scores is not None:
        tiebreak = np.asarray(selection_tiebreak_scores, dtype=float)
        if tiebreak.shape != selection.shape or not np.all(np.isfinite(tiebreak)):
            raise ValueError("selection_tiebreak_scores must be finite and match selection_losses")

    def choose(mean_losses, mean_scores=None):
        if mean_scores is None:
            return int(np.argmin(mean_losses))
        return min(range(len(mean_losses)), key=lambda j: (mean_losses[j], -mean_scores[j], j))

    p = selection.shape[1]
    names = tuple(candidate_names) if candidate_names is not None else tuple(f"candidate_{j}" for j in range(p))
    if len(names) != p or len(set(names)) != p or any(not str(name) for name in names):
        raise ValueError("candidate_names must be unique nonempty labels matching the columns")

    selection_means = selection.mean(axis=0)
    holdout_means = holdout.mean(axis=0)
    selected = choose(selection_means, None if tiebreak is None else tiebreak.mean(axis=0))
    holdout_best = int(np.argmin(holdout_means))
    gaps = holdout_means - selection_means
    selected_regret = float(holdout_means[selected] - holdout_means[holdout_best])

    selected_holdout = holdout[:, selected]
    if holdout_blocks is None:
        standard_error = float(np.std(selected_holdout, ddof=1) / np.sqrt(holdout.shape[0]))
    else:
        # Intercept-only CR1 sandwich for the pooled row mean. Center first to
        # avoid subtracting two large totals when losses have a large offset.
        residual = selected_holdout - holdout_means[selected]
        totals = np.asarray([residual[rows].sum() for rows in holdout_blocks])
        group_count = len(holdout_blocks)
        standard_error = float(np.sqrt(group_count / (group_count - 1) * np.sum(totals ** 2))
                               / holdout.shape[0])
    pointwise_radius = 1.96 * standard_error

    rng = np.random.default_rng(random_seed)
    holdout_bootstrap = np.empty(bootstrap_samples)
    selection_counts = np.zeros(p, dtype=int)
    for b in range(bootstrap_samples):
        holdout_indices = _resampled_rows(rng, holdout.shape[0], holdout_blocks)
        selection_indices = _resampled_rows(rng, selection.shape[0], selection_blocks)
        holdout_bootstrap[b] = np.mean(selected_holdout[holdout_indices])
        boot_means = np.mean(selection[selection_indices, :], axis=0)
        boot_scores = None if tiebreak is None else np.mean(tiebreak[selection_indices, :], axis=0)
        selection_counts[choose(boot_means, boot_scores)] += 1

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
        selection_rule=("minimum_mean_loss_then_maximum_mean_tiebreak_score_then_column_order"
                        if tiebreak is not None else "minimum_mean_loss_then_column_order"),
        resampling_method="whole_groups" if holdout_blocks is not None else "iid_rows",
        standard_error_method="cluster_CR1_pooled_mean" if holdout_blocks is not None else "iid_sample_mean",
        selection_unit_count=len(selection_blocks) if selection_blocks is not None else selection.shape[0],
        holdout_unit_count=len(holdout_blocks) if holdout_blocks is not None else holdout.shape[0],
        holdout_largest_unit_fraction=(max(map(len, holdout_blocks)) / holdout.shape[0]
                                       if holdout_blocks is not None else 1 / holdout.shape[0]),
    )
