# Decision-Loss-Aware Lumpability Guard

**Status:** PROMOTED v0.1

**Composition:** SALC + DSBC

Audits whether a dynamically lumpable Markov partition also preserves one common downstream action inside every aggregate state.

## Benchmark

```json
{
  "exact_lumpability": true,
  "salc_status": "EXACT_LUMPABILITY_CERTIFIED",
  "decision_safe": false,
  "unsafe_blocks": [
    "A"
  ],
  "blocks": [
    {
      "block": "A",
      "state_indices": [
        0,
        1
      ],
      "decision_safe": false,
      "compressed_state_count": 2,
      "maximum_regret": 0.0
    },
    {
      "block": "B",
      "state_indices": [
        2,
        3
      ],
      "decision_safe": true,
      "compressed_state_count": 1,
      "maximum_regret": 0.0
    }
  ],
  "status": "EXACT_BUT_DECISION_UNSAFE"
}
```

## Claim boundary

Exact strong lumpability is a transition-law certificate only. DLAG adds a declared utility matrix and regret tolerance; it does not claim a partition is decision-safe for unmodeled actions or utilities.
