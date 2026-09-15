# P025 IDRE v0.1 — Identification-Driven Decision Robustness Envelope

## Composition

DFDPE derivative-free persistence identification -> DTRM finite-horizon decision envelope.

IDRE estimates the scalar affine persistence rate from noisy observations, maps it exactly into the same-input trajectory-error dynamics, and evaluates both the point estimate and `a + z*SE(a)`. Identification uncertainty can therefore revoke a decision certificate instead of disappearing between system identification and downstream robustness analysis.

## Benchmark

Fixed-seed near-boundary synthetic system:

- identified persistence: `-0.1922774468`, SE `0.0194925886`
- nominal DTRM flip-index bound: `0.9555531556` -> action certified
- conservative flip-index bound: `1.1071388123` -> action flip cannot be excluded
- status: `IDENTIFICATION_UNCERTAINTY_REVOKES_ACTION_CERTIFICATE`

A well-stable control system remained certified under the conservative identified dynamics (`0.4283446296` flip-index bound).

## Claim boundary

Synthetic scalar-affine mechanism benchmark. The mapping is valid only when the identified shell, shared-input error dynamics, declared disturbance bound, nominal gap, and horizon are appropriate. No real-system robustness claim is made.
