# Product Result — PRIU v0.1

**Retro candidate:** R-017 / C-389 / E-806 + E-807 + E-808  
**Historical decision:** variant of IM-355  
**Product:** Priority-Reset Investment Unlocker  
**Status:** independent working product

PRIU evaluates every insertion position for a new-money claim in an existing priority waterfall. It
shows which position meets the lender's hurdle, whether old claimants improve relative to no funding,
and how much enterprise value the funded continuation creates net of new capital.

In the first construction:

- 30 units of new capital created **73 units** of net incremental enterprise value;
- junior new money recovered only **9.9** in expectation and remained blocked;
- an intermediate position recovered **26.4** and remained blocked;
- superpriority recovered **33.0**, producing lender NPV **+3.0** and unlocking financing;
- both existing claimant classes improved relative to their no-funding recoveries.

Four tests pass. PRIU is an independent financing and contract-scenario product; it is not contingent
on academic novelty, legal prediction, or integration with the current composition products.

v0.1 uses a one-period absolute-priority waterfall. The next standalone layer is collateral carveouts,
pari-passu sharing, uncertain funding draws, milestones, covenants, and negotiation constraints.
