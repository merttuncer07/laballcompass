from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from basin_authority_teacher import TinyTanhXOR, locate_bad_basins
from basin_edge_teacher import compare_edge_and_greedy


GOOD_REFERENCE_SEEDS = {2: 4, 3: 2, 4: 4}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--basins-per-width", type=int, default=2)
    parser.add_argument("--candidate-count", type=int, default=36)
    parser.add_argument("--retrain-steps", type=int, default=800)
    parser.add_argument("--budget", type=int, default=40)
    args = parser.parse_args()

    comparisons = []
    references = {}
    for hidden in (2, 3, 4):
        model = TinyTanhXOR(hidden)
        reference_seed = GOOD_REFERENCE_SEEDS[hidden]
        good = model.train(model.initialize(reference_seed), max_steps=3500)
        references[str(hidden)] = {"seed": reference_seed, "loss": good.loss}
        if good.loss > 1e-3:
            raise RuntimeError(f"fixed good reference failed for hidden={hidden}: {good.loss}")
        bad_basins = locate_bad_basins(hidden, range(500), count=args.basins_per_width)
        for bad_seed, bad in bad_basins:
            comparisons.append(
                compare_edge_and_greedy(
                    model,
                    bad.theta,
                    good.theta,
                    bad_seed=bad_seed,
                    candidate_seed=200_000 + hidden * 1_000 + bad_seed,
                    total_budget=args.budget,
                    random_candidates=args.candidate_count,
                    retrain_steps=args.retrain_steps,
                ).to_jsonable()
            )

    edge_successes = [item for item in comparisons if item["edge"] and item["edge"]["success"]]
    greedy_successes = [item for item in comparisons if item["greedy"] and item["greedy"]["success"]]
    edge_advantages = [item for item in comparisons if item["edge_advantage"]]
    anti_greedy_edge = [
        item for item in edge_successes
        if item["edge"]["immediate_slope"] is not None and item["edge"]["immediate_slope"] > 0.0
    ]
    result = {
        "schema": "basin-edge-teacher-benchmark/v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "configuration": {
            "architectures": [2, 3, 4],
            "basins_per_width": args.basins_per_width,
            "candidate_count_random": args.candidate_count,
            "retrain_steps": args.retrain_steps,
            "equal_retraining_unit_budget": args.budget,
            "norms": [0.5, 1.0, 1.5, 2.0, 3.0],
            "edge_bisection_units": 6,
            "reference_unit_charged_per_case": 1,
        },
        "good_references": references,
        "summary": {
            "bad_basins_tested": len(comparisons),
            "edge_crossings": len(edge_successes),
            "greedy_crossings": len(greedy_successes),
            "edge_advantages": len(edge_advantages),
            "anti_greedy_edge_successes": len(anti_greedy_edge),
            "edge_abstentions_or_no_crossing": len(comparisons) - len(edge_successes),
        },
        "comparisons": comparisons,
        "claim_boundary": "Local straight-line edge approximation on small tanh XOR learners. Equal recorded post-retraining-unit budgets; no global boundary, minimality, scaling, novelty, or deployment claim.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

