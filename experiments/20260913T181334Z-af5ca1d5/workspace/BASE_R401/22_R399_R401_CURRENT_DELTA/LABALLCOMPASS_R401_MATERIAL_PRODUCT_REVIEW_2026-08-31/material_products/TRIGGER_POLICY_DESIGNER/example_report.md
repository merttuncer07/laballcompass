# Trigger policy: Machine intervention trigger

Selected signal: **temperature_c**  
Policy: trigger when value is **>= 76.000**  
Evaluation cost per row: **0.200**  
Improvement versus best always/never baseline: **80.000%**

## Holdout performance

| Rows | Events | Triggers | FN rate | FP rate | Precision | Recall |
|---:|---:|---:|---:|---:|---:|---:|
| 10 | 5 | 5 | 0.000 | 0.000 | 1.000 | 1.000 |

## Candidate comparison

| Signal | Direction | Threshold | Calibration cost/row | Evaluation cost/row |
|---|:---:|---:|---:|---:|
| temperature_c | high | 76.000 | 0.170 | 0.200 |
| vibration_rms | high | 5.500 | 0.300 | 1.500 |
| operator_health_score | low | 61.000 | 0.480 | 1.680 |

## Boundary

The threshold is calibrated on earlier rows and evaluated on later rows. This does not establish future stability or causal value.
