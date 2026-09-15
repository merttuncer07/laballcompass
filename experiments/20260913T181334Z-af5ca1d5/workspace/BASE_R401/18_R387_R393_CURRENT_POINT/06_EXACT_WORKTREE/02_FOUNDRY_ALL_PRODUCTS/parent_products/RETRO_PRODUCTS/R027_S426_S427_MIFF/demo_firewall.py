import json

from miff import InformationFlow, design_inference_firewall


flows = [
    InformationFlow("trusted_core", "suspect_calibration", gain=0.80, cut_cost=5.0, label="forward summary"),
    InformationFlow("suspect_calibration", "trusted_core", gain=0.90, cut_cost=1.0, label="feedback update"),
    InformationFlow("trusted_core", "decision", gain=0.70, cut_cost=8.0, label="decision feed"),
    InformationFlow("suspect_calibration", "monitor", gain=0.30, cut_cost=4.0, label="diagnostics"),
]
result = design_inference_firewall(
    ["trusted_core", "suspect_calibration", "monitor", "decision"],
    flows,
    suspect_sources=["suspect_calibration"],
    protected_targets=["trusted_core", "decision"],
)
print(json.dumps(result.to_dict(), indent=2))
