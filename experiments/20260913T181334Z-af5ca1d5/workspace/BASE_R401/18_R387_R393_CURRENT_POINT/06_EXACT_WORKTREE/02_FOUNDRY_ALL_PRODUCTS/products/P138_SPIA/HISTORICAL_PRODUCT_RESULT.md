# P138 SPIA — Search-Policy Information Acquisition

Parents: ISPO -> AICC.

For each fixed ISPO policy, one-hot target distributions recover the complete location-specific detection-time vector. Expected detection time is therefore linear in the target-location probability vector and can be used directly as AICC action utility.

Benchmark: local and intermittent policies tie at the near-boundary belief. A hotspot-contrast measurement has expected decision improvement 0.10183, cost 0.02, net +0.08183, so it is acquired. Under a far-from-boundary belief the same channel has net value about -0.02 and is skipped.

Safety contract: covariance and channels must lie in the probability-simplex tangent space; arbitrary Gaussian probability drift is rejected.

Status: WORKING_COMPOSITION; 6/6 tests.
