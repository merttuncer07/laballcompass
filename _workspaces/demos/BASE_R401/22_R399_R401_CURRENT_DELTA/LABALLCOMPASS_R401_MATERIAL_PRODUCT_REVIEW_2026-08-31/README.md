# R401 material-product review

This directory is a product-first review of the R398 archive and clean R399 state. It is deliberately
outside the canonical product authority: evaluation and usable shells should not mutate Lab history.

Start with:

- `R401_RETROACTIVE_BLUEPRINT.md` — what exists, what was proven, what was not, and the product map;
- `material_products/CONSEQUENCE_AWARE_INSPECTION_PLANNER/` — budgeted inspection planning;
- `material_products/TRIGGER_POLICY_DESIGNER/` — holdout-evaluated CSV trigger design;
- `R401_ARCHIVE_FULL_SCAN.json` — complete ZIP scan summary;
- `R401_ARCHIVE_FILE_INDEX.jsonl` — per-entry path/size/CRC/content-hash index;
- `R401_CAPABILITY_INVENTORY.json` — 69 parent products and parsed LCB class inventory;
- `R401_PRODUCT_MATERIALITY_MATRIX.json` / `.tsv` — current 57-suite code/evidence inventory.

The scan scripts are reproducibility tools for this review, not a new Lab control surface.

Run both product test suites and examples from PowerShell:

```powershell
.\run_material_products.ps1
```
