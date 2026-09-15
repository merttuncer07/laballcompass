# Scope and provenance

## Source-to-package map

| Package path | Repository source | Status |
|---|---|---|
| `BASE_R401/18_R387_R393_CURRENT_POINT` | `LABALLCOMPASS_R401_MATERIAL_PRODUCT_HANDOFF_2026-08-31/18_R387_R393_CURRENT_POINT` | Exact embedded worktree and evidence through R392/R393 |
| `BASE_R401/19_R394_R398_FINAL_RETIREMENT_DELTA` | same-named R401 directory | Recovery/reference delta; retain its original caveats |
| `BASE_R401/20_SURVIVING_POST_R393_SURFACED_FILES` | same-named R401 directory | Surviving surfaced files |
| `BASE_R401/22_R399_R401_CURRENT_DELTA` | same-named R401 directory | R399–R401 state, replay evidence and material products |
| `ACTIVE_RESEARCH/R193_*` … `R210_*` | `TURING_ALLCOMPASS_MACHINE/NEW_WORK/` | Clean active post-R178 research line |
| `ACTIVE_PRODUCTS/LAB_CRYPTO_ALGOTRADER` | `PRODUCTS/LAB_CRYPTO_ALGOTRADER` | Current paper-first crypto product |
| `ACTIVE_PRODUCTS/basin_authority_teacher_v001` | `lab_products/basin_authority_teacher_v001` | Current research product |
| `REPORT/` | `LAB_REPORTS/R208_ACTIVE_THEORY_PORTFOLIO` and `output/pdf` | Report, renderings and builders |
| `R202_CONTEXT/` | selected direct files from `LABALLCOMPASS_R202_THEORY_REVISIT_FREEZE_2026-08-31` | Context only; duplicate payload omitted |

## Integrity provenance

Before this package was built, the complete source R401 handoff passed its own
extended-path verifier:

```text
R401 HANDOFF VERIFY: PASS
files=10397 bytes=895632396
base=R398 preserved; delta=R399+R400+R401; post-R401 crypto absent
```

The R401 files selected into this package use the hashes already validated by
that handoff's `24_R401_INTEGRITY_SHA256.tsv`. All other files are hashed during
package construction. The new unified manifest is authoritative for this ZIP.

## Why the complete R401 history is not duplicated

The full R401 handoff remains a separate history/archive artifact. Copying its
`11_SOURCE_ARCHIVE`, `12_CASE_LIBRARY` and `17_R386_CURRENT_POINT` into this
reproduction ZIP would add hundreds of megabytes of earlier and duplicate
material, including archived round labels that are not part of the clean active
line. The current executable worktree, later code deltas and material products
are included here instead.

## Reproduction levels

1. `verify_package.py`: byte/size verification for the complete payload.
2. `run_reproduction.py --profile active`: current R193–R210 and product tests,
   plus the R401 material-product tests.
3. `run_reproduction.py --profile full`: the active profile plus direct tests
   discovered in the embedded exact R392 product tree.

The runners create `REPRODUCTION_RUN_RECEIPT.json` only in the extracted copy.
That runtime receipt is deliberately not part of the immutable ZIP manifest.

