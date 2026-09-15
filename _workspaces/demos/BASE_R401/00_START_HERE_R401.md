# START HERE — LabAllCompass R401 Material-Product Handoff

This package freezes the Lab at the R401 checkpoint without deleting or rewriting its earlier history.
It was built additively from the user-supplied R398 retirement handoff whose SHA-256 is:

`ed3644144583921ac916c803511c08ba8caff72d030f5b1406580b2ff8f85abd`

All 10,320 files and 889,427,476 uncompressed bytes from that package remain in their original paths.
The R399, R400 and R401 material is added under `22_R399_R401_CURRENT_DELTA/`.

## State layers — do not collapse them

1. **Preserved historical archive:** the complete R398 handoff remains the archive base. Its own
   `00_START_HERE.md`, authority ledger, case library, source archive, exact-worktree boundary,
   negative knowledge and integrity material remain intact.
2. **Clean executable rehydration:** R399 is the latest promoted executable authority in the local
   rehydration record: 57 suites, 44 distinct product families, 516/516 direct tests and 57/57
   calibrated telemetry suites at promotion.
3. **Research after authority:** R400 promoted no V2P059. JARB-Native was retained as a negative
   transfer result, and the first eleven pair-frontier candidates were rejected/collapsed.
4. **R401 checkpoint:** R401 is a material-product review and usable-product layer outside canonical
   product authority. It must not be described as silently promoting a new V2P family.
5. **Current repository contract:** active Turing history ends at R178. The discarded R179–R192
   branch remains salvage history only and is never auto-loaded during normal work.

## Read order

1. `22_R399_R401_CURRENT_DELTA/00_R401_CURRENT_STATE.md`
2. `22_R399_R401_CURRENT_DELTA/01_AUTHORITY_BOUNDARY_R401.json`
3. `22_R399_R401_CURRENT_DELTA/LABALLCOMPASS_R401_MATERIAL_PRODUCT_REVIEW_2026-08-31/README.md`
4. `22_R399_R401_CURRENT_DELTA/LABALLCOMPASS_R401_MATERIAL_PRODUCT_REVIEW_2026-08-31/R401_RETROACTIVE_BLUEPRINT.md`
5. `22_R399_R401_CURRENT_DELTA/02_R401_CONTINUATION.md`
6. `23_R401_PACKAGE_MAP.md`
7. For the inherited archive history, continue with the original `00_START_HERE.md`.
8. Run `python 25_VERIFY_R401_HANDOFF.py`.

The inherited `09_VERIFY_ARCHIVE.py` is preserved byte-for-byte but reports 539 false `MISSING`
results when this deeply nested package is placed under the current Windows path. The files are
present; the verifier uses ordinary `pathlib` paths beyond the legacy Win32 path-length boundary.
See `22_R399_R401_CURRENT_DELTA/03_INHERITED_R398_VERIFIER_RESULT.md`. The R401 verifier uses the
Win32 extended-path form and hashes every file actually supplied and added.

## Material products present at R401

- `CONSEQUENCE_AWARE_INSPECTION_PLANNER`: budgeted inspection selection with explicit consequences.
- `TRIGGER_POLICY_DESIGNER`: holdout-evaluated trigger policy design from CSV data.

These are runnable material products, not new research-control infrastructure.

## Explicit exclusions and retirements

- The later `PRODUCTS/LAB_CRYPTO_ALGOTRADER` work is intentionally absent. It occurred after the
  requested R401 boundary and is not part of this handoff.
- No Bridge, Regime Router, custom Lab skill or control-plane architecture is reintroduced by the
  R399–R401 delta. Historical references inside the unchanged R398 archive remain historical only.
- The large local virtual environment is omitted. Small copied execution caches in the R399–R401
  source delta are non-authoritative and may be deleted after extraction.
- No old Lab memory, negative result or source/case history was deleted from the R398 base.

## Continuation principle

Work from an interesting real problem or a real dataset. Use products and R/T/IM memory as tools.
Do not make document gates, receipts, routers or self-control scaffolding prerequisites for ordinary
research, coding or testing.
