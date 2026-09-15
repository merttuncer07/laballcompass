# R-016 product result — FCMS v0.1

**Product route:** reconstructed standalone compatible-microstructure synthesizer  
**Result:** working product; 4/4 tests pass

FCMS searches sequential laminate trees while enforcing rank-one compatibility at every mixing
node. It reports phase fractions, hierarchy, macro response, error, and the smallest implied layer
relative to a declared fabrication resolution.

In the first four-phase construction, a coarse zero-gradient target absent from the allowed phase set
was realized exactly by a depth-2 laminate. Every phase carried 25%, target error was zero, and the
smallest layer was 0.25—above the 0.20 fabrication limit. Raising the fabrication limit to 0.30
correctly preserved mathematical realizability while flagging present manufacturing insufficiency.

The reconstructed product is usable for laminate and microstructure architecture searches.
