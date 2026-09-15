# Product Result — PPSA v0.1

**Retro candidate:** R-010 / C-359 / S-679 + S-680  
**Historical decision:** variant of IM-421  
**Product:** Privacy Pipeline Safety Accountant  
**Status:** independent working product

PPSA validates a release pipeline, charges real raw-data mechanisms, preserves zero-additional-cost
post-processing, and chooses the tighter of basic and explicit-slack advanced sequential composition.

In the first pipeline construction:

- **100** private mechanisms and **50** downstream dashboards were traced separately;
- correct basic composition was ε=**5.0**, not the naive 7.5 that charges dashboards again;
- advanced composition reduced the reported result to ε=**2.8846**, δ=**1.1e-6**;
- the pipeline remained inside an ε=3.0, δ=2e-6 budget;
- a post-processing declaration that touched raw data was rejected.

Four tests pass. PPSA is a standalone privacy-engineering product and requires no integration with
the current composition products.

v0.1 implements sequential composition and data-independent post-processing. The next standalone
layer is Rényi/zCDP accounting, subsampling amplification, parallel cohorts, and a pipeline DAG UI.
