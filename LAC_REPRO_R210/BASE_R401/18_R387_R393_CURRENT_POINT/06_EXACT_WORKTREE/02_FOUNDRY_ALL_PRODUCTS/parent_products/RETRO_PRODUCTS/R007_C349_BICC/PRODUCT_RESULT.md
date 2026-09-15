# Product Result — BICC v0.1

**Retro candidate:** R-007 / C-349 / M-621 + M-622  
**Historical decision:** variant of IM-318  
**Product:** Bounded-Influence Concentration Certificate  
**Status:** independent working product

BICC replaces one input coordinate at a time and measures how a scalar black-box result responds.
It produces per-input influence diagnostics, an Efron–Stein variance proxy, and—when the user supplies
global sensitivity limits—an assumption-conditional McDiarmid concentration radius.

In the first 30-input construction, two systems had the same total weight and input ranges:

- evenly distributed influence had **30.0 effective coordinates**;
- 75% concentration on one input reduced this to **1.008 effective coordinates**;
- the concentrated system's observed output variance was **16.88×** larger;
- its 95% McDiarmid radius was **4.12×** larger;
- deliberately false supplied bounds were detected and marked as observed violations.

Four tests pass. BICC never treats a sampled maximum as proof of a global bound: without supplied
bounds it remains an empirical audit. It is a standalone model/KPI reliability product and does not
require integration with the current composition products.

v0.1 assumes independently replaceable coordinates and scalar outputs. The next standalone layer is
group replacement, dependent-input conditional resampling, vector outputs, and streaming drift.
