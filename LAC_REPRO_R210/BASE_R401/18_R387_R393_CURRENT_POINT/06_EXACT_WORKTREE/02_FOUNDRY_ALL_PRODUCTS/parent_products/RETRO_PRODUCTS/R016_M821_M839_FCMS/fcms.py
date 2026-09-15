"""Fine-Compatible Microstructure Synthesizer (FCMS) v0.1."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class LaminateNode:
    matrix: tuple[tuple[float, ...], ...]
    depth: int
    weight_left: float | None
    rank_one_residual: float | None
    phase_name: str | None
    left: "LaminateNode | None" = None
    right: "LaminateNode | None" = None


@dataclass(frozen=True)
class MicrostructureResult:
    target_matrix: tuple[tuple[float, ...], ...]
    realized_matrix: tuple[tuple[float, ...], ...]
    frobenius_target_error: float
    laminate_depth: int
    phase_fractions: tuple[tuple[str, float], ...]
    estimated_smallest_layer: float
    fabrication_resolution_satisfied: bool
    tree: LaminateNode
    searched_state_count: int
    status: str

    def to_dict(self) -> dict:
        return asdict(self)


def _array(node: LaminateNode) -> np.ndarray:
    return np.asarray(node.matrix, dtype=float)


def _rank_one_residual(a: np.ndarray, b: np.ndarray) -> float:
    singular = np.linalg.svd(a - b, compute_uv=False)
    return 0.0 if singular.size < 2 else float(singular[1])


def _fractions(node: LaminateNode) -> dict[str, float]:
    if node.phase_name is not None:
        return {node.phase_name: 1.0}
    left = _fractions(node.left); right = _fractions(node.right)
    weight = float(node.weight_left)
    result: dict[str, float] = {}
    for name, value in left.items(): result[name] = result.get(name, 0.0) + weight * value
    for name, value in right.items(): result[name] = result.get(name, 0.0) + (1.0 - weight) * value
    return result


def synthesize_compatible_microstructure(
    allowed_gradients: Sequence[Sequence[Sequence[float]]],
    target_gradient: Sequence[Sequence[float]],
    *,
    phase_names: Sequence[str] | None = None,
    maximum_lamination_depth: int = 3,
    rank_one_tolerance: float = 1e-9,
    target_tolerance: float = 1e-8,
    beam_width: int = 300,
    specimen_thickness: float = 1.0,
    minimum_fabrication_feature: float = 0.0,
) -> MicrostructureResult:
    """Search sequential rank-one laminates for a requested coarse gradient."""

    phases = np.asarray(allowed_gradients, dtype=float)
    target = np.asarray(target_gradient, dtype=float)
    if phases.ndim != 3 or phases.shape[0] < 2 or phases.shape[1] != phases.shape[2] or target.shape != phases.shape[1:] or not np.all(np.isfinite(phases)) or not np.all(np.isfinite(target)):
        raise ValueError("allowed_gradients must be multiple finite square matrices matching target")
    if not isinstance(maximum_lamination_depth, int) or maximum_lamination_depth < 1 or rank_one_tolerance < 0 or target_tolerance < 0 or not isinstance(beam_width, int) or beam_width < 2:
        raise ValueError("invalid search depth, tolerances, or beam width")
    if specimen_thickness <= 0 or minimum_fabrication_feature < 0:
        raise ValueError("specimen thickness must be positive and feature size nonnegative")
    names = tuple(phase_names) if phase_names is not None else tuple(f"phase_{i}" for i in range(phases.shape[0]))
    if len(names) != phases.shape[0] or len(set(names)) != len(names):
        raise ValueError("phase_names must be unique and match allowed gradients")

    pool: list[LaminateNode] = [
        LaminateNode(tuple(tuple(map(float, row)) for row in matrix), 0, None, None, str(name))
        for matrix, name in zip(phases, names)
    ]
    best = min(pool, key=lambda node: np.linalg.norm(_array(node) - target))
    seen = {tuple(np.round(_array(node).ravel(), 10)) for node in pool}
    searched = len(pool)
    for depth in range(1, maximum_lamination_depth + 1):
        generated: list[LaminateNode] = []
        for i in range(len(pool)):
            for j in range(i + 1, len(pool)):
                left, right = pool[i], pool[j]
                if max(left.depth, right.depth) != depth - 1:
                    continue
                a, b = _array(left), _array(right)
                residual = _rank_one_residual(a, b)
                if residual > rank_one_tolerance:
                    continue
                direction = a - b
                denominator = float(np.sum(direction * direction))
                projected = .5 if denominator <= 1e-20 else float(np.sum((target - b) * direction) / denominator)
                weights = {min(.999999, max(.000001, projected)), .25, .5, .75}
                for weight in weights:
                    matrix = weight * a + (1.0 - weight) * b
                    key = tuple(np.round(matrix.ravel(), 10))
                    if key in seen:
                        continue
                    seen.add(key); searched += 1
                    generated.append(LaminateNode(
                        tuple(tuple(map(float, row)) for row in matrix),
                        max(left.depth, right.depth) + 1,
                        float(weight), residual, None, left, right,
                    ))
        if not generated:
            break
        generated.sort(key=lambda node: np.linalg.norm(_array(node) - target))
        retained = generated[:beam_width]
        candidate = retained[0]
        if np.linalg.norm(_array(candidate) - target) < np.linalg.norm(_array(best) - target):
            best = candidate
        pool = (pool + retained)
        pool.sort(key=lambda node: (np.linalg.norm(_array(node) - target), node.depth))
        pool = pool[:beam_width]
        if np.linalg.norm(_array(best) - target) <= target_tolerance:
            break

    error = float(np.linalg.norm(_array(best) - target))
    fractions = _fractions(best)
    smallest = float(specimen_thickness / (2 ** best.depth))
    fabrication_ok = smallest + 1e-15 >= minimum_fabrication_feature
    if error <= target_tolerance and fabrication_ok:
        status = "COMPATIBLE_MICROSTRUCTURE_SYNTHESIZED"
    elif error <= target_tolerance:
        status = "MATHEMATICALLY_REALIZABLE_BELOW_FABRICATION_RESOLUTION"
    else:
        status = "NEAREST_COMPATIBLE_RELAXATION_RETURNED"
    return MicrostructureResult(
        target_matrix=tuple(tuple(map(float, row)) for row in target),
        realized_matrix=best.matrix,
        frobenius_target_error=error,
        laminate_depth=best.depth,
        phase_fractions=tuple(sorted((name, float(value)) for name, value in fractions.items())),
        estimated_smallest_layer=smallest,
        fabrication_resolution_satisfied=fabrication_ok,
        tree=best,
        searched_state_count=searched,
        status=status,
    )
