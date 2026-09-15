# Adaptive Hedge Selection Audit

**Status:** PROMOTED v0.1

**Composition:** DHCC + ACSA

Audits the ridge chosen by realized hedge loss on a selection segment against a separate protected segment, keeping the entire ridge family visible.

## Benchmark

```json
{
  "dhcc_selected_ridge": 1.0,
  "protected_best_ridge": 0.1,
  "selected_protected_regret": 0.1238277750840675,
  "acsa_status": "ADAPTIVE_SELECTION_REGRET_DETECTED",
  "audit": {
    "candidate_names": [
      "ridge=0",
      "ridge=0.001",
      "ridge=0.01",
      "ridge=0.1",
      "ridge=1",
      "ridge=10"
    ],
    "selected_candidate": "ridge=1",
    "holdout_best_candidate": "ridge=0.1",
    "selection_mean_losses": [
      0.9532558433702175,
      0.8778212606447668,
      0.6320372788022216,
      0.5249515557210755,
      0.5043800156561343,
      1.5247287307941109
    ],
    "holdout_mean_losses": [
      0.9321964159701455,
      0.8926684324255494,
      0.7659117423424279,
      0.7252429917730543,
      0.8490707668571218,
      2.373482888614493
    ],
    "candidate_generalization_gaps": [
      -0.02105942740007205,
      0.014847171780782542,
      0.13387446354020627,
      0.20029143605197874,
      0.34469075120098747,
      0.8487541578203823
    ],
    "selected_selection_loss": 0.5043800156561343,
    "selected_holdout_loss": 0.8490707668571218,
    "selected_generalization_gap": 0.34469075120098747,
    "selected_holdout_regret": 0.1238277750840675,
    "family_worst_absolute_gap": 0.8487541578203823,
    "pointwise_standard_error": 0.055907401086719294,
    "pointwise_95_radius": 0.10957850612996982,
    "selected_holdout_loss_bootstrap_interval_95": [
      0.7444342027237455,
      0.9713823806082662
    ],
    "selection_bootstrap_frequencies": [
      0.0,
      0.0,
      0.02,
      0.42,
      0.56,
      0.0
    ],
    "selection_fragility": 0.43999999999999995,
    "status": "ADAPTIVE_SELECTION_REGRET_DETECTED"
  },
  "status": "HEDGE_SELECTION_HOLDOUT_AUDITED"
}
```

## Claim boundary

AHSA diagnoses adaptive hedge-selection regret on the declared protected sample. It does not guarantee future market performance or model transaction costs beyond the supplied DHCC loss contract.
