# Resilience-Aware Measurement Resolution

**Status:** PROMOTED v0.1

**Composition:** HMRM + ACRA

Turns mode exposure times recovery duration into consequence weights for a shared sensing-resolution budget, so slow consequence-bearing modes receive finer measurement first.

## Benchmark

```json
{
  "mode_scores": [
    114.0,
    3.0
  ],
  "mode_recovery_steps": [
    114,
    3
  ],
  "mode_exposures": [
    1.0,
    1.0
  ],
  "allocation": {
    "budget": 1,
    "total_cost": 1,
    "total_decision_loss": 8.280000000000001,
    "allocations": [
      {
        "region": "mode_0",
        "option": "fine",
        "cost": 1,
        "decision_loss": 2.2800000000000002
      },
      {
        "region": "mode_1",
        "option": "coarse",
        "cost": 0,
        "decision_loss": 6.0
      }
    ]
  },
  "status": "RECOVERY_WEIGHTED_RESOLUTION_ALLOCATED"
}
```

## Claim boundary

Exposure×recovery is a prioritization proxy, not an expected monetary loss. Mode identity and consequence projection remain conditional on the supplied transition and consequence model.
