# R387 authority transition

R387 promotes the R386 product overlay only after the portability repair and the terminal full-package regression receipt.

## Canonical product layer

- Registry families: **455**, unchanged.
- Executable V2 suites: **47**.
- Quality-distinct V2 product families: **34**.
- R386-native suites accepted into the executable layer: V2P039, V2P040, V2P041, V2P042, V2P043, V2P044, V2P045, V2P046, V2P048.
- New distinct families among that block: V2P039, V2P040, V2P041, V2P042, V2P043, V2P046.
- Executable family variants: V2P044→V2P035 family, V2P045→BOUNDARY_GATE_ROUTING_VARIANTS, V2P048→V2P043 family.
- V2P047 remains quarantined and is not an executable/canonical product.

`01_V2_CORE/PRODUCT_QUALITY_AUDIT_V1.json` remains the immutable R12 base audit. `01_V2_CORE/PRODUCT_QUALITY_AUDIT_R386.json` remains the R386 overlay adjudication. The explicit current authority switch is `01_V2_CORE/CURRENT_PRODUCT_AUTHORITY.json`.

## Promotion gates

- terminal packaged regression: PASS / exit 0;
- Foundry: 214 test files / 806 tests / 0 failures;
- R387 overlay closure: 7/7;
- R386-added executable suites after portability repair: 72/72;
- telemetry: 388 events, 388 exact current-suite matches, 0 unmatched;
- calibrated suites: 47/47;
- interaction map: 47 completed-composition edges;
- fixed-pilotable calibrated queue rows: 47;
- campaign mechanics passes: 47;
- rejected-current-interface edges preserved: 4;
- learning-eligible empirical campaign events: 0.

Promotion means deterministic executable/control-plane closure. It does **not** mean scientific validation, field validation, deployment validation, or empirical learning.

## Portability repair incorporated before promotion

Eight R386 test harnesses contained absolute paths to the prior R385 extraction. R387 replaced those with package-relative dependency resolution, reran the affected suites, preserved 64 old telemetry rows as superseded provenance, generated 64 replacement R387 exact-shell rows, and kept the live telemetry ledger at 388 rather than double-counting history.
