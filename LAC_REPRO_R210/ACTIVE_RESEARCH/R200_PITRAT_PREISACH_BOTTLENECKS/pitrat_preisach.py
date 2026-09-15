from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent


# ---------------------------------------------------------------------------
# HM-08: Pitrat metaknowledge -> reusable minimal failure explanations


def complete_multipartite_graph(parts: int, per_part: int):
    count = parts * per_part
    adjacency = [set() for _ in range(count)]
    for left in range(count):
        for right in range(left + 1, count):
            if left // per_part != right // per_part:
                adjacency[left].add(right)
                adjacency[right].add(left)
    return adjacency


class NogoodStore:
    def __init__(self, vertex_class: dict[int, int] | None = None, schema: bool = False):
        self.items: list[frozenset[tuple[int, int]]] = []
        self.vertex_class = vertex_class
        self.schema = schema
        self.different_color_classes: set[int] = set()

    def violates(self, assignment: dict[int, int]) -> bool:
        active = assignment.items()
        active_set = set(active)
        if any(nogood <= active_set for nogood in self.items):
            return True
        if self.schema and self.vertex_class:
            colors_by_class: dict[int, set[int]] = {}
            for vertex, color in assignment.items():
                colors_by_class.setdefault(self.vertex_class[vertex], set()).add(color)
            if any(
                len(colors_by_class.get(class_id, set())) >= 2
                for class_id in self.different_color_classes
            ):
                return True
        return False

    def violated_explanation(self, assignment: dict[int, int]):
        active_set = set(assignment.items())
        for nogood in self.items:
            if nogood <= active_set:
                return nogood
        if self.schema and self.vertex_class:
            by_class: dict[int, list[tuple[int, int]]] = {}
            for item in assignment.items():
                by_class.setdefault(self.vertex_class[item[0]], []).append(item)
            for class_id in self.different_color_classes:
                items = by_class.get(class_id, [])
                for left in range(len(items)):
                    for right in range(left + 1, len(items)):
                        if items[left][1] != items[right][1]:
                            return frozenset((items[left], items[right]))
        return None

    def add(self, explanation):
        explanation = frozenset(explanation)
        if any(existing <= explanation for existing in self.items):
            return
        self.items = [existing for existing in self.items if not explanation < existing]
        self.items.append(explanation)
        if self.schema and self.vertex_class and len(explanation) == 2:
            left, right = tuple(explanation)
            if (
                self.vertex_class[left[0]] == self.vertex_class[right[0]]
                and left[1] != right[1]
            ):
                self.different_color_classes.add(self.vertex_class[left[0]])


def structural_vertex_classes(adjacency):
    signatures = {}
    classes = {}
    for vertex, neighbors in enumerate(adjacency):
        signature = tuple(sorted(neighbors))
        if signature not in signatures:
            signatures[signature] = len(signatures)
        classes[vertex] = signatures[signature]
    return classes


@dataclass
class ColoringResult:
    solved: bool
    nodes: int
    capped: bool


