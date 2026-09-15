# P144 DPAI — Dynamic Persistence Acquisition Interface

Parents: DFDPE -> AICC.

DFDPE's derivative-free persistence estimate and standard error become a one-dimensional Gaussian belief around the stability action boundary. AICC acquires an additional identification experiment only when expected action improvement exceeds cost.

Benchmark: noisy/short identification gives persistence 0.02027 with SE 0.08260; the declared experiment has net VOI +0.03414 and is selected. A well-identified stable case gives -0.49676 with SE 0.00810; the same experiment has net -0.005 and is skipped.

Claim boundary: the identification experiment's measurement-noise variance is declared; DPAI does not infer experiment sensitivity from DFDPE.

Status: WORKING_COMPOSITION; 6/6 tests.
