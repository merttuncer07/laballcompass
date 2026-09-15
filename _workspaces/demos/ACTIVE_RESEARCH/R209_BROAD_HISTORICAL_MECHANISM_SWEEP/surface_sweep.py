"""R209 breadth-first historical mechanism sweep.

The functions in this module are deliberately small discriminators.  They do
not claim product readiness or global novelty.  Each one checks a proposed
algebraic mutation, an exact scope boundary, or a cheap counterexample.
"""

from __future__ import annotations

from itertools import combinations, product
from math import comb
from typing import Any

import numpy as np
from numpy.typing import NDArray


Array = NDArray[np.float64]


def _gf2_rref_solve(a: NDArray[np.int64], b: NDArray[np.int64]) -> tuple[NDArray[np.int64] | None, int]:
    """Solve A x=b over GF(2), returning one solution and rank."""
    aug = np.concatenate([a.copy() & 1, (b.copy() & 1)[:, None]], axis=1)
    n_rows, n_cols = a.shape
    pivots: list[int] = []
    row = 0
    for col in range(n_cols):
        hits = np.flatnonzero(aug[row:, col])
        if hits.size == 0:
            continue
        pivot = row + int(hits[0])
        aug[[row, pivot]] = aug[[pivot, row]]
        for other in range(n_rows):
            if other != row and aug[other, col]:
                aug[other] ^= aug[row]
        pivots.append(col)
        row += 1
        if row == n_rows:
            break
    for r in range(row, n_rows):
        if not aug[r, :n_cols].any() and aug[r, n_cols]:
            return None, len(pivots)
    x = np.zeros(n_cols, dtype=np.int64)
    for r, col in enumerate(pivots):
        x[col] = aug[r, n_cols]
    return x, len(pivots)


def zhuravlev_gf2_corrector(seed: int = 209) -> dict[str, Any]:
    """Compile an affine/XOR corrector without enumerating all ensembles."""
    rng = np.random.default_rng(seed)
    n, m = 28, 18
    errors = rng.integers(0, 2, size=(n, m), dtype=np.int64)
    planted = np.zeros(m, dtype=np.int64)
    planted[rng.choice(m, size=5, replace=False)] = 1
    target = (errors @ planted) & 1
    recovered, rank = _gf2_rref_solve(errors, target)
    exact = recovered is not None and np.array_equal((errors @ recovered) & 1, target)

    small = rng.integers(0, 2, size=(20, 7), dtype=np.int64)
    impossible = None
    for bits in product((0, 1), repeat=20):
        trial = np.fromiter(bits, dtype=np.int64)
        candidate, _ = _gf2_rref_solve(small, trial)
        if candidate is None:
            impossible = trial
            break
    rejected, small_rank = _gf2_rref_solve(small, impossible) if impossible is not None else (None, 0)
    return {
        "exact_planted_correction": bool(exact),
        "control_rows": n,
        "base_algorithms": m,
        "gf2_rank": int(rank),
        "enumerative_search_space": int(2**m),
        "unreachable_target_certified": bool(impossible is not None and rejected is None),
        "small_rank": int(small_rank),
    }


def _monomial_exponents_2d(max_degree: int) -> list[tuple[int, int]]:
    return [(i, degree - i) for degree in range(max_degree + 1) for i in range(degree + 1)]


def ivakhnenko_empirical_quotient(seed: int = 210) -> dict[str, Any]:
    """Measure collapse of an expanded polynomial language on a finite sample."""
    rng = np.random.default_rng(seed)
    n = 40
    x = rng.uniform(-0.9, 0.9, size=(n, 2))
    max_degree = 32
    exponents = _monomial_exponents_2d(max_degree)
    vandermonde = np.column_stack([(x[:, 0] ** i) * (x[:, 1] ** j) for i, j in exponents])
    singular = np.linalg.svd(vandermonde, compute_uv=False)
    tol = singular[0] * max(vandermonde.shape) * np.finfo(float).eps
    rank = int(np.sum(singular > tol))
    q, _ = np.linalg.qr(vandermonde, mode="reduced")
    coeff = rng.normal(size=len(exponents))
    values = vandermonde @ coeff
    projected = q @ (q.T @ values)
    return {
        "sample_size": n,
        "max_total_degree": max_degree,
        "symbolic_monomials": len(exponents),
        "evaluation_quotient_rank": rank,
        "compression_ratio": float(len(exponents) / rank),
        "on_sample_projection_error": float(np.max(np.abs(values - projected))),
        "off_sample_equivalence_guaranteed": False,
    }


