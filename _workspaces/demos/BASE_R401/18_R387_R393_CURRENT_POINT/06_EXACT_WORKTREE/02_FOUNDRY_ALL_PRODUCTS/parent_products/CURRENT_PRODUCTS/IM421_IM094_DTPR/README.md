# Decision-Targeted Private Release

This is the first working product built from the composition **IM-421 → IM-094**.

## What it does

A normal private dashboard may divide a fixed privacy budget over many descriptive outputs. The
actual operational decision then receives only a small part of the budget and can become needlessly
noisy. DTPR starts from the declared action instead:

`private records → bounded-sensitivity score → calibrated noise → action boundary → released action`

If several decisions share one privacy budget, DTPR allocates epsilon according to the operational
consequence weight and global sensitivity of each score. For Laplace releases it minimizes the local
proxy

`Σ consequence_weight × 2 × (sensitivity / epsilon)²`

under the sequential-composition constraint `Σ epsilon ≤ total epsilon`. The resulting allocation is

`epsilon_i ∝ (consequence_weight_i × sensitivity_i²)^(1/3)`.

Items with zero operational consequence receive no release. This is the direct product meaning of
“spend limited information capacity only on distinctions capable of changing the decision.”

## Formal privacy shell

For a score with global sensitivity `Δ`, DTPR samples

`private_score = score(D) + Laplace(Δ / epsilon)`.

The action, rule fingerprint, and coarse stability band are deterministic post-processing of that
private score. Releasing them therefore retains the same epsilon-DP guarantee. Multiple releases
compose through the engine's epsilon ledger.

The guarantee is valid only if:

- the declared sensitivity is correct for the chosen neighboring-dataset definition;
- decision rules and consequence weights are public or their private selection is separately
  accounted for;
- every repeated release goes through the same composition ledger;
- upstream data preparation does not publish additional unaccounted private information.

## Run

From this directory:

```powershell
python -m unittest -v test_dtpr.py
python demo_emergency_allocation.py
python demo_multisite_allocation.py
python dtpr_cli.py --policy example_policy.json --input example_records.csv --ledger privacy_ledger.jsonl
```

The demo compares a 12-statistic uniformly budgeted dashboard with a decision-targeted release under
the same total epsilon. It writes reproducible results to `evaluation_results.json`. The CLI reads a
local CSV, derives sensitivity from supported bounded query types, releases only actions, and appends
each release to a hash-chained lifetime privacy ledger. Omit `--seed` outside tests so noise comes from
the operating system's cryptographic random source.

The multi-site demo uses the exponential mechanism to select two service sites without publishing
any site count. Two sequential selections divide the declared total epsilon and return only the
resource-allocation actions.

## Product status

This is a functional reference engine, not yet a production privacy platform. The local ledger is
tamper-evident but not remotely signed. A production build still needs authenticated policy approval,
concurrent ledger locking, secure deployment boundaries, and independent sensitivity review.
