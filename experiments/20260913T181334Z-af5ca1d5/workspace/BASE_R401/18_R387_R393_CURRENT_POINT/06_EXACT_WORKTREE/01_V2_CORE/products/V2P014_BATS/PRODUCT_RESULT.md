# V2P014_BATS — Boundary-Aware Timing Sensor

Composition: `FOUNDRY:P079 -> LCB-K012`.

Mechanism: CBIA boundary evidence gates policy-aware timing acquisition. Timing probes are scheduled only when the calibrated interval spans multiple downstream actions; action-invariant regions conserve sensing budget.

Mechanism-removing comparator: downstream consumer without the upstream gate/audit/tipping signal.

Claim boundary: deterministic synthetic executable contract only.
