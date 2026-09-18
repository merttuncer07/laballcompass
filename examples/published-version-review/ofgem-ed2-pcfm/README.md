# Ofgem ED2 PCFM: genuine published-version review

This is the first real version-pair run of the workbook-review product. The
inputs are two original Ofgem publications from the ED2 Price Control
Financial Model page, not files generated for the test.

Source page: <https://www.ofgem.gov.uk/guidance/ed2-price-control-financial-model>

The pair is deliberately ordered as before → after:

- `sources/ED2_PCFM_V4_2025-01-30.xlsx` — Ofgem's 30 January 2025 V4 file;
  SHA-256 `794fde9ebae9c407f1ae1378e269cee81b441ea05bc92cdfada8fbb788e8aba5`.
- `sources/ED2_PCFM_V4_2026-01-28.xlsx` — Ofgem's 28 January 2026 V4 file;
  SHA-256 `15f34eea70e6bb9e5ba873a546d4131a412072a6a46651509022518f2549e335`.

The direct publication links are:

- <https://www.ofgem.gov.uk/sites/default/files/2025-01/ED2_PCFM_V4_30_January_2025.xlsx>
- <https://www.ofgem.gov.uk/sites/default/files/2026-01/ED2%20PCFM%20V4%20%28published%2028%20January%202026%29.xlsx>

Ofgem describes the January 2026 file as an update of variable values after the
2025 Annual Iteration Process. That description is consistent with the run:
the formula text did not change, while input and calculated-value cells did.

## Reproduction

From the repository root:

```sh
.venv/bin/python lab.py workbench analyze \
  examples/published-version-review/ofgem-ed2-pcfm/sources/ED2_PCFM_V4_2025-01-30.xlsx \
  examples/published-version-review/ofgem-ed2-pcfm/sources/ED2_PCFM_V4_2026-01-28.xlsx \
  --same-layout --output /tmp/ofgem-ed2-review
```

The independent check used `openpyxl` to read both files with formulas intact,
normalize Excel array-formula objects to their formula text and range, and
compare the union of exact sheet-name/cell-coordinate positions. It did not
import the workbench comparison function and did not recalculate formulas.

## Observed result

Both workbooks have 31 sheets. The product read 62,571 populated cells in the
2025 file and 62,598 in the 2026 file, for 125,169 populated cells in the
pair. The exact same-layout comparison found:

- 37,588 unchanged literal values;
- 20,869 unchanged formula texts, including array formulas after normalization;
- 4,054 changed literal values;
- 87 cells added on the after side;
- 60 cells removed from the after side;
- zero changed formula texts;
- zero uncomparable cells in the final run.

The static dependency pass resolved enough of the graph to trace changed
cells to 416 unique potential downstream formula targets across 16 changed
blocks. These are structural impact candidates only. The product did not
recalculate Excel values or claim that every listed target numerically changed.
The full interactive source checklist was withheld because the pair contains
20,660 distinct root cells, above the 4,000-source viewer budget. The content
report still contains the bounded impact lists.

The full generated HTML/JSON report is intentionally not stored here because
it is about 33 MB. Re-run the command above to produce it locally. The source
workbooks and this summary are the preserved evidence record.

This is a software and real-file validation result, not evidence that the tool
has been accepted by Ofgem, a bank, an audit firm or an auditor. No numeric
formula result was certified.

The repository software run after these changes passed 186/186 tests; its
receipt is [runs/20260918T031020Z-8393af30/receipt.json](../../../../runs/20260918T031020Z-8393af30/receipt.json).
