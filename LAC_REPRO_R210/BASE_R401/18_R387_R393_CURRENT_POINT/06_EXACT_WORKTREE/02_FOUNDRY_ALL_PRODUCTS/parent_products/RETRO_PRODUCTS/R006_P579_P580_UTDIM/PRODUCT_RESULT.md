# R-006 product result — UTDIM v0.1

**Product route:** reconstructed standalone unequal-transport instability monitor  
**Result:** working product; 4/4 tests pass

UTDIM reconstructs a vertical-velocity/two-scalar linear system and scans its eigenmodes. It reruns
the same gradients and couplings with equal diffusivities, isolating the causal contribution of
transport-rate mismatch.

In the first construction, the combined static stability index was +1, yet a 100× diffusivity ratio
created growth 0.64281 at wavenumber 1.84518 with e-folding time 1.55566. Under equal transport the
same mode decayed at −1.02991. The detected unstable band spanned approximately 0.0316–5.5145.

The reconstructed shell is ready for stratified fluids and other coupled transport systems.
