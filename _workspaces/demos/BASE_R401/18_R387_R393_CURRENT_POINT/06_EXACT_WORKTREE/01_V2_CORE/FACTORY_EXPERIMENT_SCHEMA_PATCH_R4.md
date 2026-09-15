# Factory schema patch — R4 experiment routing

Every candidate that may enter adaptive experiment routing must expose:

## Candidate decision state

- `decision_id`
- `uncertainty_axes[]`
  - `axis_id`
  - `uncertainty`
  - `decision_leverage`
  - `importance`
- `search_generation`
- `selection_round`
- optional `stop_unresolved_mass`
- optional `compute_ceiling_seconds`

## Candidate test channels

- `test_channels[].test_id`
- `test_channels[].expected_resolution_by_axis`
- `test_channels[].compute_seconds`
- `test_channels[].reliability`
- `test_channels[].calibration_id`
- `test_channels[].evidence_role`
- `test_channels[].selection_generation`
- `test_channels[].measurement_backreaction`
- `test_channels[].backreaction_adjusted`

The current Foundry queue builder emits the top-level experiment fields on every row but leaves them `null` and marks the row `NOT_READY_MISSING_DECLARED_CONTRACT`. This is deliberate: queue prose and composition scores are insufficient to manufacture a calibrated experiment contract.

## Current readiness

At R4 freeze the 1,000-row composition queue has **0 experiment-routing-ready rows**. See `generated_search/EXPERIMENT_READINESS_AUDIT_R4.json` for the machine-readable gap audit.
