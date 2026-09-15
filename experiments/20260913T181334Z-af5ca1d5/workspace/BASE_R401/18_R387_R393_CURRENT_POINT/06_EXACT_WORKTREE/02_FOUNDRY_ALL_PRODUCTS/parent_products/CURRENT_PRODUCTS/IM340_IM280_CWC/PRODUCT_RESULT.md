# Product Result — CWC v0.1

**Composition:** IM-340 → IM-280  
**Product:** Calibration Width Controller  
**Status:** working reference product

CWC decomposes interval performance before feedback: only coverage error drives the bounded PI
width controller, while sharpness and total interval score remain explicit evaluation outputs. This
prevents miss magnitude, center quality, and width from entering one opaque control signal.

In a reproducible 2,400-step process with two unannounced variance shifts and a deliberately stale
base scale:

- CWC's three phase coverages were **90.125%, 89.5%, and 89.875%** against a 90% target;
- the raw instantaneous interval-score gradient produced **89.875%, 87.75%, and 92.75%**;
- CWC reduced rolling coverage RMSE by **13.75%** and width-step variability by **24.71%**;
- the tradeoff was real: CWC intervals were **5.30% wider** on average and their mean interval score
  was **4.93% worse** than the raw-score controller.

The product therefore does not claim dominance on every objective. It exposes an operational
choice: pay a measured sharpness cost for materially steadier coverage under shifts. Three unit
tests pass.

v0.1 controls symmetric scalar intervals. The live extension path is asymmetric tails,
conditional/group coverage, delayed labels, anti-windup, and action-cost-aware coverage targets.