def ville_mixture_test(seed: int = 211, paths: int = 25_000, horizon: int = 200) -> dict[str, Any]:
    """Check time-uniform crossing for a capital-weighted martingale mixture."""
    rng = np.random.default_rng(seed)
    lambdas = np.array([-0.8, -0.4, 0.4, 0.8])
    capital = np.ones((paths, len(lambdas)), dtype=float)
    mixture_crossed = np.zeros(paths, dtype=bool)
    unnormalized_max_crossed = np.zeros(paths, dtype=bool)
    alpha = 0.05
    threshold = 1.0 / alpha
    for _ in range(horizon):
        x = rng.choice(np.array([-1.0, 1.0]), size=paths)
        capital *= 1.0 + x[:, None] * lambdas[None, :]
        mixture = capital.mean(axis=1)
        mixture_crossed |= mixture >= threshold
        unnormalized_max_crossed |= capital.max(axis=1) >= threshold
    return {
        "paths": paths,
        "horizon": horizon,
        "alpha": alpha,
        "mixture_crossing_rate": float(mixture_crossed.mean()),
        "max_component_crossing_rate": float(unnormalized_max_crossed.mean()),
        "ville_bound_respected": bool(mixture_crossed.mean() <= alpha + 0.005),
        "modern_collision": "mixture e-process / test-martingale literature",
    }


def yakubovich_triangle_counterexample() -> dict[str, Any]:
    """A three-constraint box implication with an S-procedure duality gap."""
    laplacian = np.array([[2.0, -1.0, -1.0], [-1.0, 2.0, -1.0], [-1.0, -1.0, 2.0]])
    vertices = np.array(list(product((-1.0, 1.0), repeat=3)))
    primal_max = float(np.max(np.einsum("bi,ij,bj->b", vertices, laplacian, vertices)))
    largest_eigenvalue = float(np.linalg.eigvalsh(laplacian)[-1])
    symmetric_multiplier_sum = 3.0 * largest_eigenvalue
    return {
        "box_max_xLx": primal_max,
        "best_symmetric_scalar_certificate_bound": symmetric_multiplier_sum,
        "duality_gap": symmetric_multiplier_sum - primal_max,
        "scalar_multi_s_procedure_exact": False,
        "reason": "permutation averaging makes a symmetric optimum valid; PSD requires lambda>=lambda_max(L)=3",
    }


