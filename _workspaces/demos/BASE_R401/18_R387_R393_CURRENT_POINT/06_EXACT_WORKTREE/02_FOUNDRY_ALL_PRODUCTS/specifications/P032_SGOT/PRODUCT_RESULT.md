# P032 SGOT v0.1 — Support-Gated Orthogonal Target

## Capability

SGOT composes OTE with OWS as a support gate rather than a reweighting repair. OTE's point estimate and standard error are left unchanged. Realized inverse-propensity weights are audited for concentration, while a separate two-sided propensity floor catches uniformly extreme assignment probabilities that relative ESS alone can miss.

## Adversarial benchmark

A good-overlap construction (`p=0.5`) passes with ESS 100/100. In the weak-overlap construction, the underlying coefficient used to generate the residual outcome is 2, but one rare counter-treatment observation dominates the orthogonal score. OTE returns target **5.00** with standard error **0.03015** and a narrow 95% interval **[4.9409, 5.0591]**. SGOT withholds deployment because effective support is only **3.96/100**, one observation carries **50%** of normalized inverse-propensity mass, and minimum two-sided propensity is **0.01**.

A separate all-`p=0.99` test has uniform realized weights, so OWS relative ESS alone reports usable support. The explicit propensity-floor check still blocks the claim. This prevents a known blind spot of concentration-only overlap diagnostics.

## Claim boundary

The support gate does not prove causal identification, correct nuisance models, SUTVA, or no unmeasured confounding. It only prevents OTE orthogonality from being misread as a cure for missing treatment support. No clipping-based "repair" is applied because that would change the target and still cannot manufacture missing counterfactual observations.

## Verification

5/5 product tests pass.
