# RX-201 prior-art note

Targeted search, 2026-08-25.

Known occupied components:
- Donoho/Jin higher criticism: rare/weak sparse-signal detection.
- Hall/Jin innovated higher criticism: correlated-noise extension.
- Lee/Li/Junge/Bresler and later short-and-sparse blind-deconvolution work: joint recovery under structural constraints.
- Labat/Idier, *Sparse Blind Deconvolution Accounting for Time-Shift Ambiguity* (ICASSP 2006, DOI 10.1109/ICASSP.2006.1660729): explicit scale/time-shift ambiguity and alignment issue.

Targeted searches did not find a direct method whose declared role is:
`post-fit candidate blind-deconvolution layer -> structural residual -> empirical-null HC/max/energy competition -> layer-mismatch rejection`, with symmetry-orbit quotient as a hard gate.

This absence is not an exhaustive novelty or patent search. The product score remains provisional 4/5 and no broad claim that higher criticism is a new blind-deconvolution solver is permitted.