def solve_coloring(
    adjacency,
    colors: int,
    preassigned: dict[int, int],
    mode: str,
    store: NogoodStore | None = None,
    node_cap: int = 250_000,
):
    store = store if store is not None else NogoodStore()
    assignment = dict(preassigned)
    nodes = 0
    capped = False

    for vertex, color in assignment.items():
        for neighbor in adjacency[vertex]:
            if neighbor in assignment and assignment[neighbor] == color:
                if mode != "none":
                    store.add({(vertex, color), (neighbor, color)})
                return ColoringResult(False, 1, False)

    def recurse():
        nonlocal nodes, capped
        nodes += 1
        if nodes > node_cap:
            capped = True
            return False, frozenset(assignment.items())
        if mode != "none" and store.violates(assignment):
            explanation = store.violated_explanation(assignment)
            return False, explanation or frozenset(assignment.items())
        if len(assignment) == len(adjacency):
            return True, None

        best_vertex = None
        best_available = None
        for vertex in range(len(adjacency)):
            if vertex in assignment:
                continue
            blocked = {assignment[n] for n in adjacency[vertex] if n in assignment}
            available = [color for color in range(colors) if color not in blocked]
            if best_available is None or len(available) < len(best_available):
                best_vertex, best_available = vertex, available
                if not available:
                    break

        if not best_available:
            if mode == "core":
                explanation = set()
                for color in range(colors):
                    blockers = [
                        neighbor
                        for neighbor in adjacency[best_vertex]
                        if assignment.get(neighbor) == color
                    ]
                    if blockers:
                        explanation.add((min(blockers), color))
                store.add(explanation)
                return False, frozenset(explanation)
            elif mode == "full":
                store.add(assignment.items())
            return False, frozenset(assignment.items())

        child_explanations = []
        for color in best_available:
            assignment[best_vertex] = color
            solved, explanation = recurse()
            if solved:
                return True, None
            if explanation is not None:
                child_explanations.append(
                    frozenset(item for item in explanation if item != (best_vertex, color))
                )
            del assignment[best_vertex]
            if capped:
                return False, frozenset(assignment.items())
        resolved = frozenset().union(*child_explanations) if child_explanations else frozenset(assignment.items())
        if mode == "core":
            store.add(resolved)
        if mode == "full" and assignment:
            store.add(assignment.items())
        return False, resolved if mode == "core" else frozenset(assignment.items())

    solved, _ = recurse()
    return ColoringResult(solved, nodes, capped)


def coloring_queries(rng: np.random.Generator, parts: int, per_part: int, colors: int):
    queries = []
    for query_index in range(36):
        if query_index % 2 == 0:
            permutation = rng.permutation(colors)
            selected = {}
            for part in range(parts):
                vertex = part * per_part + int(rng.integers(per_part))
                selected[vertex] = int(permutation[part])
            queries.append(selected)
        else:
            part = int(rng.integers(parts))
            vertices = rng.choice(
                np.arange(part * per_part, (part + 1) * per_part), 2, replace=False
            )
            first_color, second_color = rng.choice(colors, 2, replace=False)
            selected = {int(vertices[0]): int(first_color), int(vertices[1]): int(second_color)}
            # Same-part vertices are nonadjacent, so this is not a direct conflict.
            # In a complete k-partite graph with exactly k colors it is globally
            # impossible and must be discovered through the search.
            queries.append(selected)
    return queries


def pitrat_trial(seed: int, parts: int, per_part: int) -> dict:
    rng = np.random.default_rng(310000 + seed + 101 * parts)
    graph = complete_multipartite_graph(parts=parts, per_part=per_part)
    vertex_class = structural_vertex_classes(graph)
    queries = coloring_queries(rng, parts, per_part, parts)
    shared_core = NogoodStore()
    shared_schema = NogoodStore(vertex_class, schema=True)
    shared_full = NogoodStore()
    totals = {
        "plain": 0,
        "fresh_core": 0,
        "shared_core": 0,
        "shared_schema": 0,
        "shared_full": 0,
    }
    outcomes = []
    capped = False
    for query in queries:
        plain = solve_coloring(graph, parts, query, "none")
        fresh_core = solve_coloring(graph, parts, query, "core", NogoodStore())
        core = solve_coloring(graph, parts, query, "core", shared_core)
        schema = solve_coloring(graph, parts, query, "core", shared_schema)
        full = solve_coloring(graph, parts, query, "full", shared_full)
        results = (plain, fresh_core, core, schema, full)
        if len({result.solved for result in results}) != 1:
            raise AssertionError("learned explanation changed satisfiability")
        capped |= any(result.capped for result in results)
        outcomes.append(plain.solved)
        for name, result in zip(totals, results):
            totals[name] += result.nodes
    return {
        "seed": seed,
        "parts_colors": parts,
        "vertices_per_part": per_part,
        "queries": len(queries),
        "satisfiable": sum(outcomes),
        "unsatisfiable": len(outcomes) - sum(outcomes),
        "nodes": totals,
        "shared_core_nogoods": len(shared_core.items),
        "shared_schema_nogoods": len(shared_schema.items),
        "shared_schema_rules": len(shared_schema.different_color_classes),
        "shared_full_nogoods": len(shared_full.items),
        "capped": capped,
    }


