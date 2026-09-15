# R9 changes

- Added persistent `COMPOSITION_EDGE_ADJUDICATIONS.jsonl` and active-queue suppression for rejected direct interfaces.
- Independently rejected `LCB-K058 -> FOUNDRY:P143`; DLIC's constrained-LP integrality certificate is not an exact QUBO encoding for K058.
- Added `V2P005_EDSANP`: K019 effective-diversity evidence gate before P003 SANP, with raw-covariance ENPC fail-closed fallback.
- Added 12-case V2P005 suite and fixed development benchmark.
- Added 12 standardized bootstrap events; cumulative ledger now 48 events.
- Search->Foundry label advanced to R9 and ignores inactive adjudicated edges during interaction expansion.
- Active 1,000-row bootstrap audit: 5 pilotable / 120 consumer-adapter / 718 supplier-only / 157 no-surface.
- Focused engine regression 65/65 PASS; V2P005 12/12; original P003 6/6; original P143 6/6.
- Foundry source tree remains byte-identical to R8 (1,305 files excluding caches).
- Inventory: 310 base + 5 completed V2 composites = 315 addressable artifacts.
