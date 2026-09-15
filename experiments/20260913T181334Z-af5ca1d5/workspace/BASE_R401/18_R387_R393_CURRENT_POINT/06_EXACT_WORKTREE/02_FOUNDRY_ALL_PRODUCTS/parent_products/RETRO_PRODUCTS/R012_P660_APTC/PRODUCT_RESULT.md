# R-012 product result — APTC v0.1

**Product route:** reconstructed standalone coupled-charge transport calculator  
**Result:** working product; 4/4 tests pass

APTC reconstructs the internally generated electric field required to make electron and hole fluxes
move together. It validates quasineutrality and forecasts packet spreading with the resulting
ambipolar coefficient.

In the first neutral packet, uncoupled flux mismatch reached 17.4321. The restoring field reduced the
coupled mismatch to 3.55×10⁻¹⁵. Neutral-limit ambipolar diffusivity was 17.5946; over forecast time
0.05, packet variance grew from 1.00543 to 2.76489 (RMS width 1.66280).

The reconstructed product is usable for semiconductor, plasma, electrolyte, and carrier transport.
