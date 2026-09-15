# V2P004 OPIA — Observation-Policy-adjusted Information Acquisition

## Composition

LCB `ObservationPolicyConfoundingGuardV0` + Foundry `P138 SPIA`.

The curated edge is valid only through a narrow bridge. P138 operates on a probability vector over target locations; K081's historical adjustment is scalar. The composition therefore never applies a scalar coefficient directly to the full belief vector.

For each candidate information channel, a declared zero-sum `effect_contrast` defines the scalar target-state coordinate that the observation may perturb. K081's neutral mechanism is reimplemented locally: reconstruct latent state from a passive proxy jointly with the observation-policy indicator, then regress the next contrast state on observation status and reconstructed state. The adjusted observation coefficient is mapped back to the minimum-norm belief shift whose projection on the declared contrast equals that coefficient. Because the contrast is zero-sum, the shift stays in the probability-simplex tangent space.

P138's search-policy utility geometry and its original validation remain authoritative. The guarded acquisition value then evaluates the same P138 measurement channel while including the estimated observation-induced belief shift. Ordinary information value is nonnegative because the signal can be ignored; physical measurement backaction need not be, so the guarded utility change is not clamped at zero.

Neutral mechanism:

`OBSERVATION POLICY + PASSIVE STATE PROXY -> BACKACTION ESTIMATE -> SIMPLEX-TANGENT SHIFT -> BACKACTION-AWARE INFORMATION VALUE`

## Fail-closed boundary

- every candidate measurement channel requires its own observation/backaction history;
- the historical design must separately identify observation status from reconstructed latent state;
- the backaction effect contrast must be nonzero and zero-sum;
- the estimated expected shift must keep the mean belief inside the probability simplex;
- no backaction model is generalized across channels or shells.

## Development evidence

The frozen suite has twelve cases: six preserve P138's original invariants through the composed path and six exercise K081-specific behavior.

In the deterministic confounded shell, the true declared observation effect on the target contrast is `+0.05`. Because the observation policy preferentially samples a different latent-state region, the naive observed-minus-unobserved contrast has the wrong sign. Policy-aware adjustment recovers `+0.05`. P138 alone acquires the near-boundary hotspot channel, while the guarded path rejects it because the estimated measurement backaction moves target mass toward locations that worsen search utility enough to erase the information value.

This is adapter/development evidence only. It is not a general causal estimate of measurement backaction, not field validation of P138, and not proof that every observation-policy problem should use this contrast bridge.
