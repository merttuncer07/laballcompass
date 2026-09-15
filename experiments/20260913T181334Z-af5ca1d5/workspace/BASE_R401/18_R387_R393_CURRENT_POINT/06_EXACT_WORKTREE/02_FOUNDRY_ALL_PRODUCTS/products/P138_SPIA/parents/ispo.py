"""Intermittent Search Policy Optimizer (ISPO) v0.1."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class PolicyEvaluation:
    local_steps: int
    relocation_jump: int
    expected_detection_time: float
    support_coverage_probability: float
    worst_supported_detection_time: float
    relocation_count_to_worst: int
    feasible: bool


@dataclass(frozen=True)
class SearchOptimization:
    selected: PolicyEvaluation
    local_only: PolicyEvaluation
    expected_time_improvement_fraction: float
    evaluations: tuple[PolicyEvaluation, ...]
    status: str

    def to_dict(self) -> dict:
        return asdict(self)


def evaluate_periodic_policy(
    target_probabilities: Sequence[float],
    *,
    local_steps: int,
    relocation_jump: int,
    local_observation_time: float = 1.0,
    relocation_speed: float = 10.0,
    relocation_overhead: float = 0.0,
    max_cycles: int | None = None,
    coverage_tolerance: float = 1e-12,
) -> PolicyEvaluation:
    """Evaluate a detect-then-relocate periodic policy on a circular search space."""

    probabilities = np.asarray(target_probabilities, dtype=float)
    if probabilities.ndim != 1 or probabilities.size < 2 or np.any(probabilities < 0) or not np.all(np.isfinite(probabilities)) or probabilities.sum() <= 0:
        raise ValueError("target_probabilities must be a finite nonnegative vector with positive sum")
    if not isinstance(local_steps, int) or local_steps <= 0:
        raise ValueError("local_steps must be a positive integer")
    if not isinstance(relocation_jump, int) or relocation_jump < 0:
        raise ValueError("relocation_jump must be a nonnegative integer")
    if local_observation_time <= 0 or relocation_speed <= 0 or relocation_overhead < 0:
        raise ValueError("times and speed must be positive; overhead may be zero")
    if coverage_tolerance < 0:
        raise ValueError("coverage_tolerance must be nonnegative")

    probabilities = probabilities / probabilities.sum()
    n = probabilities.size
    cycles = max_cycles if max_cycles is not None else n * 2
    if not isinstance(cycles, int) or cycles <= 0:
        raise ValueError("max_cycles must be a positive integer")

    first_time = np.full(n, np.inf)
    first_relocations = np.zeros(n, dtype=int)
    position = 0
    elapsed = 0.0
    relocations = 0
    support = probabilities > coverage_tolerance
    for _ in range(cycles):
        for _ in range(local_steps):
            elapsed += local_observation_time
            if not np.isfinite(first_time[position]):
                first_time[position] = elapsed
                first_relocations[position] = relocations
            position = (position + 1) % n
        if np.all(np.isfinite(first_time[support])):
            break
        if relocation_jump:
            distance = relocation_jump % n
            position = (position + distance) % n
            elapsed += relocation_overhead + distance / relocation_speed
            relocations += 1

    covered = support & np.isfinite(first_time)
    coverage = float(probabilities[covered].sum())
    feasible = coverage >= 1.0 - coverage_tolerance
    if feasible:
        expected = float(np.dot(probabilities[support], first_time[support]))
        worst = float(np.max(first_time[support]))
        reloc_to_worst = int(np.max(first_relocations[support]))
    else:
        expected = float("inf")
        worst = float("inf")
        reloc_to_worst = relocations
    return PolicyEvaluation(
        local_steps=local_steps,
        relocation_jump=relocation_jump,
        expected_detection_time=expected,
        support_coverage_probability=coverage,
        worst_supported_detection_time=worst,
        relocation_count_to_worst=reloc_to_worst,
        feasible=feasible,
    )


def optimize_search_policy(
    target_probabilities: Sequence[float],
    local_step_candidates: Sequence[int],
    relocation_jump_candidates: Sequence[int],
    *,
    local_observation_time: float = 1.0,
    relocation_speed: float = 10.0,
    relocation_overhead: float = 0.0,
    max_cycles: int | None = None,
) -> SearchOptimization:
    """Choose a complete-coverage local/relocation schedule from declared candidates."""

    probabilities = np.asarray(target_probabilities, dtype=float)
    candidates = {(int(local), int(jump)) for local in local_step_candidates for jump in relocation_jump_candidates}
    candidates.add((int(probabilities.size), 0))
    evaluations = tuple(
        evaluate_periodic_policy(
            probabilities,
            local_steps=local,
            relocation_jump=jump,
            local_observation_time=local_observation_time,
            relocation_speed=relocation_speed,
            relocation_overhead=relocation_overhead,
            max_cycles=max_cycles,
        )
        for local, jump in sorted(candidates)
    )
    feasible = [evaluation for evaluation in evaluations if evaluation.feasible]
    if not feasible:
        raise RuntimeError("no candidate covers the declared target support")
    selected = min(
        feasible,
        key=lambda item: (item.expected_detection_time, item.worst_supported_detection_time),
    )
    local_only = next(
        item for item in evaluations if item.local_steps == probabilities.size and item.relocation_jump == 0
    )
    improvement = 1.0 - selected.expected_detection_time / local_only.expected_detection_time
    status = "INTERMITTENT_POLICY_SELECTED" if selected.relocation_jump else "LOCAL_ONLY_SELECTED"
    return SearchOptimization(
        selected=selected,
        local_only=local_only,
        expected_time_improvement_fraction=float(improvement),
        evaluations=evaluations,
        status=status,
    )
