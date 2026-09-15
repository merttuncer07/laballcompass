# LabAllCompass R4 — Experiment selection contract

## Purpose

R4 closes the next reflexive loop after search and composition:

`SEARCH -> COMPOSE -> DECLARE UNRESOLVED DECISION -> ROUTE NEXT DISCRIMINATING TEST -> OBSERVE -> UPDATE NEXT ROUND`

The selector is not allowed to infer test value from prose. It routes only from a declared experiment contract.

## Primitive

For each unresolved decision axis `i`, the contract declares:

- current uncertainty `u_i` in `[0,1]`;
- decision leverage `d_i` in `[0,1]` — how strongly resolving this axis can affect the actual research decision;
- optional non-negative importance weight `w_i`.

The unresolved decision mass is:

`sum_i u_i * d_i * w_i`

For each candidate test `t`, the contract declares:

- expected fractional resolution `r_ti` for every axis it can resolve;
- reliability `q_t`;
- measured/estimated compute time `c_t`;
- `calibration_id` identifying where the resolution/reliability estimate came from;
- evidence role;
- search generation;
- whether measurement backreaction exists and, if so, whether the calibration already accounts for it.

The routing proxy is:

`expected decision progress(t) = sum_i (u_i * d_i * w_i * r_ti * q_t)`

`routing score(t) = expected decision progress(t) / c_t`

This is a transparent routing proxy, not a claim of Shannon information gain and not a scientific evidence score.

## Unknown policy

`UNKNOWN` stays unknown.

A test is not numerically ranked if any required quantity is absent, including:

- compute time;
- reliability;
- expected resolution for a declared covered axis;
- calibration provenance;
- backreaction state;
- backreaction adjustment when backreaction is known to exist.

There are no favorable defaults.

## Protected validation

`PROTECTED_VALIDATION` is never eligible for adaptive next-test routing and a protected-validation outcome cannot update the adaptive experiment program. The final untouched surface remains an audit surface rather than a tuning signal.

## Frozen rounds

Each plan carries a fingerprint of the exact decision axes and candidate-test contracts used to select it. An outcome can update only a later selection round. It cannot mutate or reinterpret the frozen plan that selected the test.

## Blind directions

The selector reports every unresolved axis that no eligible test covers. A high-ranked test list with a blind decision direction is therefore visible as incomplete rather than being mistaken for a complete experimental program.

## Stop behavior

The selector stops when:

1. unresolved decision mass is below the declared stop threshold; or
2. no quantified eligible test can reduce the declared uncertainty.

Case (2) is a telemetry/test-design failure, not evidence that the candidate is resolved.

## Non-claims

- Expected resolution values are not inferred from mechanism descriptions.
- Synthetic replay values are constructed mechanics tests, not empirical Lab calibrations.
- Lower compute does not prove higher scientific value unless the declared decision contract is appropriate.
- Search relevance, experiment routing, scientific evidence, and product promotion remain separate surfaces.
