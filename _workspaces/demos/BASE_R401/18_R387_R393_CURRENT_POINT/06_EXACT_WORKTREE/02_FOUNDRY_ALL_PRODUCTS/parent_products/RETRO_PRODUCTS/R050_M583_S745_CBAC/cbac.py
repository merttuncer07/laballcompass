"""Covariate-Balanced Assignment Certificate (CBAC) v0.1."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class AssignmentCertificate:
    assignment: tuple[int, ...]
    treated_count: int
    control_count: int
    randomization_draws: int
    acceptance_fraction: float
    accepted_pool_size: int
    mahalanobis_distance: float
    acceptance_cutoff: float
    distance_percentile: float
    standardized_mean_differences: tuple[float, ...]
    maximum_absolute_standardized_difference: float
    constant_covariate_indices: tuple[int, ...]
    baseline_first_draw_distance: float
    improvement_over_first_draw: float
    status: str

    def to_dict(self) -> dict:
        return asdict(self)


def design_balanced_assignment(
    covariates: Sequence[Sequence[float]],
    *,
    treated_count: int,
    randomization_draws: int = 10_000,
    acceptance_fraction: float = 0.01,
    seed: int | None = None,
) -> AssignmentCertificate:
    """Rerandomize fixed-size treatment assignment and sample from a balance acceptance region."""

    x = np.asarray(covariates, dtype=float)
    if x.ndim != 2 or x.shape[0] < 4 or x.shape[1] < 1 or not np.all(np.isfinite(x)):
        raise ValueError("covariates must be a finite matrix with at least four rows and one column")
    n, p = x.shape
    if not isinstance(treated_count, int) or not 0 < treated_count < n:
        raise ValueError("treated_count must be an integer strictly between zero and n")
    if not isinstance(randomization_draws, int) or randomization_draws < 2:
        raise ValueError("randomization_draws must be an integer at least two")
    if not 0 < acceptance_fraction <= 1:
        raise ValueError("acceptance_fraction must lie in (0,1]")

    standard_deviation = np.std(x, axis=0, ddof=1)
    active = standard_deviation > np.finfo(float).eps * np.maximum(np.max(np.abs(x), axis=0), 1.0)
    constant = tuple(map(int, np.where(~active)[0]))
    if not np.any(active):
        raise ValueError("at least one covariate must vary")
    z = (x[:, active] - np.mean(x[:, active], axis=0)) / standard_deviation[active]
    covariance = np.atleast_2d(np.cov(z, rowvar=False, ddof=1))
    covariance_inverse = np.linalg.pinv(covariance, hermitian=True)
    rng = np.random.default_rng(seed)
    assignments = np.zeros((randomization_draws, n), dtype=np.int8)
    differences = np.zeros((randomization_draws, z.shape[1]))
    distances = np.zeros(randomization_draws)
    for draw in range(randomization_draws):
        treated = rng.choice(n, size=treated_count, replace=False)
        assignments[draw, treated] = 1
        mask = assignments[draw].astype(bool)
        difference = np.mean(z[mask], axis=0) - np.mean(z[~mask], axis=0)
        differences[draw] = difference
        distances[draw] = float(difference @ covariance_inverse @ difference)

    accepted_size = max(1, int(np.ceil(acceptance_fraction * randomization_draws)))
    accepted_indices = np.argsort(distances, kind="stable")[:accepted_size]
    chosen_index = int(rng.choice(accepted_indices))
    chosen_assignment = assignments[chosen_index]
    chosen_difference_active = differences[chosen_index]
    full_difference = np.zeros(p)
    full_difference[active] = chosen_difference_active
    cutoff = float(distances[accepted_indices[-1]])
    chosen_distance = float(distances[chosen_index])
    percentile = float(np.mean(distances <= chosen_distance))
    baseline = float(distances[0])
    improvement = float(1.0 - chosen_distance / baseline) if baseline > 0 else 0.0
    return AssignmentCertificate(
        tuple(map(int, chosen_assignment)), treated_count, n - treated_count, randomization_draws,
        float(acceptance_fraction), accepted_size, chosen_distance, cutoff, percentile,
        tuple(map(float, full_difference)), float(np.max(np.abs(full_difference))), constant,
        baseline, improvement, "RANDOMIZED_WITHIN_ACCEPTANCE_REGION",
    )