def run_pitrat():
    cases = [
        pitrat_trial(seed, parts, per_part)
        for seed in range(6)
        for parts, per_part in ((4, 6), (5, 5), (6, 4))
    ]
    core_plain = sum(c["nodes"]["shared_core"] < c["nodes"]["plain"] for c in cases)
    core_fresh = sum(c["nodes"]["shared_core"] < c["nodes"]["fresh_core"] for c in cases)
    core_full = sum(c["nodes"]["shared_core"] < c["nodes"]["shared_full"] for c in cases)
    schema_core = sum(c["nodes"]["shared_schema"] < c["nodes"]["shared_core"] for c in cases)
    return {
        "cases": cases,
        "summary": {
            "case_count": len(cases),
            "shared_core_beats_plain": core_plain,
            "shared_core_beats_fresh_core": core_fresh,
            "shared_core_beats_full_state_nogoods": core_full,
            "quotient_schema_beats_exact_core": schema_core,
            "mean_plain_nodes": float(np.mean([c["nodes"]["plain"] for c in cases])),
            "mean_fresh_core_nodes": float(
                np.mean([c["nodes"]["fresh_core"] for c in cases])
            ),
            "mean_shared_core_nodes": float(
                np.mean([c["nodes"]["shared_core"] for c in cases])
            ),
            "mean_shared_schema_nodes": float(
                np.mean([c["nodes"]["shared_schema"] for c in cases])
            ),
            "mean_shared_full_nodes": float(
                np.mean([c["nodes"]["shared_full"] for c in cases])
            ),
            "any_node_cap": any(c["capped"] for c in cases),
            "status": (
                "RESOLVED_FAILURE_SCHEMA_TRANSFERS_UNDER_STRUCTURAL_QUOTIENT"
                if schema_core >= 15
                else "NOT_BROKEN"
            ),
        },
    }


# ---------------------------------------------------------------------------
# HM-11: Preisach relays -> exact O(n) frontier + low-rank density factors


class DensePreisach:
    def __init__(self, weights: np.ndarray):
        self.weights = weights
        self.levels = weights.shape[0]
        self.valid = np.greater.outer(np.arange(self.levels), np.arange(self.levels))
        self.state = np.where(self.valid, -1, 0).astype(np.int8)
        self.previous = -1

    def update(self, level: int) -> float:
        if level > self.previous:
            alpha = np.arange(self.levels)[:, None]
            self.state[(alpha <= level) & self.valid] = 1
        elif level < self.previous:
            beta = np.arange(self.levels)[None, :]
            self.state[(beta >= level) & self.valid] = -1
        self.previous = level
        return float(np.sum(self.weights * self.state))


class FrontierPreisach:
    def __init__(self, left_factor: np.ndarray, right_factor: np.ndarray):
        self.left = left_factor
        self.right = right_factor
        self.levels, self.rank = left_factor.shape
        self.prefix = np.cumsum(left_factor, axis=0)
        self.frontier = np.arange(self.levels, dtype=int)
        self.previous = -1
        total = 0.0
        for beta in range(self.levels):
            if beta + 1 < self.levels:
                segment = self.prefix[-1] - self.prefix[beta]
                total += float(segment @ self.right[beta])
        self.total_weight = total

    def update(self, level: int) -> float:
        if level > self.previous:
            ids = np.arange(level)
            self.frontier[ids] = np.maximum(self.frontier[ids], level)
        elif level < self.previous:
            ids = np.arange(level, self.levels)
            self.frontier[ids] = ids
        self.previous = level
        on_weight = 0.0
        for beta, stop in enumerate(self.frontier):
            if stop <= beta:
                continue
            segment = self.prefix[stop] - self.prefix[beta]
            on_weight += float(segment @ self.right[beta])
        return -self.total_weight + 2.0 * on_weight

    def expanded_state(self):
        alpha = np.arange(self.levels)[:, None]
        beta = np.arange(self.levels)[None, :]
        valid = alpha > beta
        return np.where(valid, np.where(alpha <= self.frontier[None, :], 1, -1), 0)


