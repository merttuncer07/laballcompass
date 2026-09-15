# Value-first benchmark batch 8

## RX-085 — UniversalityTransferGate
The gate is scientifically valid: 98.7% of closure-mismatched targets rejected, only 0.5% of
matched targets falsely rejected. Yet overall forecast RMSE improves only ~3.8% because a short
local fallback is cheap. Keep as transfer-validation diagnostic, not a major product.

## RX-086 — ScaleAwareModelGate
Scale crossover is detected often (68.1% switch rate) with 5% false switches in a true single-AR
control. Overall forecast RMSE improves only ~2.2%. Keep as a warning/diagnostic component.

## RX-087 — ActiveSetMap
Strong survivor. Active-set accuracy 98.4%. Piecewise-affine map RMSE .00224 vs histogram gradient
boosting .03874 (-94.2%); near regime boundaries .00532 vs .03783 (-85.9%). Promote.

## RX-089 — TimescaleBottleneckDetector
r02 removes oracle parameter access. With the same 30-job information budget, direct completion
pilot bottleneck accuracy is 84.5%; process/residence timescale estimator 90.2%. Throughput MAE
5.82 -> 3.31 (-43.1%). Promote.

## RX-093 — CouplingDistanceExplainer
All sources have identical 85% scalar accuracy. TV/coupling AUC .992 for downstream substitution
risk; JS .985 and Frobenius .994 are similarly strong. Keep the coupling interpretation as an
understandable minimum-disagreement / source-substitution audit, but do not claim a uniquely better
distance algorithm.
