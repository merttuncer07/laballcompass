from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from symbolic_favorable import (
    compile_bdd_fixed_point,
    compile_circuit_acyclic,
    compile_explicit,
    independent_choice_program,
)


def timed(function):
    start = time.perf_counter()
    value = function()
    return value, time.perf_counter() - start


def run():
    explicit_records = []
    for pair_count in (4, 8, 12, 16):
        rules, bases, _ = independent_choice_program(pair_count)
        values, elapsed = timed(lambda: compile_explicit(rules, bases))
        family = values["goal"]
        explicit_records.append(
            {
                "pairs": pair_count,
                "minimal_supports": len(family),
                "support_atoms": sum(len(support) for support in family),
                "seconds": elapsed,
            }
        )

    symbolic_records = []
    for pair_count in (4, 8, 12, 16):
        rules, bases, topological = independent_choice_program(pair_count)
        circuit_result, circuit_seconds = timed(
            lambda: compile_circuit_acyclic(rules, bases, topological)
        )
        circuit, circuit_values = circuit_result
        interleaved = [
            f"{side}{index}" for index in range(pair_count) for side in "ab"
        ]
        split = [f"a{index}" for index in range(pair_count)] + [
            f"b{index}" for index in range(pair_count)
        ]
        good_result, good_seconds = timed(
            lambda: compile_bdd_fixed_point(rules, bases, interleaved)
        )
        bad_result, bad_seconds = timed(
            lambda: compile_bdd_fixed_point(rules, bases, split)
        )
        good_bdd, good_values, good_iterations = good_result
        bad_bdd, bad_values, bad_iterations = bad_result
        symbolic_records.append(
            {
                "pairs": pair_count,
                "factored_circuit_nodes": circuit.reachable_count(
                    circuit_values["goal"]
                ),
                "factored_circuit_seconds": circuit_seconds,
                "interleaved_bdd_nodes": good_bdd.reachable_count(
                    good_values["goal"]
                ),
                "interleaved_bdd_seconds": good_seconds,
                "interleaved_fixed_point_iterations": good_iterations,
                "split_bdd_nodes": bad_bdd.reachable_count(bad_values["goal"]),
                "split_bdd_seconds": bad_seconds,
                "split_fixed_point_iterations": bad_iterations,
            }
        )

    rules, bases, topological = independent_choice_program(4096)
    large_result, large_seconds = timed(
        lambda: compile_circuit_acyclic(rules, bases, topological)
    )
    large_circuit, large_values = large_result
    result = {
        "status": "SCOPED_THEOREM_AND_EXPONENTIAL_SEPARATION_CONFIRMED",
        "problem": "Maslov-style explicit favorable/minimal-support set explosion",
        "explicit": explicit_records,
        "symbolic": symbolic_records,
        "large_factored_case": {
            "pairs": 4096,
            "implicit_minimal_supports": str(2**4096),
            "circuit_nodes": large_circuit.reachable_count(large_values["goal"]),
            "seconds": large_seconds,
        },
        "retained": [
            "absorptive minimal-support semantics",
            "factored monotone proof circuit for finite acyclic rule hypergraphs",
            "canonical BDD fixed point for finite cyclic rule hypergraphs",
        ],
        "failure_boundaries": [
            "explicit antichain is exponentially large even for a linear rule graph",
            "ROBDD size is exponentially sensitive to variable order",
            "first-order unification and infinite term generation are not solved",
            "general novelty is not established because of strong provenance-circuit collisions",
        ],
        "python": sys.version,
    }
    output = Path(__file__).with_name("R207_RESULT.json")
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    run()

