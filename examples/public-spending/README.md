# Public spending record comparison

Open [observations and baselines](verified/index.html), then [the changed amount](verified/changed_unique_voucher/report/index.html). The report initially shows the single changed value and both dependent SUM formulas. The [ambiguous example](verified/changed_repeated_voucher/report/index.html) shows which rows could not be matched.

The input CSV contains 84 published HM Treasury spending records for September 2025. [Publisher](https://www.gov.uk/government/publications/hm-treasury-spending-over-25000-september-2025), [original download and hash](SOURCES.json). It was downloaded intact. Reuse is under the Open Government Licence v3.0. A published dataset's title is not a rule that every individual line item exceeds £25,000; no threshold violation is inferred.

The Excel files are **generated derivatives for this experiment**. Rows and columns are shuffled, one amount is increased by 123.45, one case renames headers, and demonstration SUM formulas are added. These are not discovered errors in HM Treasury's publication or client audit workpapers. The amount column contains mixed currency formatting; the generator explicitly removes leading £ and thousands commas before numeric conversion. Other fields remain text. The application itself accepts Excel, not CSV.

Observed outcomes, using a fixed seed and maps withheld from the matcher:

| Case | Value-based record matching | Header-aligned exact rows | Header-aligned 80% row matching |
|---|---:|---:|---:|
| Rows and columns reordered | 84/84 | 84/84 | 84/84 |
| First unique-voucher amount changed | 84/84, changed pair found | 83/84 | 84/84, changed pair found |
| First repeated-voucher amount changed | 83/84; ambiguous changed pair omitted | 83/84 | 83/84; ambiguous changed pair omitted |
| Headers renamed and unique-voucher amount changed | 84/84, changed pair found | Cannot align headers | Cannot align headers |
| Each column independently shuffled | No row candidate | No exact row | No row candidate |

No returned pairs disagreed with the planted row maps in the four derivative cases. This is five controlled cases from one public dataset, not estimated field accuracy. The two header baselines are a strong alternative when headers are available. The added capability is automatic column correspondence from values; it is not a scientific novelty claim. Equal column distributions without corresponding records did not create a match in the fifth case.

Reproduce from the lab directory (choose a new output folder):

```sh
.venv/bin/python examples/public-spending/reproduce.py --output /tmp/new-spending-observations
```

Analyze the same files through the ordinary product command:

```sh
.venv/bin/python lab.py workbench analyze examples/public-spending/verified/changed_unique_voucher/inputs --output /tmp/new-spending-review
```

The reproduction script uses that command's `save_workbook_analysis` implementation, then adds a visible notice explaining the artificial transformation to the example reports. Formula tracing uses R207; the value-based matcher is new workbench code. Matching values never merge lineage roots. Formula values are not recalculated, covariance is not inferred, and the output is not an audit opinion. The lab's EBC covariance calculations remain a separate API requiring justified numerical inputs.

Older `observed-v1` and `report` outputs are retained; `verified` is the current result. See its [receipt](verified/receipt.json) for preprocessing, source/code hashes, cases and informational single-run timings. Timing compares different operations and is not a speed benchmark.
