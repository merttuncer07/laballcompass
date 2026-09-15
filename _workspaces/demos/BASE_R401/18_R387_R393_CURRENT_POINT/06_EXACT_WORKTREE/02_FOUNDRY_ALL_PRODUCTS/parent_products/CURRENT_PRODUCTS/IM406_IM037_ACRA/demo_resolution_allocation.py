from __future__ import annotations

import json
from pathlib import Path

from acra import AdaptiveConsequenceResolutionAllocator, DecisionRegion, ResolutionOption


def evaluate() -> dict[str, object]:
    allocator = AdaptiveConsequenceResolutionAllocator(
        [
            DecisionRegion("emergency_onset", 10, 1, 5),
            DecisionRegion("resonance_band", 1, 10, 4),
            DecisionRegion("regime_change", 8, 2, 4),
            DecisionRegion("machine_vibration", 2, 8, 5),
            DecisionRegion("mixed_control", 4, 4, 3),
            DecisionRegion("low_consequence_monitor", 1, 1, 0.5),
        ],
        [
            ResolutionOption("coarse", 1, 8, 8),
            ResolutionOption("short_time", 3, 1, 6),
            ResolutionOption("long_frequency", 3, 6, 1),
            ResolutionOption("balanced", 4, 2.5, 2.5),
            ResolutionOption("fine_both", 8, 1, 1),
        ],
    )
    fixed = allocator.fixed_option("balanced")
    adaptive = allocator.allocate(fixed["total_cost"])
    return {
        "fixed_balanced": fixed,
        "adaptive_same_budget": adaptive,
        "decision_loss_reduction": 1.0
        - adaptive["total_decision_loss"] / fixed["total_decision_loss"],
    }


if __name__ == "__main__":
    result = evaluate()
    output = Path(__file__).with_name("resolution_allocation_results.json")
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
