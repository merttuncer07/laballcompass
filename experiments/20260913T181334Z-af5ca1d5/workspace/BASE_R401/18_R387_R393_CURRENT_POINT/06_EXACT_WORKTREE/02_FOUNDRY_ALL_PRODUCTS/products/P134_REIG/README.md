# P134 REIG — Relational-Evidence Integrity Gate

REIG composes REL with EBC.

1. REL checks declared pairwise consistency relations among historical evidence records.
2. If no declared violation exists, REIG does not penalize historical borrowing power.
3. If violations exist, REIG converts REL's marginal *conditional* suspect mass into an explicit integrity multiplier.
4. EBC then performs its independent current-vs-historical compatibility weighting and global borrowing cap.

The adapter is deliberately conservative about semantics: REL posterior mass is conditional on the enumerated one-or-more-culprit hypothesis space. REIG does not call it an unconditional fraud probability.
