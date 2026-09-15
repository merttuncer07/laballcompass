# Product Result — TFLD v0.1

**Retro candidate:** R-021 / C-399 / M-896  
**Historical decision:** variant of IM-406  
**Product:** Time-Frequency Localization Designer  
**Status:** independent working product

TFLD measures candidate window energy moments and selects a time-frequency analyzer from explicit
joint localization requirements.

In the first design sweep:

- 18 window designs were evaluated and **5** met both declared limits;
- the selected 128-sample Gaussian window had time spread **0.01509 s**;
- frequency spread was **5.298 Hz** and uncertainty product **0.07995**;
- an impossible tighter request produced no fake solution;
- its closest 32-sample Hamming compromise exceeded time and frequency limits by **2.46×** and **3.45×**.

Four tests pass. TFLD is a standalone sensing and signal-analysis design product; current-product
integration is not required.

v0.1 designs fixed windows. The next standalone layer is adaptive/multiresolution windows, chirps,
leakage constraints, computational budgets, and application-specific detection loss.
