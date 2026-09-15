# Value-first benchmark batch 20

## RX-023 — ForecastQualityPartialOrder
Fails distinct product test. A strong scalar/proper-score style selection rule and the partial-order
gate both have median downstream regret 0 and choose an oracle-cost forecast in 67.2% of cases.
Keep multidimensional forecast QA semantics, but no separate product core.

## RX-106 — CodedBottleneckRouter
With complementary receiver side information and one packet-equivalent bottleneck slot, uncoded
routing completes median .8177 receivers/slot while an XOR/linear mixture completes 1.6353: exactly
2.0x. With no side information the coded mixture completes 0 while routing remains .8177.
Promote despite established network-coding prior art.

## RX-121 — DecisionWeightedCalibration
Equal 600-sample calibration budget. Raw-MSE-optimal allocation produces 14.39% downstream decision
error; consequence-weighted allocation 11.11% (-22.8%), even though its raw local bias MSE is worse.
Equal-consequence control nearly collapses. Promote.

## RX-161 — IrreversibleExplorationBudget
Normal opportunity shell: classic H/e exploration selects 35.1% of the realized oracle maximum on
average, while a distribution-aware continuation threshold selects 77.6% (+42.4 percentage points).
Pareto heavy-tail control reverses: fixed record policy 54.1%, adaptive Gaussian policy 40.6%.
Promote only with distribution-shell gate/fallback.

## RX-183 — TestingWealthController
Across 1,000 online hypotheses with bursty signals, fixed alpha spending yields 20.16 true
discoveries vs 74.08 for a finite-horizon LORD-like wealth controller (+267.4%). Mean FDP is 2.28%.
Under the global null, probability of any false discovery is 4.17% for wealth vs 4.92% for fixed
spending. Promote.
