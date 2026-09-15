import json
from pathlib import Path
from idasro import identification_admissible_shift_robust_decision

r=identification_admissible_shift_robust_decision(
    -0.2,0.03,horizon=8,disturbance_bound=0.22,decision_gap=1.0,
    mean_vector_at_estimate=[0.12,0.50],mean_sensitivity_to_persistence=[3.0,0.0],z_score=1.96,
    sensitivity_shell_certified=True,sensitivity_provenance="DECLARED_SYNTHETIC_AFFINE_MAP_V1",
)
control=identification_admissible_shift_robust_decision(
    -0.2,0.03,horizon=8,disturbance_bound=0.22,decision_gap=1.0,
    mean_vector_at_estimate=[0.12,0.50],mean_sensitivity_to_persistence=[0.0,0.0],z_score=1.96,
    sensitivity_shell_certified=True,sensitivity_provenance="DECLARED_SYNTHETIC_ZERO_MAP_CONTROL",
)
out={
 "model_version":"V2P006_IDASRO_DEV_V1",
 "claim_scope":"deterministic declared-affine development shell only; no real-system sensitivity or uncertainty-set calibration claim",
 "near_boundary_identification_envelope":r.identification_envelope.to_dict(),
 "declared_affine_shift_decision":r.decision.to_dict(),
 "zero_sensitivity_control":control.decision.to_dict(),
}
Path(__file__).with_name('BENCHMARK_RESULT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2,sort_keys=True))
