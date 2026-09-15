# Product Result — EBC v0.1

**Retro candidate:** R-026 / S-423 + S-424  
**Historical decision:** merged into IM-081 / IM-131  
**Product:** Evidence Borrowing Controller  
**Status:** independent working product

EBC combines a current normal estimate with historical estimates using source-specific maximum power,
conflict-adaptive commensurability, and a cap on total borrowed precision relative to current data.

In the first three-market construction:

- the current-only estimate was **1.200 ± 0.250 SE**;
- uncontrolled pooling let a conflicting precise market shift it to **1.701**;
- adaptive borrowing reduced that conflicting source's power to **0.00050**;
- total borrowed precision was capped at exactly **2×** current precision;
- the controlled estimate was **1.174 ± 0.144 SE**, only −0.0256 from current data;
- current data retained one-third of total information instead of 6.96% under uncontrolled pooling.

Four tests pass, including compatible borrowing, conflict rejection, global cap enforcement, and an
exact current-only mode. EBC is a standalone sequential evidence product; current-product integration
is not required.

v0.1 covers independent normal estimates with known/estimated SEs. The next standalone layer is
binomial/rate outcomes, hierarchical source clusters, time decay, robust mixtures, and online updates.
