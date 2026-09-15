import json
from pathlib import Path

from tgcars import FeatureSpec, ResolutionOption, allocate_certificate_aware_resolution, transport_gated_certificate_aware_resolution


def actual_loss(allocation, actual_weights):
    errors = {"coarse": 1.0, "fine": 0.1}
    return sum(actual_weights[x["region"]] * errors[x["option"]] ** 2 for x in allocation["allocations"])

features = [
    FeatureSpec("critical", 1.0, 0.08, 1.0),
    FeatureSpec("secondary", 0.6, 0.08, 1.0),
    FeatureSpec("nuisance", 0.95, 0.19, 20.0),
]
options = [ResolutionOption("coarse", 1.0, 1.0, 0.0), ResolutionOption("fine", 3.0, 0.1, 0.0)]
source = [-1.0, -0.5, 0.0, 0.5, 1.0] * 4
shifted = [x + 2.0 for x in source]
blind = allocate_certificate_aware_resolution(features, protected_margin=0.19, options=options, budget=5.0)
guarded = transport_gated_certificate_aware_resolution(
    features, protected_margin=0.19, options=options, budget=5.0,
    source_residuals=source, target_residuals=shifted, max_transport_score=0.5,
)
# Benchmark-only oracle consequence weights make the deliberately shifted feature costly.
# They are not supplied to the product and therefore do not leak into the allocation.
actual = {"critical": 0.08, "secondary": 0.048, "nuisance": 0.80}
result = {
    "model_version": "V2P008_TGCARS_DEV_V1",
    "mechanism_removing_comparator": "P135 certificate reuse without transport gate",
    "blind_p135": blind.to_dict(),
    "guarded": guarded.to_dict(),
    "benchmark_only_oracle_weights": actual,
    "blind_oracle_loss": actual_loss(blind.allocation, actual),
    "guarded_oracle_loss": actual_loss(guarded.allocation, actual),
}
result["oracle_loss_reduction_fraction"] = 1.0 - result["guarded_oracle_loss"] / result["blind_oracle_loss"]
Path(__file__).with_name("BENCHMARK_RESULT.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
