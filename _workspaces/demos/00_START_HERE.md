# LabAllCompass Product-Code Reproduction Package — R210

This is the code-bearing companion to the R193–R208 academic report and the
current R210 research checkpoint. It is designed to survive chat/context loss:
the package contains the executable product base, current research code,
frozen results, tests, report sources and integrity metadata in one ZIP.

## What is included

- `BASE_R401/18_R387_R393_CURRENT_POINT/`: the exact executable worktree and
  product authority preserved at the R392/R393 boundary.
- `BASE_R401/19_R394_R398_FINAL_RETIREMENT_DELTA/` and
  `BASE_R401/20_SURVIVING_POST_R393_SURFACED_FILES/`: later recovered/reference
  product code with its original evidence boundaries.
- `BASE_R401/22_R399_R401_CURRENT_DELTA/`: R399–R401 replay evidence and the
  two runnable R401 material products.
- `ACTIVE_RESEARCH/`: every clean active theory round from R193 through R210,
  including code, tests, theory notes, decision files and frozen result JSON.
- `ACTIVE_PRODUCTS/`: the Lab crypto carry/algotrader product and Basin
  Authority Teacher product, including their frozen data/results and tests.
- `REPORT/`: Markdown, DOCX and PDF forms of the academic report plus the two
  report builders.
- `R202_CONTEXT/`: the root/transformation report, standalone methodology,
  claim ledger and continuation context from the R202 freeze. Large duplicate
  worktrees and lineage anchors are not repeated here.
- `CONTRACT/AGENTS.md`: the repository research contract active at packaging.

## Explicitly not included

- Bridge, Regime Router and the retired custom Lab skill/control plane.
- The discarded R179–R192 branch and `POST_R178_SALVAGE_ARCHIVE`.
- The R401 historical source archive, case-library duplicates and older
  duplicate current-point tree. The authoritative executable/product layers
  are included; this is a reproduction package, not another full history ZIP.
- Virtual environments and regenerable caches from post-R401 additions.

## Fast start

Windows has path-length limits in some Python import paths. The ZIP therefore
uses the short internal root `LAC_REPRO_R210`; extract it to a reasonably short
location such as `C:\lac_r210`.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-reproduction.txt
python verify_package.py
python run_reproduction.py --profile active
```

The `active` profile verifies the package and runs 112 tests: 98 tests across
R193–R210 plus the two current products, and 14 tests for the R401 material
products. It uses only frozen/local inputs and sends no exchange orders.

For the larger embedded R392 product regression:

```powershell
python run_reproduction.py --profile full
```

`04_FILE_MANIFEST_SHA256.tsv` covers every packaged file except the manifest
itself. The ZIP also has a sibling `.sha256.txt` file for transport checking.

## Authority boundary

Passing tests establish code integrity and reproduction on the tested frozen
surfaces. They do not establish financial profitability, deployment safety,
scientific novelty, or empirical validity beyond the recorded experiments.
The R394–R398 files retain the recovery/byte-identity limitations documented in
the R401 handoff; this package does not silently upgrade their status.
