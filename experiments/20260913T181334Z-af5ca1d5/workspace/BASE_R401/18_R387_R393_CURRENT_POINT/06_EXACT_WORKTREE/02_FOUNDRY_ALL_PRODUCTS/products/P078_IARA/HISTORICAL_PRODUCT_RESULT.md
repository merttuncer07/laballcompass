# Influence-Aware Resolution Allocator

**Status:** PROMOTED v0.1

**Composition:** BICC + ACRA

Uses observed bounded-replacement impact of black-box inputs as ACRA consequence weights so scarce measurement resolution goes to inputs that materially move the protected output.

## Benchmark

```json
{
  "influences": [
    10.0,
    1.0,
    0.1
  ],
  "allocation": {
    "budget": 1,
    "total_cost": 1,
    "total_decision_loss": 2.4,
    "allocations": [
      {
        "region": "critical",
        "option": "fine",
        "cost": 1,
        "decision_loss": 0.20000000000000004
      },
      {
        "region": "medium",
        "option": "coarse",
        "cost": 0,
        "decision_loss": 2.0
      },
      {
        "region": "tiny",
        "option": "coarse",
        "cost": 0,
        "decision_loss": 0.2
      }
    ]
  },
  "consequence_mode": "maximum_observed",
  "status": "INFLUENCE_WEIGHTED_RESOLUTION_ALLOCATED"
}
```

## Claim boundary

Observed replacement influence is a consequence proxy, not proof of causal effect or adversarial realizability. Global concentration claims still require valid caller-supplied bounds; IARA uses the empirical influence audit for allocation.
