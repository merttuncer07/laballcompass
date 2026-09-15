from __future__ import annotations

import json
import math
import time
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent


def ridge(x: np.ndarray, y: np.ndarray, lam: float = 1e-6) -> np.ndarray:
    gram = x.T @ x
    scale = float(np.trace(gram)) / max(1, gram.shape[0])
    return np.linalg.solve(gram + (lam * max(scale, 1e-12)) * np.eye(gram.shape[0]), x.T @ y)


def _accuracy(scores: np.ndarray, labels: np.ndarray) -> float:
    return float(np.mean(np.argmax(scores, axis=1) == labels))


# ---------------------------------------------------------------------------
# HM-07: Steinbuch Lernmatrix -> bounded signed evidence with anti-saturation


def _prototype_bank(rng: np.random.Generator, classes: int, dims: int) -> np.ndarray:
    prototypes = np.zeros((classes, dims), dtype=np.int8)
    group_count = max(2, classes // 3)
    group_bits = [rng.choice(dims, 10, replace=False) for _ in range(group_count)]
    for c in range(classes):
        prototypes[c, group_bits[c % group_count]] = 1
        available = np.flatnonzero(prototypes[c] == 0)
        prototypes[c, rng.choice(available, 14, replace=False)] = 1
    return prototypes


def _corrupt_binary(
    rng: np.random.Generator,
    prototypes: np.ndarray,
    labels: np.ndarray,
    drop: float,
    insert: float,
) -> np.ndarray:
    x = prototypes[labels].copy()
    ones = x == 1
    zeros = ~ones
    x[ones & (rng.random(x.shape) < drop)] = 0
    x[zeros & (rng.random(x.shape) < insert)] = 1
    return x


def steinbuch_trial(seed: int, train_per_class: int, drop: float, insert: float) -> dict:
    rng = np.random.default_rng(seed)
    classes, dims = 12, 192
    prototypes = _prototype_bank(rng, classes, dims)
    train_labels = np.repeat(np.arange(classes), train_per_class)
    train_x = _corrupt_binary(rng, prototypes, train_labels, drop=0.12, insert=0.025)
    test_labels = np.repeat(np.arange(classes), 120)
    test_x = _corrupt_binary(rng, prototypes, test_labels, drop=drop, insert=insert)

    counts = np.stack([train_x[train_labels == c].sum(axis=0) for c in range(classes)])
    rates = counts / train_per_class

    # Saturating binary Lernmatrix/Willshaw-like cell: one hit permanently sets a cell.
    binary = counts > 0
    binary_scores = test_x @ binary.T

    # Strong floating baseline: nonnegative class centroid with cosine row normalization.
    centroid = rates / np.maximum(np.linalg.norm(rates, axis=1, keepdims=True), 1e-12)
    centroid_scores = test_x @ centroid.T

    # Equal-memory control: four unsigned evidence levels. This isolates whether
    # the gain merely comes from replacing a one-bit latch with two-bit cells.
    two_bit_count = np.digitize(rates, bins=np.array([0.05, 0.20, 0.50])).astype(np.int8)
    two_bit_count_scores = test_x @ two_bit_count.T

    # Mutation: every cell records whether a bit is positive, neutral, or negative
    # evidence for a class. Evidence is based on within-class versus outside-class
    # rates, so repeated incidental hits cannot monotonically saturate the matrix.
    total = train_x.sum(axis=0, keepdims=True)
    outside_rates = (total - counts) / max(1, train_per_class * (classes - 1))
    delta = rates - outside_rates
    uncertainty = np.sqrt(
        rates * (1.0 - rates) / max(1, train_per_class)
        + outside_rates * (1.0 - outside_rates) / max(1, train_per_class * (classes - 1))
        + 1e-6
    )
    z = delta / uncertainty
    ternary = np.where(z >= 1.25, 1, np.where(z <= -1.25, -1, 0)).astype(np.int8)
    ternary_scores = test_x @ ternary.T

    return {
        "seed": seed,
        "train_per_class": train_per_class,
        "drop": drop,
        "insert": insert,
        "binary_accuracy": _accuracy(binary_scores, test_labels),
        "centroid_accuracy": _accuracy(centroid_scores, test_labels),
        "two_bit_count_accuracy": _accuracy(two_bit_count_scores, test_labels),
        "signed_ternary_accuracy": _accuracy(ternary_scores, test_labels),
        "binary_saturation": float(binary.mean()),
        "ternary_nonzero": float(np.mean(ternary != 0)),
        "bits_binary": int(classes * dims),
        "bits_signed_ternary": int(2 * classes * dims),
        "bits_float_centroid": int(32 * classes * dims),
    }


def run_steinbuch() -> dict:
    cases = []
    for seed in range(8):
        for load in (4, 16, 64):
            for drop, insert in ((0.25, 0.03), (0.40, 0.06)):
                cases.append(steinbuch_trial(seed, load, drop, insert))
    high_load = [c for c in cases if c["train_per_class"] == 64]
    signed_vs_binary = sum(c["signed_ternary_accuracy"] > c["binary_accuracy"] for c in cases)
    signed_vs_centroid = sum(c["signed_ternary_accuracy"] > c["centroid_accuracy"] for c in cases)
    signed_vs_two_bit = sum(c["signed_ternary_accuracy"] > c["two_bit_count_accuracy"] for c in cases)
    high_binary = np.mean([c["binary_accuracy"] for c in high_load])
    high_signed = np.mean([c["signed_ternary_accuracy"] for c in high_load])
    high_centroid = np.mean([c["centroid_accuracy"] for c in high_load])
    high_two_bit = np.mean([c["two_bit_count_accuracy"] for c in high_load])
    return {
        "cases": cases,
        "summary": {
            "case_count": len(cases),
            "signed_beats_binary": signed_vs_binary,
            "signed_beats_float_centroid": signed_vs_centroid,
            "signed_beats_equal_memory_2bit_count": signed_vs_two_bit,
            "high_load_mean_binary_accuracy": float(high_binary),
            "high_load_mean_signed_accuracy": float(high_signed),
            "high_load_mean_float_centroid_accuracy": float(high_centroid),
            "high_load_mean_2bit_count_accuracy": float(high_two_bit),
            "high_load_mean_binary_saturation": float(
                np.mean([c["binary_saturation"] for c in high_load])
            ),
            "high_load_mean_ternary_nonzero": float(
                np.mean([c["ternary_nonzero"] for c in high_load])
            ),
            "status": (
                "SATURATION_BROKEN_BY_2BIT_PROMOTION_SIGNED_EDGE_UNPROVEN"
                if high_signed > high_binary + 0.05
                and high_signed >= high_centroid - 0.04
                and high_signed >= high_two_bit - 0.02
                else "NOT_BROKEN"
            ),
        },
    }


# ---------------------------------------------------------------------------
# HM-10: Choquet capacity -> sparse signed Mobius support with exact certificate


def pair_index(dims: int) -> list[tuple[int, int]]:
    return [(i, j) for i in range(dims) for j in range(i + 1, dims)]


def pair_features(x: np.ndarray, pairs: list[tuple[int, int]]) -> np.ndarray:
    if not pairs:
        return np.empty((len(x), 0))
    return np.column_stack([np.minimum(x[:, i], x[:, j]) for i, j in pairs])


def project_two_additive_capacity(
    singleton: np.ndarray,
    interactions: np.ndarray,
    pairs: list[tuple[int, int]],
) -> tuple[np.ndarray, np.ndarray]:
    singleton = singleton.astype(float).copy()
    interactions = interactions.astype(float).copy()
    required = np.zeros_like(singleton)
    for value, (i, j) in zip(interactions, pairs):
        if value < 0:
            required[i] -= value
            required[j] -= value
    singleton = np.maximum(singleton, required + 1e-10)
    total = float(singleton.sum() + interactions.sum())
    if total <= 1e-12:
        singleton = required + 1.0
        total = float(singleton.sum() + interactions.sum())
    return singleton / total, interactions / total


def minimum_capacity_marginal(
    singleton: np.ndarray,
    interactions: np.ndarray,
    pairs: list[tuple[int, int]],
) -> float:
    minimum = math.inf
    for i, base in enumerate(singleton):
        marginal = float(base)
        for value, (left, right) in zip(interactions, pairs):
            if value < 0 and (i == left or i == right):
                marginal += float(value)
        minimum = min(minimum, marginal)
    return minimum


def capacity_predict(
    x: np.ndarray,
    singleton: np.ndarray,
    interactions: np.ndarray,
    pairs: list[tuple[int, int]],
) -> np.ndarray:
    return x @ singleton + pair_features(x, pairs) @ interactions


def _make_sparse_capacity(rng: np.random.Generator, dims: int, support: int):
    all_pairs = pair_index(dims)
    chosen_ids = rng.choice(len(all_pairs), support, replace=False)
    chosen = [all_pairs[int(i)] for i in chosen_ids]
    b = rng.uniform(-0.22, 0.22, support)
    required = np.zeros(dims)
    for value, (i, j) in zip(b, chosen):
        if value < 0:
            required[i] -= value
            required[j] -= value
    a = required + rng.uniform(0.10, 0.32, dims)
    total = a.sum() + b.sum()
    return a / total, b / total, chosen


def _fit_sparse_capacity(x: np.ndarray, y: np.ndarray, support: int):
    dims = x.shape[1]
    all_pairs = pair_index(dims)
    all_pair_x = pair_features(x, all_pairs)
    selected: list[int] = []
    base = x
    for _ in range(support):
        design = np.column_stack([base, all_pair_x[:, selected]]) if selected else base
        coef = ridge(design, y, 1e-5)
        residual = y - design @ coef
        corr = np.abs(all_pair_x.T @ residual)
        if selected:
            corr[selected] = -np.inf
        selected.append(int(np.argmax(corr)))
    selected_pairs = [all_pairs[i] for i in selected]
    design = np.column_stack([x, all_pair_x[:, selected]])
    coef = ridge(design, y, 1e-5)
    a, b = project_two_additive_capacity(coef[:dims], coef[dims:], selected_pairs)
    return a, b, selected_pairs


def choquet_trial(seed: int, dims: int, train_size: int, support: int = 7) -> dict:
    rng = np.random.default_rng(1000 + seed + 31 * dims + train_size)
    true_a, true_b, true_pairs = _make_sparse_capacity(rng, dims, support)
    train_x = rng.random((train_size, dims))
    test_x = rng.random((2000, dims))
    train_y = capacity_predict(train_x, true_a, true_b, true_pairs)
    train_y += rng.normal(0.0, 0.008, train_size)
    test_y = capacity_predict(test_x, true_a, true_b, true_pairs)

    add_a = ridge(train_x, train_y, 1e-5)
    add_a = np.maximum(add_a, 1e-10)
    add_a /= add_a.sum()
    add_pred = test_x @ add_a

    all_pairs = pair_index(dims)
    full_design = np.column_stack([train_x, pair_features(train_x, all_pairs)])
    full_coef = ridge(full_design, train_y, 1e-4)
    raw_full_pred = np.column_stack([test_x, pair_features(test_x, all_pairs)]) @ full_coef
    raw_full_a = full_coef[:dims]
    raw_full_b = full_coef[dims:]
    full_a, full_b = project_two_additive_capacity(
        full_coef[:dims], full_coef[dims:], all_pairs
    )
    full_pred = capacity_predict(test_x, full_a, full_b, all_pairs)

    sparse_a, sparse_b, sparse_pairs = _fit_sparse_capacity(
        train_x, train_y, support=support
    )
    sparse_pred = capacity_predict(test_x, sparse_a, sparse_b, sparse_pairs)
    overlap = len(set(sparse_pairs) & set(true_pairs))

    return {
        "seed": seed,
        "dims": dims,
        "train_size": train_size,
        "additive_rmse": float(np.sqrt(np.mean((add_pred - test_y) ** 2))),
        "full_pair_rmse": float(np.sqrt(np.mean((full_pred - test_y) ** 2))),
        "raw_unconstrained_full_pair_rmse": float(
            np.sqrt(np.mean((raw_full_pred - test_y) ** 2))
        ),
        "raw_unconstrained_min_marginal": float(
            minimum_capacity_marginal(raw_full_a, raw_full_b, all_pairs)
        ),
        "sparse_capacity_rmse": float(np.sqrt(np.mean((sparse_pred - test_y) ** 2))),
        "sparse_exact_min_marginal": float(
            minimum_capacity_marginal(sparse_a, sparse_b, sparse_pairs)
        ),
        "support_overlap": overlap,
        "true_support": support,
        "sparse_parameters": dims + support,
        "full_pair_parameters": dims + len(all_pairs),
        "unrestricted_capacity_parameters": (2**dims) - 2,
    }


def choquet_dense_stress(seed: int, dims: int = 12) -> dict:
    """Deliberately violates sparse support; the compact model should not claim this class."""
    rng = np.random.default_rng(7000 + seed)
    pairs = pair_index(dims)
    b = rng.uniform(0.04, 0.16, len(pairs))
    a = rng.uniform(0.02, 0.06, dims)
    total = a.sum() + b.sum()
    a, b = a / total, b / total
    train_x = rng.random((800, dims))
    test_x = rng.random((2500, dims))
    train_y = capacity_predict(train_x, a, b, pairs) + rng.normal(0, 0.004, 800)
    test_y = capacity_predict(test_x, a, b, pairs)

    sparse_a, sparse_b, sparse_pairs = _fit_sparse_capacity(train_x, train_y, support=7)
    sparse_pred = capacity_predict(test_x, sparse_a, sparse_b, sparse_pairs)
    design = np.column_stack([train_x, pair_features(train_x, pairs)])
    coef = ridge(design, train_y, 1e-5)
    full_a, full_b = project_two_additive_capacity(coef[:dims], coef[dims:], pairs)
    full_pred = capacity_predict(test_x, full_a, full_b, pairs)
    return {
        "seed": seed,
        "sparse_rmse": float(np.sqrt(np.mean((sparse_pred - test_y) ** 2))),
        "full_rmse": float(np.sqrt(np.mean((full_pred - test_y) ** 2))),
    }


def run_choquet() -> dict:
    cases = [
        choquet_trial(seed, dims, train_size)
        for seed in range(8)
        for dims in (12, 20)
        for train_size in (80, 200)
    ]
    sparse_add_wins = sum(c["sparse_capacity_rmse"] < c["additive_rmse"] for c in cases)
    sparse_full_wins = sum(c["sparse_capacity_rmse"] < c["full_pair_rmse"] for c in cases)
    sparse_raw_full_wins = sum(
        c["sparse_capacity_rmse"] < c["raw_unconstrained_full_pair_rmse"] for c in cases
    )
    exact = sum(c["sparse_exact_min_marginal"] >= -1e-9 for c in cases)
    dense_stress = [choquet_dense_stress(seed) for seed in range(6)]
    return {
        "cases": cases,
        "dense_interaction_stress": dense_stress,
        "summary": {
            "case_count": len(cases),
            "sparse_beats_additive": sparse_add_wins,
            "sparse_beats_full_pair": sparse_full_wins,
            "sparse_beats_raw_unconstrained_full_pair": sparse_raw_full_wins,
            "exact_monotonicity_certificates": exact,
            "mean_additive_rmse": float(np.mean([c["additive_rmse"] for c in cases])),
            "mean_full_pair_rmse": float(np.mean([c["full_pair_rmse"] for c in cases])),
            "mean_raw_unconstrained_full_pair_rmse": float(
                np.mean([c["raw_unconstrained_full_pair_rmse"] for c in cases])
            ),
            "raw_unconstrained_monotonicity_failures": sum(
                c["raw_unconstrained_min_marginal"] < -1e-9 for c in cases
            ),
            "mean_sparse_rmse": float(np.mean([c["sparse_capacity_rmse"] for c in cases])),
            "mean_support_overlap": float(np.mean([c["support_overlap"] for c in cases])),
            "dense_stress_full_beats_sparse": sum(
                c["full_rmse"] < c["sparse_rmse"] for c in dense_stress
            ),
            "dense_stress_mean_sparse_rmse": float(
                np.mean([c["sparse_rmse"] for c in dense_stress])
            ),
            "dense_stress_mean_full_rmse": float(
                np.mean([c["full_rmse"] for c in dense_stress])
            ),
            "status": (
                "EXPONENTIAL_CAPACITY_BROKEN_ONLY_FOR_SPARSE_2ADDITIVE_CLASS"
                if sparse_add_wins >= 24
                and sparse_full_wins >= 20
                and sparse_raw_full_wins >= 20
                and exact == len(cases)
                else "NOT_BROKEN"
            ),
        },
    }


# ---------------------------------------------------------------------------
# HM-12: Volterra series -> boundary-aware separable hereditary algebra


def lag_matrix(x: np.ndarray, memory: int, starts: np.ndarray, reset: bool) -> np.ndarray:
    z = np.zeros((len(x), memory))
    segment_start = 0
    for t in range(len(x)):
        if starts[t]:
            segment_start = t
        lower = segment_start if reset else 0
        for lag in range(memory):
            idx = t - lag
            if idx >= lower:
                z[t, lag] = x[idx]
    return z


def quadratic_features(z: np.ndarray) -> tuple[np.ndarray, list[tuple[int, int]]]:
    pairs = [(i, j) for i in range(z.shape[1]) for j in range(i, z.shape[1])]
    cols = [z[:, i] * z[:, j] * (1.0 if i == j else 2.0) for i, j in pairs]
    return np.column_stack(cols), pairs


def _coef_to_matrix(coef: np.ndarray, pairs: list[tuple[int, int]], memory: int):
    matrix = np.zeros((memory, memory))
    for value, (i, j) in zip(coef, pairs):
        matrix[i, j] = value
        matrix[j, i] = value
    return matrix


def _rank_truncate(matrix: np.ndarray, rank: int):
    values, vectors = np.linalg.eigh(matrix)
    ids = np.argsort(np.abs(values))[::-1][:rank]
    return values[ids], vectors[:, ids]


def _separable_predict(z: np.ndarray, linear: np.ndarray, values: np.ndarray, vectors: np.ndarray):
    return z @ linear + np.sum((z @ vectors) ** 2 * values[None, :], axis=1)


def _signal(rng: np.random.Generator, segments: int, length: int):
    total = segments * length
    x = np.zeros(total)
    starts = np.zeros(total, dtype=bool)
    for segment in range(segments):
        begin = segment * length
        starts[begin] = True
        x[begin] = rng.normal()
        for t in range(begin + 1, begin + length):
            x[t] = 0.72 * x[t - 1] + rng.normal(scale=0.65)
    return x, starts


def volterra_trial(seed: int, train_segments: int) -> dict:
    rng = np.random.default_rng(9000 + seed)
    memory, rank_true, length = 16, 3, 22
    decay = np.exp(-np.arange(memory) / 6.0)
    linear_true = rng.normal(scale=0.18, size=memory) * decay
    vectors_true = rng.normal(size=(memory, rank_true)) * decay[:, None]
    vectors_true /= np.maximum(np.linalg.norm(vectors_true, axis=0), 1e-12)
    values_true = np.array([0.42, -0.31, 0.22])

    train_x, train_starts = _signal(rng, train_segments, length)
    test_x, test_starts = _signal(rng, 30, length)
    train_reset = lag_matrix(train_x, memory, train_starts, True)
    test_reset = lag_matrix(test_x, memory, test_starts, True)
    train_noreset = lag_matrix(train_x, memory, train_starts, False)
    test_noreset = lag_matrix(test_x, memory, test_starts, False)

    train_y = _separable_predict(
        train_reset, linear_true, values_true, vectors_true
    ) + rng.normal(scale=0.025, size=len(train_x))
    test_y = _separable_predict(test_reset, linear_true, values_true, vectors_true)

    q_reset, pairs = quadratic_features(train_reset)
    design_reset = np.column_stack([train_reset, q_reset])
    coef_reset = ridge(design_reset, train_y, 2e-3)
    linear_reset = coef_reset[:memory]
    dense_matrix = _coef_to_matrix(coef_reset[memory:], pairs, memory)
    dense_test_q, _ = quadratic_features(test_reset)
    dense_pred = np.column_stack([test_reset, dense_test_q]) @ coef_reset
    values, vectors = _rank_truncate(dense_matrix, rank_true)
    separable_pred = _separable_predict(test_reset, linear_reset, values, vectors)

    q_noreset, pairs_noreset = quadratic_features(train_noreset)
    coef_noreset = ridge(np.column_stack([train_noreset, q_noreset]), train_y, 2e-3)
    matrix_noreset = _coef_to_matrix(coef_noreset[memory:], pairs_noreset, memory)
    values_nr, vectors_nr = _rank_truncate(matrix_noreset, rank_true)
    noreset_pred = _separable_predict(
        test_noreset, coef_noreset[:memory], values_nr, vectors_nr
    )
    linear_coef = ridge(train_reset, train_y, 2e-3)
    linear_pred = test_reset @ linear_coef

    rmse = lambda pred: float(np.sqrt(np.mean((pred - test_y) ** 2)))
    return {
        "seed": seed,
        "train_segments": train_segments,
        "linear_rmse": rmse(linear_pred),
        "dense_volterra_rmse": rmse(dense_pred),
        "separable_reset_rmse": rmse(separable_pred),
        "separable_noreset_rmse": rmse(noreset_pred),
        "dense_parameters": memory + memory * (memory + 1) // 2,
        "separable_parameters": memory + rank_true * (memory + 1),
    }


def volterra_dense_rank_stress(seed: int) -> dict:
    """Violates the separable low-rank assumption while retaining boundary markers."""
    rng = np.random.default_rng(12000 + seed)
    memory, length = 16, 22
    train_x, train_starts = _signal(rng, 60, length)
    test_x, test_starts = _signal(rng, 30, length)
    train_z = lag_matrix(train_x, memory, train_starts, True)
    test_z = lag_matrix(test_x, memory, test_starts, True)
    linear_true = rng.normal(scale=0.08, size=memory)
    raw = rng.normal(size=(memory, memory))
    dense_true = (raw + raw.T) / (8.0 * math.sqrt(memory))
    train_y = train_z @ linear_true + np.einsum("ni,ij,nj->n", train_z, dense_true, train_z)
    train_y += rng.normal(scale=0.025, size=len(train_y))
    test_y = test_z @ linear_true + np.einsum("ni,ij,nj->n", test_z, dense_true, test_z)

    train_q, pairs = quadratic_features(train_z)
    coef = ridge(np.column_stack([train_z, train_q]), train_y, 2e-3)
    test_q, _ = quadratic_features(test_z)
    dense_pred = np.column_stack([test_z, test_q]) @ coef
    fitted_matrix = _coef_to_matrix(coef[memory:], pairs, memory)
    values, vectors = _rank_truncate(fitted_matrix, 3)
    rank3_pred = _separable_predict(test_z, coef[:memory], values, vectors)
    return {
        "seed": seed,
        "dense_rmse": float(np.sqrt(np.mean((dense_pred - test_y) ** 2))),
        "rank3_rmse": float(np.sqrt(np.mean((rank3_pred - test_y) ** 2))),
    }


def run_volterra() -> dict:
    cases = [volterra_trial(seed, segments) for seed in range(8) for segments in (16, 48)]
    sep_dense = sum(c["separable_reset_rmse"] <= 1.10 * c["dense_volterra_rmse"] for c in cases)
    sep_linear = sum(c["separable_reset_rmse"] < c["linear_rmse"] for c in cases)
    reset_wins = sum(c["separable_reset_rmse"] < c["separable_noreset_rmse"] for c in cases)
    dense_stress = [volterra_dense_rank_stress(seed) for seed in range(6)]
    return {
        "cases": cases,
        "dense_rank_stress": dense_stress,
        "summary": {
            "case_count": len(cases),
            "within_10pct_of_dense": sep_dense,
            "beats_linear": sep_linear,
            "reset_beats_noreset": reset_wins,
            "mean_dense_rmse": float(np.mean([c["dense_volterra_rmse"] for c in cases])),
            "mean_separable_reset_rmse": float(np.mean([c["separable_reset_rmse"] for c in cases])),
            "mean_separable_noreset_rmse": float(np.mean([c["separable_noreset_rmse"] for c in cases])),
            "mean_linear_rmse": float(np.mean([c["linear_rmse"] for c in cases])),
            "parameter_reduction": float(
                1.0 - cases[0]["separable_parameters"] / cases[0]["dense_parameters"]
            ),
            "dense_rank_stress_dense_beats_rank3": sum(
                c["dense_rmse"] < c["rank3_rmse"] for c in dense_stress
            ),
            "dense_rank_stress_mean_dense_rmse": float(
                np.mean([c["dense_rmse"] for c in dense_stress])
            ),
            "dense_rank_stress_mean_rank3_rmse": float(
                np.mean([c["rank3_rmse"] for c in dense_stress])
            ),
            "status": (
                "DEPLOY_KERNEL_BOTTLENECK_BROKEN_LOW_RANK_BOUNDARIES_REQUIRED_TRAINING_OPEN"
                if sep_dense >= 12 and sep_linear >= 14 and reset_wins >= 12
                else "NOT_BROKEN"
            ),
        },
    }


def run_all() -> dict:
    started = time.perf_counter()
    result = {
        "steinbuch": run_steinbuch(),
        "choquet": run_choquet(),
        "volterra": run_volterra(),
    }
    result["elapsed_seconds"] = time.perf_counter() - started
    return result


if __name__ == "__main__":
    output = run_all()
    path = HERE / "R196_RESULT.json"
    path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps({k: v["summary"] for k, v in output.items() if isinstance(v, dict)}, indent=2))
    print(f"wrote {path}")
