# Inspection plan: Plant weekly inspection allocation

Budget: **18.000**  
Allocated cost: **17.600**  
Decision-weighted loss: **1,159.700**

## Selected inspection modes

| Target | Mode | Cost | Decision loss | Loss share |
|---|---:|---:|---:|---:|
| high_pressure_pump | full_diagnostic | 7.000 | 63.700 | 5.5% |
| boiler_feed_valve | balanced_review | 3.600 | 416.000 | 35.9% |
| refrigeration_compressor | balanced_review | 3.000 | 364.000 | 31.4% |
| warehouse_fan | quick_screen | 1.000 | 52.000 | 4.5% |
| backup_generator | balanced_review | 3.000 | 264.000 | 22.8% |

## What the allocation buys

- Loss reduction versus the minimum-cost plan: **73.517%**.
- Loss reduction versus the best affordable one-mode-for-everything policy: **26.601%**.
- The next strictly better plan needs **1.600** more budget and reduces current loss by **7.365%**.

## Budget curve

| Budget | Feasible | Used | Decision loss |
|---:|:---:|---:|---:|
| 8.000 | yes | 7.600 | 3,155.000 |
| 12.000 | yes | 11.600 | 1,850.000 |
| 15.000 | yes | 13.600 | 1,616.000 |
| 18.000 | yes | 17.600 | 1,159.700 |
| 22.000 | yes | 21.600 | 840.290 |
| 27.000 | yes | 26.400 | 475.250 |

## Declared consequence stresses

| Stress | Allocation stable | Changed targets | Loss |
|---|:---:|---:|---:|
| backup generator becomes mission critical | no | 2 | 1,432.850 |
| warehouse ventilation outage matters more | yes | 0 | 1,367.700 |

## Boundary

This plan is only as good as the supplied costs, errors and consequence weights. Validate those estimates with field data before operational deployment.
