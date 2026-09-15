# Reproducibility and independent verification

## Included

- `WORKTREE/TURING_ALLCOMPASS_MACHINE/BASE_R178_CUTOFF.zip`: active pre-delta
  Turing root.
- `WORKTREE/TURING_ALLCOMPASS_MACHINE/NEW_WORK/R179_*` through `R202_*`: source,
  unit tests, benchmark scripts, result JSON and local READMEs.
- `WORKTREE/foundry_completion/products/P147_EBG` and `P148_AES`: R180's actual
  executable dependencies, kept at their original relative paths.
- `WORKTREE/AGENTS.md` and entry documents: repository contract at freeze time.
- `LINEAGE_ANCHORS/LABALLCOMPASS_R401_MATERIAL_PRODUCT_HANDOFF_2026-08-31.zip`:
  byte-identical sealed prior archive-of-record. It preserves older lineage but
  is not loaded by the active R179–R202 runner.
- `07_MANIFEST_SHA256.tsv`: byte-level file inventory.
- `08_VERIFY_FREEZE.py`: standard-library integrity verifier.
- `10_RUN_SCIENCE_TESTS.py`: all included `test_*.py` suites, one round at a time.
- `11_SCIENCE_TEST_RECEIPT.json`: freeze-machine test receipt.

## Environment

The active research code uses Python and NumPy. Tested freeze runtime:

```text
Python executable:
C:\Users\mertt\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
Required third-party package: numpy
```

No large virtual environment is embedded.

## Integrity

From the extracted package root:

```powershell
python 08_VERIFY_FREEZE.py
```

The verifier hashes every manifest entry. `07_MANIFEST_SHA256.tsv` excludes
itself so that the inventory has no recursive hash dependency.

The outer ZIP has a separate sibling `.sha256.txt` file. Verify that before
extraction if possible.

## Scientific tests

```powershell
python 10_RUN_SCIENCE_TESTS.py
```

The runner discovers `test_*.py` in each included R179–R202 directory. R181 and
R190 are scout/portfolio rounds without unit tests; their source/result artefacts
remain included. Benchmarks are **not** all rerun automatically because some are
deliberately expensive (R189 is itself a cost-negative result). Full stored
benchmark outputs remain under their round folders.

## Independent audit recipe

1. Verify outer ZIP SHA-256.
2. Extract to a short, fresh directory.
3. Verify the internal manifest.
4. Optionally verify the embedded R401 anchor against its adjacent SHA-256 file.
5. Create a clean Python environment and install only NumPy.
6. Run all unit tests.
7. Select one positive and one negative round; rerun their benchmark scripts.
8. Check that README claims equal the result JSON summaries.
9. For a strong survivor, independently add one new seed and one shift rather
   than only replaying stored cases.
10. Never use the README claim as the oracle; use source code, result records and
   the direct baseline implementation.

## Expected non-identical quantities

Wall-clock timings vary by CPU, OS and BLAS. Exact algebraic agreement, pass/fail
counts, deterministic seeded metrics and classification direction should remain.
If only timing changes, report hardware/runtime. If predictions or statuses
change, treat it as a scientific discrepancy.
