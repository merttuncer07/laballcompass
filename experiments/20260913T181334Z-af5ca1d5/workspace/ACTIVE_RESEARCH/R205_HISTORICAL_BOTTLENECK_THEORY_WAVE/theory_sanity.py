from __future__ import annotations

import itertools

import numpy as np


def thinned_transition(transition: np.ndarray, retention: float):
    identity = np.eye(len(transition))
    return (
        retention
        * transition
        @ np.linalg.inv(identity - (1.0 - retention) * transition)
    )


def recover_nested_thinning(first: np.ndarray, second: np.ndarray):
    identity = np.eye(len(first))
    first_transform = np.linalg.inv(first) - identity
    second_transform = np.linalg.inv(second) - identity
    retention = float(
        np.sum(first_transform * first_transform)
        / np.sum(second_transform * first_transform)
    )
    transition = np.linalg.inv(identity + retention * first_transform)
    return retention, transition


def preisach_prefix_output(weights: np.ndarray, frontier: np.ndarray):
    prefix = np.cumsum(weights, axis=1)
    active = frontier >= 0
    return float(
        np.sum(prefix[np.arange(len(frontier))[active], frontier[active]])
    )


def preisach_dense_output(weights: np.ndarray, frontier: np.ndarray):
    state = np.zeros_like(weights)
    for row, stop in enumerate(frontier):
        if stop >= 0:
            state[row, : stop + 1] = 1.0
    return float(np.sum(weights * state))


def recover_symmetric_low_rank(matrix: np.ndarray, probe_count: int, seed: int = 0):
    dimension = len(matrix)
    rng = np.random.default_rng(seed)
    probes = rng.normal(size=(dimension, probe_count))

    def quadratic(vector):
        return float(vector @ matrix @ vector)

    def bilinear(left, right):
        return (quadratic(left + right) - quadratic(left - right)) / 4.0

    image = np.empty((dimension, probe_count))
    identity = np.eye(dimension)
    for row in range(dimension):
        for column in range(probe_count):
            image[row, column] = bilinear(identity[row], probes[:, column])
    basis, _ = np.linalg.qr(image)
    basis = basis[:, :probe_count]
    core = np.empty((probe_count, probe_count))
    for row in range(probe_count):
        for column in range(probe_count):
            core[row, column] = bilinear(basis[:, row], basis[:, column])
    return basis @ core @ basis.T


def glushkov_polynomial_outputs(word):
    modulus = 5
    transitions = {
        "a": (
            np.array([[0, 1], [1, 0]], dtype=int),
            np.array([[1, 1], [0, 1]], dtype=int),
            np.array([[1, 0], [1, 1]], dtype=int),
        ),
        "b": (
            np.array([[1, 1], [0, 1]], dtype=int),
            np.array([[0, 1], [1, 0]], dtype=int),
            np.array([[1, 1], [0, 1]], dtype=int),
        ),
    }
    states = [
        np.array([1, 0], dtype=int),
        np.array([0, 1], dtype=int),
        np.array([1, 0], dtype=int),
    ]
    outputs = [
        np.array([1, 2], dtype=int),
        np.array([2, 1], dtype=int),
        np.array([1, 3], dtype=int),
    ]
    lifted = np.concatenate([states[0], np.kron(states[1], states[2])])
    lifted_output = np.concatenate(
        [outputs[0], 2 * np.kron(outputs[1], outputs[2])]
    )
    for symbol in word:
        blocks = transitions[symbol]
        states = [blocks[index] @ states[index] % modulus for index in range(3)]
        lifted_transition = np.zeros((6, 6), dtype=int)
        lifted_transition[:2, :2] = blocks[0]
        lifted_transition[2:, 2:] = np.kron(blocks[1], blocks[2])
        lifted = lifted_transition @ lifted % modulus
    direct = int(
        (
            outputs[0] @ states[0]
            + 2 * (outputs[1] @ states[1]) * (outputs[2] @ states[2])
        )
        % modulus
    )
    represented = int(lifted_output @ lifted % modulus)
    return direct, represented


def reduce_convex(points: np.ndarray, weights: np.ndarray, tolerance: float = 1e-11):
    points = points.copy()
    weights = weights.copy()
    dimension = points.shape[1]
    while len(weights) > dimension + 1:
        augmented = np.vstack([points.T, np.ones(len(points))])
        _, _, right = np.linalg.svd(augmented, full_matrices=True)
        dependence = right[-1]
        positive = dependence > tolerance
        if not np.any(positive):
            dependence = -dependence
            positive = dependence > tolerance
        ratio = np.full(len(weights), np.inf)
        ratio[positive] = weights[positive] / dependence[positive]
        drop = int(np.argmin(ratio))
        step = ratio[drop]
        weights = weights - step * dependence
        # In exact arithmetic the selected coefficient is zero.  Delete that
        # index explicitly so floating-point residue cannot stall the
        # constructive Caratheodory reduction.
        points = np.delete(points, drop, axis=0)
        weights = np.delete(weights, drop)
        weights = np.maximum(weights, 0.0)
        weights /= np.sum(weights)
    return points, weights


def compress_signed_responses(responses: np.ndarray, coefficients: np.ndarray):
    compressed = []
    for sign in (1.0, -1.0):
        selected = coefficients * sign > 0.0
        mass = float(np.sum(np.abs(coefficients[selected])))
        if not mass:
            continue
        points, weights = reduce_convex(
            responses[selected], np.abs(coefficients[selected]) / mass
        )
        compressed.append((sign, mass, points, weights))
    return compressed


def compressed_response(compressed):
    if not compressed:
        return np.array([])
    result = np.zeros(compressed[0][2].shape[1])
    for sign, mass, points, weights in compressed:
        result += sign * mass * (weights @ points)
    return result


def two_color_core_is_unsatisfiable(edges):
    vertices = sorted(set(itertools.chain.from_iterable(edges)))
    for colors in itertools.product((0, 1), repeat=len(vertices)):
        assignment = dict(zip(vertices, colors))
        if all(assignment[left] != assignment[right] for left, right in edges):
            return False
    return True


def permute_edges(edges, permutation):
    return [tuple(sorted((permutation[left], permutation[right]))) for left, right in edges]
