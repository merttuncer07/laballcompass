from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from basin_authority_teacher import TinyTanhXOR, designed_candidates, locate_bad_basins
from basin_edge_teacher import evaluate_ranked, rank_by_soft_modes, rank_candidates, soft_mode_geometry


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--basins-per-width", type=int, default=2)
    parser.add_argument("--candidate-count", type=int, default=36)
    parser.add_argument("--retrain-steps", type=int, default=800)
    parser.add_argument("--budget", type=int, default=40)
    args = parser.parse_args()
    norms = (0.5, 1.0, 1.5, 2.0, 3.0)
    candidate_limit = args.budget // len(norms)

    comparisons = []
    for hidden in (2, 3, 4):
        model = TinyTanhXOR(hidden)
        for bad_seed, bad in locate_bad_basins(hidden, range(500), count=args.basins_per_width):
            candidates = designed_candidates(
                model,
                bad.theta,
                seed=300_000 + hidden * 1_000 + bad_seed,
                random_count=args.candidate_count,
            )
            eigenvalues, modes, gradient_evaluations = soft_mode_geometry(model, bad.theta)
            soft = evaluate_ranked(
                model,
                bad.theta,
                rank_by_soft_modes(model, bad.theta, candidates, modes),
                method="soft_mode_edge",
                candidate_limit=candidate_limit,
                norms=norms,
                success_loss=1e-3,
                retrain_steps=args.retrain_steps,
            )
            greedy = evaluate_ranked(
                model,
                bad.theta,
                rank_candidates(candidates, method="greedy"),
                method="greedy",
                candidate_limit=candidate_limit,
                norms=norms,
                success_loss=1e-3,
                retrain_steps=args.retrain_steps,
            )
            advantage = soft.success and (not greedy.success or soft.minimum_norm < greedy.minimum_norm)
            comparisons.append({
                "hidden": hidden,
                "bad_seed": bad_seed,
                "bad_loss": bad.loss,
                "soft_eigenvalues": eigenvalues.tolist(),
                "soft_gradient_evaluations": gradient_evaluations,
                "equal_retraining_budget": args.budget,
                "soft": soft.__dict__,
                "greedy": greedy.__dict__,
                "soft_advantage": advantage,
            })

    soft_success = [item for item in comparisons if item["soft"]["success"]]
    greedy_success = [item for item in comparisons if item["greedy"]["success"]]
    advantages = [item for item in comparisons if item["soft_advantage"]]
    anti_greedy = [item for item in soft_success if item["soft"]["immediate_slope"] > 0.0]
    result = {
        "schema": "basin-soft-edge-benchmark/v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "configuration": {
            "architectures": [2, 3, 4],
            "basins_per_width": args.basins_per_width,
            "candidate_count_random": args.candidate_count,
            "retrain_steps": args.retrain_steps,
            "equal_retraining_unit_budget": args.budget,
            "norms": list(norms),
            "soft_modes": 4,
        },
        "summary": {
            "bad_basins_tested": len(comparisons),
            "soft_crossings": len(soft_success),
            "greedy_crossings": len(greedy_success),
            "soft_advantages": len(advantages),
            "anti_greedy_soft_successes": len(anti_greedy),
        },
        "comparisons": comparisons,
        "claim_boundary": "Numerical low-curvature functional-mode ranking on small tanh XOR networks, with equal retraining budgets but extra recorded Hessian-gradient evaluations."
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
