"""R210: theorem-level second pass for the two R209 leaders."""

from __future__ import annotations

from itertools import combinations
from math import comb
from typing import Any

import numpy as np
from numpy.typing import NDArray


def gf2_solve(a: NDArray[np.int64], b: NDArray[np.int64]) -> tuple[NDArray[np.int64] | None, int]:
    aug = np.concatenate([(a.copy() & 1), (b.copy() & 1)[:, None]], axis=1)
    rows, cols = a.shape
    pivot_columns: list[int] = []
    pivot_row = 0
    for col in range(cols):
        candidates = np.flatnonzero(aug[pivot_row:, col])
        if candidates.size == 0:
            continue
        selected = pivot_row + int(candidates[0])
        aug[[pivot_row, selected]] = aug[[selected, pivot_row]]
        for row in range(rows):
            if row != pivot_row and aug[row, col]:
                aug[row] ^= aug[pivot_row]
        pivot_columns.append(col)
        pivot_row += 1
        if pivot_row == rows:
            break
    for row in range(pivot_row, rows):
        if not aug[row, :cols].any() and aug[row, cols]:
            return None, len(pivot_columns)
    solution = np.zeros(cols, dtype=np.int64)
    for row, col in enumerate(pivot_columns):
        solution[col] = aug[row, cols]
    return solution, len(pivot_columns)


def gdr_blind_direction(max_cluster_size: int = 12) -> dict[str, Any]:
    """Construct two nonnegative spectra nearly indistinguishable by all void probes."""
    K = max_cluster_size
    order = K // 2
    offset = K - order
    delta = np.zeros(K)
    for j in range(order + 1):
        delta[offset + j - 1] = ((-1.0) ** j) * comb(order, j)

    baseline = np.abs(delta) + 0.25
    spectrum_plus = baseline + delta
    spectrum_minus = baseline - delta
    p = np.linspace(0.0, 1.0, 20_001)
    cluster_order = np.arange(1, K + 1, dtype=float)
    observation = 1.0 - (1.0 - p[:, None]) ** cluster_order[None, :]
    measured = observation @ delta
    closed_form = -((1.0 - p) ** offset) * (p**order)
    analytic_max = (order / K) ** order * (offset / K) ** offset

    moment_annihilation = []
    support_index = np.arange(1, K + 1, dtype=float)
    for degree in range(order):
        moment_annihilation.append(float(np.dot(delta, support_index**degree)))

    return {
        "K": K,
        "finite_difference_order": order,
        "offset": offset,
        "delta_l1": float(np.linalg.norm(delta, ord=1)),
        "spectra_nonnegative": bool(np.all(spectrum_plus >= 0) and np.all(spectrum_minus >= 0)),
        "spectra_l1_distance": float(np.linalg.norm(spectrum_plus - spectrum_minus, ord=1)),
        "max_void_log_curve_distance": float(2.0 * np.max(np.abs(measured))),
        "analytic_max_single_delta": float(analytic_max),
        "closed_form_max_error": float(np.max(np.abs(measured - closed_form))),
        "inverse_l1_amplification_lower_bound": float(np.linalg.norm(delta, ord=1) / analytic_max),
        "annihilated_raw_moments_degrees_0_to_r_minus_1": moment_annihilation,
        "conclusion": "full finite cluster spectrum recovery from noisy real-retention void probes is exponentially ill-conditioned",
    }


def gdr_amplification_curve() -> dict[str, float]:
    output: dict[str, float] = {}
    for K in range(4, 22, 2):
        result = gdr_blind_direction(K)
        output[str(K)] = result["inverse_l1_amplification_lower_bound"]
    return output


def boolean_monomial_features(h: NDArray[np.int64], degree: int) -> tuple[NDArray[np.int64], list[tuple[int, ...]]]:
    """Evaluation matrix of square-free Boolean monomials up to fixed degree."""
    rows, generators = h.shape
    labels: list[tuple[int, ...]] = [()]
    columns: list[NDArray[np.int64]] = [np.ones(rows, dtype=np.int64)]
    for current_degree in range(1, degree + 1):
        for indices in combinations(range(generators), current_degree):
            columns.append(np.prod(h[:, indices], axis=1, dtype=np.int64) & 1)
            labels.append(indices)
    return np.column_stack(columns), labels


def zhuravlev_bounded_degree_corrector(seed: int = 210) -> dict[str, Any]:
    """Compile a degree-2 Boolean corrector and expose the interpolation boundary."""
    rng = np.random.default_rng(seed)
    rows, base_count = 300, 18
    base = rng.integers(0, 2, size=(rows, base_count), dtype=np.int64)
    affine_features, _ = boolean_monomial_features(base, degree=1)
    quadratic_features, quadratic_labels = boolean_monomial_features(base, degree=2)

    pair_column = quadratic_labels.index((2, 11))
    target = quadratic_features[:, pair_column].copy()
    target ^= quadratic_features[:, quadratic_labels.index((5,))]
    target ^= 1

    affine_solution, affine_rank = gf2_solve(affine_features, target)
    quadratic_solution, quadratic_rank = gf2_solve(quadratic_features, target)
    exact = quadratic_solution is not None and np.array_equal((quadratic_features @ quadratic_solution) & 1, target)

    growth = {}
    m = 40
    for degree in range(1, 6):
        growth[str(degree)] = int(sum(comb(m, j) for j in range(degree + 1)))

    # Empirical quotient: replace m dependent generators by a GF(2) column basis.
    duplicated = np.column_stack([base[:, :8], base[:, :8], base[:, 0] ^ base[:, 1]])
    _, generator_rank = gf2_solve(duplicated, np.zeros(rows, dtype=np.int64))
    raw_degree2 = 1 + duplicated.shape[1] + comb(duplicated.shape[1], 2)
    quotient_upper_bound = sum(comb(generator_rank, j) for j in range(3))

    return {
        "control_rows": rows,
        "base_algorithms": base_count,
        "affine_feature_count": int(affine_features.shape[1]),
        "quadratic_feature_count": int(quadratic_features.shape[1]),
        "affine_rank": int(affine_rank),
        "quadratic_rank": int(quadratic_rank),
        "affine_can_represent_target": bool(affine_solution is not None),
        "quadratic_exact": bool(exact),
        "feature_growth_for_m40": growth,
        "dependent_raw_generators": int(duplicated.shape[1]),
        "dependent_generator_rank": int(generator_rank),
        "raw_degree2_feature_count": int(raw_degree2),
        "rank_quotient_degree2_upper_bound": int(quotient_upper_bound),
        "worst_case": "fixed degree is polynomial in m; degree growing with m returns exponential 2^m algebra",
        "generalization_boundary": "control-sample exactness can become arbitrary interpolation once feature rank reaches sample size",
    }


def run_all() -> dict[str, Any]:
    return {
        "GDR_VOID_ONLY_CONDITIONING_BOUNDARY": gdr_blind_direction(),
        "GDR_AMPLIFICATION_CURVE": gdr_amplification_curve(),
        "ZHURAVLEV_BOUNDED_DEGREE_CORRECTOR": zhuravlev_bounded_degree_corrector(),
    }

