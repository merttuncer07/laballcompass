# 17 September architecture and context-efficiency revision

User asked for internet-grounded architecture comparison and redesign, then
prioritized faster progress with fewer tokens. Live branch main, expected origin
and existing dirty checkout verified before edits. No commit/push or source reset.

Design and primary sources: ../../ARCHITECTURE.md. Previous startup documents
and changed infrastructure sources are preserved under before/ (text snapshots).
They include earlier uncommitted work; they are not clean Git HEAD snapshots.

Implemented: bounded mission briefs; selective exact component parsing; paginated
search; quiet execution with durable logs and visible failures; explicit historical
test labels; workbench/lab.py added to Python run snapshots; top-level application
tests included in all discovery. The lab profile includes tests/restoration, so
the all profile does not also run the separate restoration target twice.

Validation and text-volume measurements are in validation.json after the run.
Benchmarks are local engineering measurements, not future billed-token savings.
Python hashes do not cover all data or dependencies; no test cache was introduced.

Next unresolved action: the active workbook-review brief describes genuine
published-version acquisition, independent change labels and baseline evaluation.
Product superiority and user demand remain unvalidated. Stop further architecture
expansion after this slice; review net task cost on subsequent work.
