# R398 Frozen Candidate State — DO NOT SILENTLY PROMOTE

Base authority: **R397 / Products56 / Quality43**.
Candidate: **V2P058 SACATRC**.
Candidate accounting if and only if promotion gate is replayed and passes: **Products57 / Quality44**.

### Candidate evidence already obtained
- V2P058 hardened direct: 14/14 PASS.
- Correct-support frozen shell RMSE: ~1.22155 → ~0.12168.
- Wrong-support frozen shell RMSE: ~1.22155 → ~1.40987.
- 100-cell sensitivity: correct/nonzero 20/20 positive; diagonal 25/25 exact collapse; wrong-support tolerance=.02 5/5 negative.
- Exact-current-shell mechanics pilot: 14/14 COMPLETE.
- Candidate ledger: 516 events; 516 exact; 57/57 calibrated; 0 unmatched.
- Candidate closure: 31/31 PASS.
- Old R393 canonical tree byte identity: 421/421.
- Foundry byte identity: 1305/1305.
- V2P054–058 fresh direct: 69/69 PASS.

### Missing terminal evidence at retirement
The remaining split state-sensitive promotion-regression batches had not all produced terminal receipts. A prior first batch was 34/34 PASS, but this is insufficient for explicit promotion.

### Successor rule
Because the exact R398 ephemeral source tree was lost after runtime remount, the safest successor path is not to infer promotion. Reconstruct/recover V2P054–058 bytes, replay current-shell tests/telemetry and the full R398 promotion regression from the byte-complete R392/R393 base, then explicitly write a new authority transition only if all gates pass.
