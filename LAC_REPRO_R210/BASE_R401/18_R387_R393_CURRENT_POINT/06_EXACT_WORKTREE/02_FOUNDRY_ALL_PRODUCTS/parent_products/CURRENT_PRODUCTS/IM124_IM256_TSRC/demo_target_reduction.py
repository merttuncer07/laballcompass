from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from tsrc import FeatureSpec, TargetSufficientReductionCertifier


def evaluate() -> dict[str, object]:
    rng = np.random.default_rng(20260825)
    features = [
        FeatureSpec("core_demand", 2.0, 3.0, 8.0),
        FeatureSpec("core_capacity", -1.6, 3.0, 7.0),
        FeatureSpec("core_delay", -1.2, 3.0, 6.0),
    ] + [
        FeatureSpec(f"detail_{index:02d}", coefficient, 0.5, cost)
        for index, (coefficient, cost) in enumerate(
            zip([0.08, -0.06, 0.05, 0.04, -0.03, 0.02, 0.015, -0.01, 0.008], [3, 4, 2, 5, 3, 2, 4, 2, 3]),
            start=1,
        )
    ]
    certifier = TargetSufficientReductionCertifier(features)

    # Two operational regimes are constructed at scores -3 and +3.  Random
    # non-core detail remains, while core_demand is solved so the protected
    # action margin is explicit rather than accidental.
    negative = rng.normal(0.0, 0.25, (2000, len(features)))
    positive = rng.normal(0.0, 0.25, (2000, len(features)))
    negative[:, 3:] = np.clip(negative[:, 3:], -0.5, 0.5)
    positive[:, 3:] = np.clip(positive[:, 3:], -0.5, 0.5)
    weights = np.array([feature.coefficient for feature in features])
    negative[:, 0] = (-3.0 - negative[:, 1:] @ weights[1:]) / weights[0]
    positive[:, 0] = (3.0 - positive[:, 1:] @ weights[1:]) / weights[0]
    values = np.vstack([negative, positive])
    protected_margin = certifier.margin_on_values(values)
    certificate = certifier.optimize(protected_margin, reserve=0.20)
    evaluated = certifier.evaluate(certificate, values)
    return {
        "rows": len(values),
        "feature_count_before": len(features),
        "feature_count_after": len(evaluated.retained_features),
        "certificate": evaluated.as_dict(),
    }


if __name__ == "__main__":
    result = evaluate()
    output = Path(__file__).with_name("target_reduction_results.json")
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
