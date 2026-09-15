from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from basin_authority_teacher import FULL_AUTHORITY, TinyTanhXOR, compare_teachers, locate_bad_basins


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--basins-per-width", type=int, default=3)
    parser.add_argument("--candidate-count", type=int, default=72)
    parser.add_argument("--retrain-steps", type=int, default=800)
    args = parser.parse_args()

    comparisons = []
    missing = []
    for hidden in (2, 3, 4):
        basins = locate_bad_basins(hidden, range(500), count=args.basins_per_width)
        if len(basins) < args.basins_per_width:
            missing.append({"hidden": hidden, "requested": args.basins_per_width, "found": len(basins)})
        model = TinyTanhXOR(hidden)
        for index, (source_seed, training) in enumerate(basins):
            comparison = compare_teachers(
                model,
                training.theta,
                source_seed=source_seed,
                authority=FULL_AUTHORITY,
                candidate_seed=100_000 + hidden * 1_000 + source_seed,
                random_candidates=args.candidate_count,
                retrain_steps=args.retrain_steps,
            )
            comparisons.append(comparison.to_jsonable())

    eligible = [item for item in comparisons if item["basin"] is not None]
    matched_wins = [
        item for item in eligible
        if item["basin"]["success"] and not item["greedy_at_basin_norm"]["success"]
    ]
    anti_greedy = [item for item in eligible if item["basin"]["immediate_slope"] > 0.0]
    result = {
        "schema": "basin-authority-teacher-benchmark/v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "configuration": {
            "architectures": [2, 3, 4],
            "basins_per_width": args.basins_per_width,
            "candidate_count_random": args.candidate_count,
            "retrain_steps": args.retrain_steps,
            "designed_targets_per_point": 2,
            "success_loss": 0.001,
            "matched_intervention_norm": True,
        },
        "summary": {
            "bad_basins_tested": len(comparisons),
            "basin_crossing_found": len(eligible),
            "basin_beats_greedy_at_matched_norm": len(matched_wins),
            "successful_basin_directions_that_worsen_loss_locally": len(anti_greedy),
            "missing_bad_basins": missing,
        },
        "comparisons": comparisons,
        "claim_boundary": "Small deterministic XOR networks and empirical candidate search only; no large-network, optimality, novelty, or deployment claim.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
