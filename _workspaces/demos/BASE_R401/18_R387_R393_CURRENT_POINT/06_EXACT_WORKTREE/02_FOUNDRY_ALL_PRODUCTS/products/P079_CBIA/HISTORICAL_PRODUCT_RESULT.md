# Calibrated Boundary Information Acquisition

**Status:** PROMOTED v0.1

**Composition:** CWC + AICC

Uses a frozen calibrated uncertainty interval as an action-boundary gate. Information acquisition is considered only when the interval spans different downstream actions; AICC then prices the available channels.

## Benchmark

```json
{
  "near_boundary": {
    "calibrated_multiplier": 1.6081781955976822,
    "interval": [
      -0.14163563911953647,
      0.5016356391195365
    ],
    "lower_action": 0,
    "upper_action": 1,
    "boundary_crossed": true,
    "selected_channel": "measure",
    "status": "MEASUREMENT_CONSIDERED_AT_ACTION_BOUNDARY"
  },
  "far_from_boundary": {
    "calibrated_multiplier": 1.6081781955976822,
    "interval": [
      1.8391821804402317,
      2.1608178195597683
    ],
    "lower_action": 1,
    "upper_action": 1,
    "boundary_crossed": false,
    "selected_channel": null,
    "status": "CALIBRATED_INTERVAL_ACTION_INVARIANT_NO_MEASUREMENT"
  }
}
```

## Claim boundary

The interval is a calibration object, not a posterior probability of action change. Skipping acquisition is certified only relative to the declared action functions and calibrated interval shell.
