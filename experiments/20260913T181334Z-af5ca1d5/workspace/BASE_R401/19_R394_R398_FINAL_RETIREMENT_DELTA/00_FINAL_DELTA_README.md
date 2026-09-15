# R394–R398 Final Retirement Delta

This directory is the additive layer after the R393 archive-of-record. It exists because the retiring instance continued product mining through R398 after the R393 handoff.

### What is exact
- The entire inherited R393 archive and its R392 exact worktree are exact historical bytes.
- The numerical/test/telemetry/authority results in this directory are recovered from the conversation's completed tool receipts and assistant status messages.

### What is not exact
- The ephemeral R394–R398 source trees were not surfaced as durable files before a runtime remount. Their byte-exact contents are unavailable in the final runtime.
- `RECOVERED_REFERENCE_CODE/` therefore contains contract-faithful reference reconstructions, not byte-identical canonical source.

### Final research position
The logical canonical line reached R397 (`56 executable / 43 distinct`). R398 built V2P058 and closed its candidate telemetry/closure, but did not finish the remaining terminal promotion-regression batches before retirement. Freeze it as candidate, not canonical.
