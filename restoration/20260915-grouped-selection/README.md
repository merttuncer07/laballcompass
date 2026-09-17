# ACSA / DREW: whole-source group repair

ACSA now accepts declared source groups and resamples whole groups while retaining
the pooled case mean and full selection/tiebreak rule. Its cluster CR1 standard
error no longer treats every within-group row as an independent sampling unit.
Both partitions now require at least five groups and disjoint IDs in a shared
namespace. This fail-closed floor does not guarantee few-cluster coverage.
The canonical implementation and six embedded copies are identical. DREW passes
group IDs through its actual decision-loss adapter; nonzero transaction costs are
rejected in grouped mode because sequential group replay is not implemented.

**84 tests passed across two runs.** The first run passed 79 tests and found one
collection error in the new test's import. After that import-only correction,
the remaining five tests passed. The other tested sources remained byte-identical;
they were not needlessly rerun. See [validation.json](validation.json),
[first receipt](../../runs/20260915T170940Z-a2a6a24f/receipt.json) and
[corrected test receipt](../../runs/20260915T174437Z-9df9e1f6/receipt.json).
The package verifier passed on the final files. The catalogue was refreshed.

The [real-data evaluation](../../examples/grouped-selection/README.md) uses the
unchanged UCI Parkinsons Telemonitoring records: 5,875 recordings, 42 subjects,
one predeclared subject split, six fitted candidates and 2,000 draws per method.
In the protected split, 1,529 rows belong to 11 subjects. Standard error changes
from 0.11805 to 1.34253 (11.3725 times); the selected constant model and mean error
8.73124 remain unchanged. This is a mechanism check, not a banking or clinical
validation. The installed ACSA hash matches the actual experiment's source hash.

The mathematical regression arrays test algebra and API boundaries; they are
not represented as real audit records. The substantive evaluation uses genuine
published observations with no simulated-data fallback. Both outcomes and the
constant model's selection over five fitted alternatives are preserved.

CR1 and whole-cluster pairs bootstrap are established methods. This repair does
not demonstrate novelty, calibrated interval coverage, unknown-source discovery,
independence of distinct sources, retraining uncertainty or a complete laboratory.
Source availability in the SVB portfolio app remains separate from statistical
independence; this numerical experiment does not redefine evidence quality.

Original files are preserved under `before/`. The initial failing test is kept
under `intermediate/`. [changes.json](changes.json) and [source.patch](source.patch)
record this repair relative to the previous uncommitted working state. Earlier
repairs, archives and portfolio releases are preserved. No commit or push.
