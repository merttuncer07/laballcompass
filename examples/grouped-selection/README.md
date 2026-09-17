# Real repeated-source evaluation of ACSA

The same 1,529 protected records give very different uncertainty when their 11
actual source subjects are retained. The selected constant training-mean model
and every candidate's mean absolute error remain identical.

| Calculation | IID rows | Whole subjects |
| --- | ---: | ---: |
| Resampling units in protected sample | 1,529 rows | 11 subjects |
| Standard error | 0.11805 | 1.34253 |
| Bootstrap percentile interval | 8.4983–8.9797 | 6.2244–11.3787 |
| Bootstrap draws | 2,000 | 2,000 |

The cluster SE is **11.3725 times** the row SE on this fixed split. This is an
observed effect of a different sampling assumption, not proof that the interval
is calibrated. Neither method improves point prediction, and the constant model
winning over five fitted alternatives is retained as observed. No favorable seed
or model search was performed.

The original [UCI Parkinsons Telemonitoring dataset](https://archive.ics.uci.edu/dataset/189/parkinsons+telemonitoring)
contains 5,875 recordings from 42 people with explicit subject IDs. The published
motor UPDRS target is linearly interpolated. This experiment uses the 16 original
voice features and is a software mechanism check, not a medical recommendation,
banking audit example or proof of a new algorithm.

`PROTOCOL.md` was written before execution. `result.json` records the exact
subject split, models, environment, source hashes and both outcomes. Derived
`selection-losses.csv` and `holdout-losses.csv` retain original CSV line numbers
and subject IDs; the ZIP contains the unchanged public observations.

From the lab root, with `requirements-pilots.lock` installed:

```sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 .venv/bin/python examples/grouped-selection/run.py \
  --acsa-dir LAC_REPRO_R210/BASE_R401/18_R387_R393_CURRENT_POINT/06_EXACT_WORKTREE/02_FOUNDRY_ALL_PRODUCTS/parent_products/RETRO_PRODUCTS/R014_S781_S792_ACSA
```

The script writes results beside itself. It accepts only the original archive
hash, does not download automatically and has no simulated-data fallback.
ACSA's API accepts other measured case-by-candidate loss matrices and declared
source IDs; it does not infer those IDs or losses from ordinary documents.

Provenance: Tsanas, A. & Little, M. (2009), *Parkinsons Telemonitoring*, UCI,
DOI [10.24432/C5ZS3N](https://doi.org/10.24432/C5ZS3N), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
Download: [original ZIP](https://archive.ics.uci.edu/static/public/189/parkinsons+telemonitoring.zip).
The raw data are unchanged; loss CSVs are derived from the documented fitted models.

Only 11 protected subjects means limited precision. Independence between subjects
is an assumption, not established by the IDs. The calculation conditions on the
six fitted models, does not include retraining uncertainty and is not a familywise
test. Known-source grouping is useful here; it does not solve unknown overlap or
make six derivatives of one report into six independent evidence items.
