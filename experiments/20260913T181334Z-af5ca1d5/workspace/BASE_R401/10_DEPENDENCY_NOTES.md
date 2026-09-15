# Dependency and execution notes

The archive intentionally preserves historical Python source, tests, shell artifacts, JSON/JSONL, TSV/CSV, reports, raw transcript and benchmark data. Historical code may depend on Python standard library plus packages present in its original environment (notably pytest; some real-data pilots use scientific Python/scikit-learn). Exact historical environment lockfiles were not uniformly present in every revision; any present dependency/config files are archived in their original paths.

Do not silently modernize historical code. Reproduce in-place first; make migrations in a new shadow layer with provenance. `09_VERIFY_ARCHIVE.py` validates archive integrity and canonical inventory invariants without requiring every historical experiment dependency.


R385 entity/instrumentation reconstruction uses Python stdlib only; it reads canonical R12 JSON/JSONL artifacts and does not introduce a new runtime dependency.


## R386
R386 adds no new mandatory third-party runtime dependency to the archived R12 control plane. Individual experimental products may use standard-library/numpy-style numerical code already represented in the source tree; exact imports are preserved in source.


## R387–R393
Current Lab code remains primarily Python. Historical/current tests use pytest; numerical products may use numpy/scientific-Python dependencies already present in the source tree. The archive verifier itself uses Python standard library only. Do not silently modernize historical code or restore obsolete absolute paths. Current product tests must resolve package-relative dependencies. R392/R393 routing JSONL files are large but are data artifacts, not extra runtime dependencies.


# Late recovery dependency note
`RECOVERED_REFERENCE_CODE` uses Python + NumPy only and is deliberately decoupled from the exact parent runtime. A faithful rebuild should instead import the exact R392 parent modules for ACRA, DSBC, DLEW, AICC, SACPS, RECS/P017, LCB-K090 and ATRC from the embedded exact worktree and reproduce the original shell tests.