def masked_low_rank_weights(left: np.ndarray, right: np.ndarray):
    weights = left @ right.T
    valid = np.greater.outer(np.arange(len(left)), np.arange(len(left)))
    return np.where(valid, weights, 0.0)


def preisach_trial(seed: int, levels: int, rank: int = 4) -> dict:
    rng = np.random.default_rng(410000 + seed + levels)
    left = rng.normal(scale=0.15, size=(levels, rank))
    right = rng.normal(scale=0.15, size=(levels, rank))
    weights = masked_low_rank_weights(left, right)
    dense = DensePreisach(weights)
    frontier = FrontierPreisach(left, right)
    walk = np.empty(900, dtype=int)
    walk[0] = int(rng.integers(levels))
    for i in range(1, len(walk)):
        walk[i] = int(np.clip(walk[i - 1] + rng.integers(-7, 8), 0, levels - 1))
    max_output_error = 0.0
    max_state_error = 0
    for level in walk:
        dense_output = dense.update(int(level))
        frontier_output = frontier.update(int(level))
        max_output_error = max(max_output_error, abs(dense_output - frontier_output))
        max_state_error = max(
            max_state_error, int(np.max(np.abs(dense.state - frontier.expanded_state())))
        )

    dense_values = int(2 * np.sum(np.greater.outer(np.arange(levels), np.arange(levels))))
    factor_values = int(levels + 2 * levels * rank)

    # Dense-density stress: a rank-r approximation of an arbitrary triangular
    # density is not protected by the exact factor certificate.
    random_dense = np.where(
        np.greater.outer(np.arange(levels), np.arange(levels)),
        rng.normal(scale=0.2, size=(levels, levels)),
        0.0,
    )
    u, singular, vt = np.linalg.svd(random_dense, full_matrices=False)
    approx_left = u[:, :rank] * np.sqrt(singular[:rank])[None, :]
    approx_right = vt[:rank].T * np.sqrt(singular[:rank])[None, :]
    approximated = masked_low_rank_weights(approx_left, approx_right)
    dense_relative_error = float(
        np.linalg.norm(approximated - random_dense) / np.linalg.norm(random_dense)
    )
    return {
        "seed": seed,
        "levels": levels,
        "rank": rank,
        "max_exact_output_error": max_output_error,
        "max_exact_state_error": max_state_error,
        "dense_state_plus_weight_values": dense_values,
        "frontier_plus_factor_values": factor_values,
        "representation_reduction": dense_values / factor_values,
        "dense_density_rank_approximation_relative_error": dense_relative_error,
    }


def run_preisach():
    cases = [
        preisach_trial(seed, levels)
        for seed in range(8)
        for levels in (32, 64, 128)
    ]
    exact = sum(
        c["max_exact_output_error"] < 1e-9 and c["max_exact_state_error"] == 0
        for c in cases
    )
    largest = [c for c in cases if c["levels"] == 128]
    return {
        "cases": cases,
        "summary": {
            "case_count": len(cases),
            "exact_frontier_and_output": exact,
            "max_output_error": float(max(c["max_exact_output_error"] for c in cases)),
            "levels128_mean_representation_reduction": float(
                np.mean([c["representation_reduction"] for c in largest])
            ),
            "dense_density_mean_rank4_relative_error": float(
                np.mean([c["dense_density_rank_approximation_relative_error"] for c in cases])
            ),
            "status": (
                "SCALAR_PREISACH_STATE_AND_LOWRANK_DENSITY_EXACTLY_FACTORIZED_DENSE_DENSITY_OPEN"
                if exact == len(cases)
                else "NOT_BROKEN"
            ),
        },
    }


def run_all():
    started = time.perf_counter()
    result = {"pitrat": run_pitrat(), "preisach": run_preisach()}
    result["elapsed_seconds"] = time.perf_counter() - started
    return result


if __name__ == "__main__":
    result = run_all()
    path = HERE / "R200_RESULT.json"
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k: v["summary"] for k, v in result.items() if isinstance(v, dict)}, indent=2))
    print(f"wrote {path}")
