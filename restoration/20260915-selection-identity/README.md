# Selected model identity and complete test discovery

This repair continues the interrupted DREW/ACSA work. The separate Akbank portfolio
release is preserved in `/Users/mertalituncer/Developer/iz-audit` and in Downloads.
No Git commit or push was performed for this repair.

## Observed faults and changes

1. DLEW could select candidate `b` on a regret tie while ACSA audited `a`.
   The adapter now supplies realized payoffs from the identical decision paths;
   ACSA uses loss, payoff, then original column order for selection and paired
   row resamples. DREW explicitly enforces selected/audited identity and preserves
   ACSA's unstable status. The public loss-matrix API remains compatible.
2. NaN and infinite materiality thresholds could conceal a positive selected
   holdout regret. They now raise a finite/nonnegative validation error. This
   was observed again on actual fitted-model errors from the digits pilot.
3. `lab.py check` used unittest-only discovery for ACSA and MIFF. It collected
   four old tests for each and silently omitted module-level pytest regressions.
   Parent suites with module-level test functions now use pytest. Other parent
   unittest suites retain their existing runner. A failing mixed-suite test
   demonstrates that the new dispatcher cannot report only its passing half.

Canonical ACSA and its six embedded copies have identical bytes. Original
sources are retained in `before/`; the intermediate implementation is retained
as `acsa-before-finite-threshold.py`. The earlier tie regression is a small
mechanical test, not a real banking case or evidence of real-world efficacy.

## Executed evidence

- `runner-receipt.json` links the ordinary lab-run record: 85 tests, no failures
  or skips. Includes 17 ACSA, 24 MIFF and 44 consumer tests.
- `runner-tests-final.xml` / `.log`: 17 runner and component tests passed.
- `runner-before.json`: four tests per affected parent under the previous
  unittest-only discovery, with no loader errors to reveal the omission.
- `real-data-validation.json`: the unchanged, fixed-seed, 27-model digits pilot
  ran with scikit-learn 1.9.1. Selected and audited model: `knn_k3`; protected
  winner: `knn_k1`. Final errors: 8/360 and 6/360. Ordinary holdout argmin chooses
  the same protected winner; no unique DREW accuracy benefit is established.
- `digits-search-model-errors.csv` and `digits-holdout-model-errors.csv` contain
  the actual fitted models' error matrices, not a manufactured banking dataset.
- `changes.json`, `source.patch`, and `validation.json` identify changed bytes,
  working-package verification, and the exact scope of these observations.

The earlier `parent-tests.*`, `consumer-tests.*`, and `after-observations.json`
record the interrupted stage before the additional threshold and runner fixes.
They are historical evidence, not substituted for the fresh official run.

## Reproduce

From the lab root:

```sh
.venv/bin/python lab.py check R014
.venv/bin/python lab.py check R027
.venv/bin/python lab.py check P001
.venv/bin/python -m pytest -q tests/test_runner.py tests/test_components.py
.venv/bin/python -m pip install -r requirements-pilots.lock
.venv/bin/python restoration/20260915-selection-identity/run_real_data_validation.py
```

The real pilot uses the published handwritten-digit observations distributed by
[scikit-learn](https://scikit-learn.org/stable/modules/generated/sklearn.datasets.load_digits.html).
Its row split does not establish writer-group independence and is not banking
field validation. The bootstrap operates on supplied rows; it does not replay
sequential actions or automatically account for shared sources. The runner
change follows [pytest's support for unittest suites](https://docs.pytest.org/en/stable/how-to/unittest.html)
while retaining unittest for unaffected parent suites.

The wider lab goal remains unfinished. In particular, passing these tests does
not turn 89 generic replacements into recovered historical products, validate
all research claims, or prove a product's superiority to strong baselines.
