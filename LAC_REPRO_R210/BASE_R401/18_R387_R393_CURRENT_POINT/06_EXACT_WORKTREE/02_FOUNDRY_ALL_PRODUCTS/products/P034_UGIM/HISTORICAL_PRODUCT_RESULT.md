# P034 UGIM v0.1 — Ultimate Gain Incidence Mapper

## Capability

UGIM connects LGID's local incidence decomposition to OWNM's ownership-network propagation through one explicit bridge: a declared vector mapping local landlord assets to company nodes. It then propagates landlord rent transfers and property-capitalization gains by ultimate **cash-flow exposure** while reporting voting control separately.

## Benchmark result

The benchmark allocates all local absentee-landlord property gain to company C in a three-company 51%-51% ownership pyramid. An investor directly owns 51% of A and, through voting propagation, controls A, B, and C. Its economic cash-flow exposure to C is only `0.51^3 = 0.132651`.

UGIM therefore reports full control of the mapped local property-gain node but only **13.2651% economic incidence** to that investor. The remaining economic incidence is left as an explicit unassigned residual rather than being silently attributed through control rights.

## Claim boundary

The local-property-to-company mapping is an operator input; UGIM does not infer it from company names, voting control, or geography. Cash-flow ownership determines economic incidence. Voting control remains a distinct output and is not substituted for ownership. If the supplied investor set does not span all ultimate owners, the residual remains unassigned.

## Verification

6/6 product tests pass.
