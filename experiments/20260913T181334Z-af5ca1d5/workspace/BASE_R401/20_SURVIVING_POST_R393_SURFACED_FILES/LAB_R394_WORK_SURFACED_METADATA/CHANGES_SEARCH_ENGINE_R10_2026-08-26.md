# R10 changes

- Persisted current-interface rejections for `LCB-K089 -> P137` and `LCB-K089 -> P142`.
- Kept K089/P137/P142 as standalone searchable capabilities; only the direct edges are suppressed.
- Added `V2P006_IDASRO`: P025 scalar identification uncertainty routes into K068 directional robustness only through a certified affine downstream sensitivity map with provenance.
- Reimplemented the K068 quadratic directional robust mechanism independently in exact closed form; no monolithic LCB runtime import.
- V2P006 adapter suite: 12/12 PASS; original P025 4/4 PASS.
- Added 12 fixed bootstrap telemetry events; cumulative ledger now 60 events.
- Active queue bootstrap audit: 6 pilotable / 117 consumer-adapter / 720 supplier-only / 157 no-surface.
- Search->Foundry label advanced to R10; rejected interaction edges remain suppressed.
- Focused reflexive-engine regression: 67/67 PASS.
- R9->R10 Foundry source tree: 1305/1305 byte-identical excluding caches.
- Inventory: 310 base + 6 completed V2 composites = 316 addressable artifacts.
