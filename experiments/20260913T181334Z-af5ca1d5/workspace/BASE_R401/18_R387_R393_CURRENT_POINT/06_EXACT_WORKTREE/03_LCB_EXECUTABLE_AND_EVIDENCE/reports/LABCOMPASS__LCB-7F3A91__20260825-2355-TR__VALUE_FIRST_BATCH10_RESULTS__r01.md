# Value-first benchmark batch 10

## RX-075 — BurdenReliefController
Fair r02 gives both policies 82 production +18 reserve. Converting reserve into active purge when
burden accumulates raises throughput 41.78 -> 56.72 (+35.7%) and reduces mean burden 73.45 -> 46.06
(-37.3%). Fast-natural-relief control is exactly equal. Promote.

## RX-018 — VerificationStateLiquidity
Item-level verification state lowers deployable-liquidity RMSE 36.62 -> 31.83 (~13.1%), but
shortfall baseline AUC is already ~.9995 and homogeneous verification collapses the difference.
Useful extension of LiquidityStateEngine, not a new core.

## RX-026 — SelectionVsWithinAttribution
With true within-unit trend zero, selective exit creates an aggregate survivor trend +.0339 while
fixed-effects within trend is -.0021. With true +.06 improvement plus selection, aggregate shows
+.0844 and within gives +.0584. No-selection control agrees exactly. Promote.

## RX-066 — SafeProblemReducer
Optimized adjacency/queue r02 preserves the exact objective (<8.6e-14 disagreement), fixes a median
85.6% of variables, and reduces full MILP .0190s -> total kernelized .00321s (~5.89x).
Few-safe-reduction control gives only 1.17x. Promote.

## RX-032 — ArrivalFrontierEngine
Under heterogeneous starts/speeds/barriers: Euclidean owner accuracy 51.1%, speed-aware 58.8%,
full arrival-time frontier 100%. Homogeneous control collapses to nearest geometry. Promote.
