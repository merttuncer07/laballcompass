# Market-Clearing Fragility Surface

**Status:** PROMOTED v0.1

**Composition:** MCPR + TDSX

Maps the nearest declared demand stress at which a uniform-price market can no longer fully serve demand.

## Benchmark

```json
{
  "baseline_status": "CLEARED",
  "baseline_price": 20.0,
  "baseline_service_fraction": 1.0,
  "tipping_multiplier": 1.3,
  "surface": {
    "parameter_names": [
      "demand_multiplier"
    ],
    "grid_shape": [
      6
    ],
    "evaluated_points": 6,
    "baseline_parameters": {
      "demand_multiplier": 1.0
    },
    "baseline_metric": 1.0,
    "decision_threshold": 0.999999,
    "baseline_decision": true,
    "robust_surface_share": 0.6666666666666666,
    "tipping_point": {
      "parameters": {
        "demand_multiplier": 1.3
      },
      "metric": 0.9615384615384616,
      "normalized_euclidean_distance": 0.42857142857142866,
      "normalized_manhattan_distance": 0.42857142857142866
    },
    "one_way_tipping_values": {
      "demand_multiplier": 1.3
    },
    "metric_minimum": 0.8333333333333334,
    "metric_maximum": 1.0,
    "status": "TIPPING_POINT_FOUND"
  },
  "evaluations": [
    {
      "demand_multiplier": 0.8,
      "demand": 64.0,
      "served": 64.0,
      "unserved": 0.0,
      "service_fraction": 1.0,
      "clearing_price": 20.0,
      "status": "CLEARED"
    },
    {
      "demand_multiplier": 1.0,
      "demand": 80.0,
      "served": 80.0,
      "unserved": 0.0,
      "service_fraction": 1.0,
      "clearing_price": 20.0,
      "status": "CLEARED"
    },
    {
      "demand_multiplier": 1.1,
      "demand": 88.0,
      "served": 88.0,
      "unserved": 0.0,
      "service_fraction": 1.0,
      "clearing_price": 20.0,
      "status": "CLEARED"
    },
    {
      "demand_multiplier": 1.25,
      "demand": 100.0,
      "served": 100.0,
      "unserved": 0.0,
      "service_fraction": 1.0,
      "clearing_price": 20.0,
      "status": "CLEARED"
    },
    {
      "demand_multiplier": 1.3,
      "demand": 104.0,
      "served": 100.0,
      "unserved": 4.0,
      "service_fraction": 0.9615384615384616,
      "clearing_price": 100.0,
      "status": "SHORTAGE"
    },
    {
      "demand_multiplier": 1.5,
      "demand": 120.0,
      "served": 100.0,
      "unserved": 20.0,
      "service_fraction": 0.8333333333333334,
      "clearing_price": 100.0,
      "status": "SHORTAGE"
    }
  ]
}
```

## Claim boundary

The tipping point is conditional on the declared offer stack, fixed offer prices/quantities, scarcity-price rule, and finite demand grid. It is not a forecast of strategic bidding or endogenous supply entry.
