# P141 PCFT — Predictive Closure-Fidelity Tipping

Parents: PSCT -> TDSX.

PSCT merge tolerance is scanned through a joint validity margin: closure violation must remain below a declared ceiling and predictive log-loss improvement must remain above a declared floor. This prevents the degenerate `merge everything into one state` solution from appearing safe merely because one-state closure is trivial.

Benchmark: baseline tolerance 0.05 has four predictive states and joint margin +0.07254. The nearest flip is tolerance 0.10, where closure violation jumps to 0.2575 and joint margin becomes -0.1575. Aggressive merges at 0.5/1.0 also fail the fidelity component.

Status: WORKING_COMPOSITION; 6/6 tests.
