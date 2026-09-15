# P046 DTRC v0.1 — Decision-Targeted Reporting Contract

## Composition
SRCD → DLEW. SRCD creates truthful contracts for declared statistical targets; DLEW selects among valid contracts by the downstream capacity decisions their reports induce.

## Benchmark result
With shortage cost 4 and excess cost 1, the critical fractile is **0.8**. The truthful **q80** contract is selected by decision regret, while **mean** is selected by prediction RMSE. On untouched validation data q80 regret is **35.6071** versus **37.3856** for mean, despite mean having lower prediction RMSE (**54.9297** vs **57.4415**). Contracts whose payment clipping destroys strict incentives are rejected before decision evaluation.

Promotion state: **WORKING_COMPOSITION / DECISION-TARGETED INCENTIVE BENCHMARK**.
