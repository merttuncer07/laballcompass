# R-020 product result — SCCRT v0.1

**Product route:** reconstructed standalone catalyst-state and regeneration-capacity tracker  
**Result:** working product; 4/4 tests pass

SCCRT treats lattice species as finite state carried through reaction and regeneration steps. Its
designer selects the smallest declared oxidant scale satisfying minimum and terminal activity.

In the first eight-cycle construction, oxidant scale 4.0 was the minimum feasible option. Active
fraction stayed above 0.47234 and ended at 0.95351; 387.39390 capacity units were consumed and
382.74512 restored, closing material balance within 7.25×10⁻¹³. A passive-catalyst model
overpredicted product by 44.56%.

The product supports redox catalyst feed scheduling, regeneration sizing, and state monitoring.
