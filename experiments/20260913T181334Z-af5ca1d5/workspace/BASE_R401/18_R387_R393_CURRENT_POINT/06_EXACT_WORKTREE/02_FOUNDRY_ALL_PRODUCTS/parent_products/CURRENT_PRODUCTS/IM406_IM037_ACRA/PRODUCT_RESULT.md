# IM-406 → IM-037 product result: Adaptive Consequence-Resolution Allocator v0.1

ACRA allocates time/frequency resolution according to marginal decision consequence rather than
using one fixed measurement window everywhere.

## Construction result

Six decision regions shared a measurement budget. A fixed balanced setting cost 24 and produced
decision-weighted error 1,337.5. At the same available budget, ACRA selected:

- short-time resolution for emergency onset;
- long-frequency resolution for resonance;
- balanced resolution for regime change and mixed control;
- fine time-and-frequency resolution for high-consequence machine vibration;
- coarse resolution for low-consequence monitoring.

The adaptive portfolio cost 23 and reduced total decision-weighted error to 928.0, an improvement of
**30.62%**.

## Working software

- region-specific time, frequency, and consequence weights;
- resolution-option cost/error definitions;
- shared-budget mixed-integer allocation;
- transparent fixed-resolution comparison;
- three automated tests, all passing.

## Next construction layer

Derive time/frequency errors from real windows and sampled signals rather than supplied option
tables, then update allocations online when action gaps and operational consequences move.
