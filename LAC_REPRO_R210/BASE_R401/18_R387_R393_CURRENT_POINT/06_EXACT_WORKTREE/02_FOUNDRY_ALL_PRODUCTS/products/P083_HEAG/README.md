# HEAG: historical evidence and the next measurement

The current implementation calls canonical EBC and AICC code. The previous generic score allocator and its tests are preserved under `restoration/20260914-heag/before/` in the lab root. This is a **new native implementation**, not recovery of the missing historical code. `HISTORICAL_PRODUCT_RESULT.md` is unchanged and its old 6-test result is not evidence about this implementation.

Run from the lab root:

```sh
.venv/bin/python lab.py evidence-acquisition examples/evidence-acquisition/verified/declared_copies-input.json --review
```

`evaluate(config)` takes two mappings:

- `evidence`: current estimate, standard error, historical normal estimates and EBC policy parameters. Optional named joint covariance handles partial evidence dependence; observation IDs identify exact repeats.
- `decision`: named affine actions, one-dimensional slopes/intercepts, candidate channels with measurement vectors/noise variances/costs, and `future_error_relation: "independent_of_evidence"`.

The future-error declaration is necessary. A measurement copied from, or sharing errors with, used evidence requires a larger joint model. This adapter rejects a declared shared-error relation. Mutual dependence among unobserved future channels does not affect their individual marginal one-step value; this product selects just one next channel and does not optimize an acquisition sequence.

EBC's mean and squared reported SE define an explicit Gaussian working belief. Adaptive EBC weights are not proved to produce a calibrated posterior. AICC compares expected downstream improvement against cost in the same utility units. Output includes current-only acquisition, history-informed acquisition, per-channel value changes and actual parent source hashes. Content matches or REL candidate weights are not used as covariances.

`review_dependency(config)` runs the same observations, EBC policies, utilities and costs after removing only declared identity/cross-covariance. A different choice is a sensitivity result, not proof that an acquisition was useful in practice. Old score-only records, `baseline` and allocation `budget` arguments are rejected because they did not implement EBC + AICC.

Current validation: 13 meaningful product tests, including both-parent execution, 1/2/5/20-copy invariance, current-observation overlap, independent equal estimates, conflict suppression, cap ablation, covariance-to-acquisition propagation against direct GLS and closed form, cost/utility changes and invalid adapters. The example reproduction adds all 1–20 copy counts and a public clustered-estimate numerical reference. Neither tests nor historical claims establish real auditor benefit.