def _carry_runs(base: int, trials: int, digits: int, seed: int) -> tuple[float, int, float]:
    rng = np.random.default_rng(seed)
    if base == 2:
        a = rng.integers(0, 2, size=(trials, digits), dtype=np.int8)
        b = rng.integers(0, 2, size=(trials, digits), dtype=np.int8)
    elif base == 3:
        a = rng.integers(-1, 2, size=(trials, digits), dtype=np.int8)
        b = rng.integers(-1, 2, size=(trials, digits), dtype=np.int8)
    else:
        raise ValueError(base)
    carry = np.zeros(trials, dtype=np.int8)
    run = np.zeros(trials, dtype=np.int16)
    run_lengths: list[NDArray[np.int16]] = []
    max_run = np.zeros(trials, dtype=np.int16)
    active_positions = 0
    for col in range(digits):
        total = a[:, col] + b[:, col] + carry
        if base == 2:
            next_carry = (total // 2).astype(np.int8)
        else:
            remainder = ((total + 1) % 3) - 1
            next_carry = ((total - remainder) // 3).astype(np.int8)
        active = next_carry != 0
        active_positions += int(active.sum())
        ended = (run > 0) & ~active
        if ended.any():
            run_lengths.append(run[ended].copy())
        run = np.where(active, run + 1, 0)
        max_run = np.maximum(max_run, run)
        carry = next_carry
    if (run > 0).any():
        run_lengths.append(run[run > 0].copy())
    all_runs = np.concatenate(run_lengths) if run_lengths else np.zeros(1)
    return float(all_runs.mean()), int(max_run.max()), float(active_positions / (trials * digits))


def setun_carry_locality(seed: int = 212) -> dict[str, Any]:
    """Compare average carry runs, while retaining the worst-case caveat."""
    binary = _carry_runs(2, trials=60_000, digits=64, seed=seed)
    ternary = _carry_runs(3, trials=60_000, digits=64, seed=seed + 1)
    return {
        "binary_mean_nonzero_carry_run": binary[0],
        "balanced_ternary_mean_nonzero_carry_run": ternary[0],
        "mean_run_ratio_binary_over_ternary": binary[0] / ternary[0],
        "binary_observed_max_run": binary[1],
        "ternary_observed_max_run": ternary[1],
        "binary_active_carry_fraction": binary[2],
        "ternary_active_carry_fraction": ternary[2],
        "worst_case_linear_in_word_length_for_both": True,
    }


def _thinning_matrix(p: Array, k: int) -> Array:
    orders = np.arange(1, k + 1, dtype=float)
    return 1.0 - (1.0 - p[:, None]) ** orders[None, :]


def gdr_thinning_tomography(seed: int = 213) -> dict[str, Any]:
    """Recover bounded cluster-size intensities from voids after controlled thinning."""
    rng = np.random.default_rng(seed)
    conditioning: dict[str, float] = {}
    exact_errors: dict[str, float] = {}
    for k in (3, 4, 6, 8):
        idx = np.arange(1, k + 1)
        p = 0.5 * (1.0 - np.cos((2 * idx - 1) * np.pi / (2 * k)))
        matrix = _thinning_matrix(p, k)
        mu = 0.8 * np.exp(-0.55 * np.arange(k))
        minus_log_void = matrix @ mu
        recovered = np.linalg.solve(matrix, minus_log_void)
        conditioning[str(k)] = float(np.linalg.cond(matrix))
        exact_errors[str(k)] = float(np.max(np.abs(recovered - mu)))

    k = 4
    idx = np.arange(1, k + 1)
    p = 0.5 * (1.0 - np.cos((2 * idx - 1) * np.pi / (2 * k)))
    matrix = _thinning_matrix(p, k)
    mu = np.array([0.8, 0.42, 0.21, 0.09])
    void = np.exp(-(matrix @ mu))
    windows = 250_000
    observed_void = rng.binomial(windows, void) / windows
    noisy_recovered = np.linalg.solve(matrix, -np.log(observed_void))
    return {
        "identity": "-log P(N_p=0)=sum_k mu_k[1-(1-p)^k]",
        "exact_max_abs_error_by_K": exact_errors,
        "condition_number_by_K": conditioning,
        "K4_noisy_relative_l2_error": float(np.linalg.norm(noisy_recovered - mu) / np.linalg.norm(mu)),
        "K4_recovered_nonnegative": bool(np.all(noisy_recovered >= 0)),
        "high_order_ill_conditioning_visible": bool(conditioning["8"] > 100 * conditioning["3"]),
    }


def _additive_linf_cycle_optimum(matrix: Array) -> float:
    """Solve min ||F-g-h||_inf through difference-constraint cycle feasibility."""
    rows, cols = matrix.shape
    nodes = rows + cols

    def feasible(tolerance: float) -> bool:
        # Put a_i=g_i and b_j=-h_j.  The band
        # F_ij-t <= a_i-b_j <= F_ij+t becomes two directed edges.
        edges: list[tuple[int, int, float]] = []
        for i in range(rows):
            for j in range(cols):
                b_node = rows + j
                edges.append((b_node, i, float(matrix[i, j] + tolerance)))
                edges.append((i, b_node, float(-matrix[i, j] + tolerance)))
        distance = np.zeros(nodes)
        for pass_index in range(nodes):
            changed = False
            for source, target, weight in edges:
                proposal = distance[source] + weight
                if proposal < distance[target] - 1e-14:
                    distance[target] = proposal
                    changed = True
            if not changed:
                return True
            if pass_index == nodes - 1:
                return False
        return True

    low, high = 0.0, float(np.max(np.abs(matrix)))
    for _ in range(70):
        middle = 0.5 * (low + high)
        if feasible(middle):
            high = middle
        else:
            low = middle
    return high


def _level_additive(matrix: Array, tolerance: float = 1e-10, max_iter: int = 20_000) -> tuple[float, int]:
    residual = matrix.copy()
    previous = np.inf
    for iteration in range(1, max_iter + 1):
        row_shift = 0.5 * (residual.max(axis=1) + residual.min(axis=1))
        residual -= row_shift[:, None]
        col_shift = 0.5 * (residual.max(axis=0) + residual.min(axis=0))
        residual -= col_shift[None, :]
        current = float(np.max(np.abs(residual)))
        if abs(previous - current) <= tolerance:
            return current, iteration
        previous = current
    return previous, max_iter


def diliberto_cycle_certificate(seed: int = 214) -> dict[str, Any]:
    """Compare leveling with the exact finite-grid Chebyshev LP and rectangle witness."""
    rng = np.random.default_rng(seed)
    matrix = rng.normal(size=(7, 8))
    cycle_error = _additive_linf_cycle_optimum(matrix)
    leveled_error, iterations = _level_additive(matrix)
    rectangle = 0.0
    for i, k in combinations(range(matrix.shape[0]), 2):
        for j, ell in combinations(range(matrix.shape[1]), 2):
            alternating = matrix[i, j] - matrix[i, ell] - matrix[k, j] + matrix[k, ell]
            rectangle = max(rectangle, abs(float(alternating)) / 4.0)
    return {
        "cycle_optimal_linf_error": cycle_error,
        "leveling_linf_error": leveled_error,
        "leveling_iterations": iterations,
        "rectangle_invariant_lower_bound": rectangle,
        "leveling_matches_cycle_optimum": bool(abs(leveled_error - cycle_error) < 1e-7),
        "rectangles_alone_attain_dual_optimum": bool(abs(rectangle - cycle_error) < 1e-7),
    }


def _kaczmarz(a: Array, b: Array, order: NDArray[np.int64], epochs: int) -> Array:
    x = np.zeros(a.shape[1])
    norm2 = np.sum(a * a, axis=1)
    for _ in range(epochs):
        for i in order:
            x += ((b[i] - a[i] @ x) / norm2[i]) * a[i]
    return x


def kaczmarz_inconsistent_order(seed: int = 215) -> dict[str, Any]:
    """Expose row-order dependence on an inconsistent overdetermined system."""
    rng = np.random.default_rng(seed)
    a = rng.normal(size=(70, 12))
    truth = rng.normal(size=12)
    b = a @ truth + 0.35 * rng.normal(size=70)
    forward = _kaczmarz(a, b, np.arange(len(b)), epochs=250)
    reverse = _kaczmarz(a, b, np.arange(len(b) - 1, -1, -1), epochs=250)
    symmetric = 0.5 * (forward + reverse)
    least_squares = np.linalg.lstsq(a, b, rcond=None)[0]
    residual = lambda x: float(np.linalg.norm(a @ x - b))
    return {
        "forward_reverse_solution_distance": float(np.linalg.norm(forward - reverse)),
        "forward_residual": residual(forward),
        "reverse_residual": residual(reverse),
        "symmetric_average_residual": residual(symmetric),
        "least_squares_residual": residual(least_squares),
        "symmetric_average_closes_gap": bool(residual(symmetric) < min(residual(forward), residual(reverse))),
        "modern_collision": "extended/randomized/block Kaczmarz literature",
    }


def lavrentiev_extrapolation(seed: int = 216) -> dict[str, Any]:
    """Cancel first-order regularization bias and expose noise amplification."""
    rng = np.random.default_rng(seed)
    singular = np.geomspace(1.0, 1e-4, 80)
    truth = rng.normal(size=len(singular)) / (1.0 + np.arange(len(singular)) ** 0.7)
    clean = singular * truth
    alpha = 2e-3

    def solve(data: Array, scale: float) -> Array:
        return data / (singular + scale)

    clean_one = solve(clean, alpha)
    clean_two = 2.0 * clean_one - solve(clean, 2.0 * alpha)
    noise = 2e-4 * rng.normal(size=len(singular))
    noisy = clean + noise
    noisy_one = solve(noisy, alpha)
    noisy_two = 2.0 * noisy_one - solve(noisy, 2.0 * alpha)
    return {
        "alpha": alpha,
        "clean_single_error": float(np.linalg.norm(clean_one - truth)),
        "clean_extrapolated_error": float(np.linalg.norm(clean_two - truth)),
        "noisy_single_error": float(np.linalg.norm(noisy_one - truth)),
        "noisy_extrapolated_error": float(np.linalg.norm(noisy_two - truth)),
        "bias_reduced": bool(np.linalg.norm(clean_two - truth) < np.linalg.norm(clean_one - truth)),
        "noise_tradeoff_present": bool(np.linalg.norm(noisy_two - clean_two) > np.linalg.norm(noisy_one - clean_one)),
        "modern_collision": "iterated/extrapolated Lavrentiev regularization",
    }


def _intertwiner_basis(p: Array, q: Array, tolerance: float = 1e-10) -> list[Array]:
    n = p.shape[0]
    operator = np.kron(np.eye(n), q) - np.kron(p.T, np.eye(n))
    u, s, vh = np.linalg.svd(operator)
    rank = int(np.sum(s > tolerance * max(1.0, s[0])))
    return [vh[i].reshape((n, n), order="F") for i in range(rank, len(vh))]


def delsarte_intertwiner_boundary(seed: int = 217) -> dict[str, Any]:
    """Check the finite-dimensional spectral boundary of exact transmutation."""
    rng = np.random.default_rng(seed)
    p = np.diag(np.array([1.0, 2.0, 4.0, 7.0]))
    s = rng.normal(size=(4, 4))
    while abs(np.linalg.det(s)) < 0.1:
        s = rng.normal(size=(4, 4))
    q_similar = s @ p @ np.linalg.inv(s)
    similar_basis = _intertwiner_basis(p, q_similar)
    candidate = s
    similar_residual = float(np.linalg.norm(q_similar @ candidate - candidate @ p))

    q_disjoint = np.diag(np.array([11.0, 13.0, 17.0, 19.0]))
    disjoint_basis = _intertwiner_basis(p, q_disjoint)
    return {
        "similar_case_nullity": len(similar_basis),
        "known_invertible_intertwiner_residual": similar_residual,
        "disjoint_spectrum_nullity": len(disjoint_basis),
        "universal_exact_invertible_transmuter": False,
        "boundary": "finite exact invertible intertwining requires similarity; shared spectral blocks permit only partial maps",
    }


def run_all() -> dict[str, Any]:
    return {
        "ZHURAVLEV_GF2_CORRECTOR": zhuravlev_gf2_corrector(),
        "IVAKHNENKO_EMPIRICAL_QUOTIENT": ivakhnenko_empirical_quotient(),
        "VILLE_CAPITAL_MIXTURE": ville_mixture_test(),
        "YAKUBOVICH_MULTI_S_GAP": yakubovich_triangle_counterexample(),
        "SETUN_CARRY_LOCALITY": setun_carry_locality(),
        "GDR_THINNING_TOMOGRAPHY": gdr_thinning_tomography(),
        "DILIBERTO_CYCLE_CERTIFICATE": diliberto_cycle_certificate(),
        "KACZMARZ_INCONSISTENT_ORDER": kaczmarz_inconsistent_order(),
        "LAVRENTIEV_EXTRAPOLATION": lavrentiev_extrapolation(),
        "DELSARTE_INTERTWINER_BOUNDARY": delsarte_intertwiner_boundary(),
    }
