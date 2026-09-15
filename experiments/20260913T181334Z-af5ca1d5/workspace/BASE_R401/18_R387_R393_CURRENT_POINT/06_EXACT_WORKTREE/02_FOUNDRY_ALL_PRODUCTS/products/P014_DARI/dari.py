"""Design-aware randomization inference (DARI) v0.1.

CBAC supplies the realized rerandomized design. DARI retains the finite accepted
assignment pool and performs Fisher randomization tests inside that pool. OTE
remains a separate model-assisted point estimate; its standard error is never
relabeled as design-exact.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable, Sequence

import numpy as np

if __package__:
    from .parents.cbac import AssignmentCertificate, design_balanced_assignment
else:
    from parents.cbac import AssignmentCertificate, design_balanced_assignment
if __package__:
    from .parents.ote import OrthogonalEstimate, OrthogonalTargetEstimator
else:
    from parents.ote import OrthogonalEstimate, OrthogonalTargetEstimator


@dataclass(frozen=True)
class RandomizationDesign:
    certificate: AssignmentCertificate
    accepted_assignments: tuple[tuple[int, ...], ...]

    def to_dict(self) -> dict:
        return {
            "certificate": self.certificate.to_dict(),
            "accepted_assignments": self.accepted_assignments,
        }


@dataclass(frozen=True)
class RandomizationTestResult:
    null_effect: float
    two_sided_p_value: float
    observed_residualized_difference: float
    accepted_pool_size: int
    extreme_pool_indices: int
    status: str

    def to_dict(self) -> dict:
        return asdict(self)


class DesignAwareRandomizationInference:
    @staticmethod
    def _accepted_pool(
        covariates: np.ndarray,
        *,
        treated_count: int,
        randomization_draws: int,
        acceptance_fraction: float,
        seed: int,
    ) -> tuple[np.ndarray, np.ndarray, int]:
        x = np.asarray(covariates, dtype=float)
        standard_deviation = np.std(x, axis=0, ddof=1)
        active = standard_deviation > np.finfo(float).eps * np.maximum(np.max(np.abs(x), axis=0), 1.0)
        z = (x[:, active] - np.mean(x[:, active], axis=0)) / standard_deviation[active]
        covariance = np.atleast_2d(np.cov(z, rowvar=False, ddof=1))
        inverse = np.linalg.pinv(covariance, hermitian=True)
        rng = np.random.default_rng(seed)
        assignments = np.zeros((randomization_draws, len(x)), dtype=np.int8)
        distances = np.empty(randomization_draws)
        for draw in range(randomization_draws):
            treated = rng.choice(len(x), size=treated_count, replace=False)
            assignments[draw, treated] = 1
            mask = assignments[draw].astype(bool)
            difference = np.mean(z[mask], axis=0) - np.mean(z[~mask], axis=0)
            distances[draw] = float(difference @ inverse @ difference)
        accepted_size = max(1, int(np.ceil(acceptance_fraction * randomization_draws)))
        accepted_indices = np.argsort(distances, kind="stable")[:accepted_size]
        chosen_index = int(rng.choice(accepted_indices))
        return assignments[accepted_indices], distances[accepted_indices], chosen_index

    def design(
        self,
        covariates: Sequence[Sequence[float]],
        *,
        treated_count: int,
        randomization_draws: int = 10_000,
        acceptance_fraction: float = 0.01,
        seed: int = 0,
    ) -> RandomizationDesign:
        x = np.asarray(covariates, dtype=float)
        certificate = design_balanced_assignment(
            x,
            treated_count=treated_count,
            randomization_draws=randomization_draws,
            acceptance_fraction=acceptance_fraction,
            seed=seed,
        )
        pool, _, chosen_index = self._accepted_pool(
            x,
            treated_count=treated_count,
            randomization_draws=randomization_draws,
            acceptance_fraction=acceptance_fraction,
            seed=seed,
        )
        # The chosen draw occurs after the same RNG stream used by CBAC.
        full_pool, _, _ = self._accepted_pool(
            x,
            treated_count=treated_count,
            randomization_draws=randomization_draws,
            acceptance_fraction=acceptance_fraction,
            seed=seed,
        )
        del chosen_index, full_pool
        if not any(np.array_equal(row, certificate.assignment) for row in pool):
            raise RuntimeError("CBAC assignment was not retained in the reconstructed acceptance pool")
        return RandomizationDesign(
            certificate=certificate,
            accepted_assignments=tuple(tuple(int(v) for v in row) for row in pool),
        )

    @staticmethod
    def randomization_test(
        outcomes: Sequence[float],
        assignment: Sequence[int],
        accepted_assignments: Iterable[Sequence[int]],
        *,
        null_effect: float,
    ) -> RandomizationTestResult:
        y = np.asarray(outcomes, dtype=float)
        observed_assignment = np.asarray(assignment, dtype=int)
        pool = np.asarray(list(accepted_assignments), dtype=int)
        if y.ndim != 1 or observed_assignment.shape != y.shape:
            raise ValueError("outcomes and assignment must be equal-length vectors")
        if pool.ndim != 2 or pool.shape[1] != len(y) or len(pool) == 0:
            raise ValueError("accepted_assignments must be a non-empty assignment matrix")
        if not np.all(np.isin(observed_assignment, [0, 1])) or not np.all(np.isin(pool, [0, 1])):
            raise ValueError("assignments must be binary")
        adjusted = y - float(null_effect) * observed_assignment

        def difference(candidate: np.ndarray) -> float:
            mask = candidate.astype(bool)
            if mask.all() or (~mask).all():
                raise ValueError("every assignment must contain treatment and control")
            return float(np.mean(adjusted[mask]) - np.mean(adjusted[~mask]))

        observed = difference(observed_assignment)
        statistics = np.asarray([difference(row) for row in pool])
        extreme = int(np.sum(np.abs(statistics) >= abs(observed) - 1e-12))
        p_value = float(extreme / len(pool))
        return RandomizationTestResult(
            null_effect=float(null_effect),
            two_sided_p_value=p_value,
            observed_residualized_difference=observed,
            accepted_pool_size=len(pool),
            extreme_pool_indices=extreme,
            status="NULL_REJECTED_AT_5_PERCENT" if p_value <= 0.05 else "NULL_NOT_REJECTED",
        )

    def confidence_set(
        self,
        outcomes: Sequence[float],
        assignment: Sequence[int],
        accepted_assignments: Iterable[Sequence[int]],
        effect_grid: Sequence[float],
        *,
        alpha: float = 0.05,
    ) -> dict[str, object]:
        if not 0 < alpha < 1:
            raise ValueError("alpha must lie in (0,1)")
        pool = tuple(tuple(row) for row in accepted_assignments)
        tested = tuple(float(effect) for effect in effect_grid)
        if not tested:
            raise ValueError("effect_grid cannot be empty")
        accepted = tuple(
            effect
            for effect in tested
            if self.randomization_test(
                outcomes,
                assignment,
                pool,
                null_effect=effect,
            ).two_sided_p_value > alpha
        )
        return {
            "alpha": float(alpha),
            "tested_effects": tested,
            "accepted_effects": accepted,
            "lower_hull": min(accepted) if accepted else None,
            "upper_hull": max(accepted) if accepted else None,
            "disconnected": any(
                tested.index(accepted[i + 1]) - tested.index(accepted[i]) > 1
                for i in range(len(accepted) - 1)
            ),
        }

    @staticmethod
    def orthogonal_point_estimate(
        representation: Sequence[Sequence[float]],
        assignment: Sequence[int],
        outcomes: Sequence[float],
        *,
        folds: int = 5,
        seed: int = 0,
    ) -> OrthogonalEstimate:
        return OrthogonalTargetEstimator(folds=folds, seed=seed).fit(
            representation,
            assignment,
            outcomes,
        )
