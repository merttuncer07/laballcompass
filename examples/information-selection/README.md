# AICC: decision value and dependent observations

[Open the computed example](index.html). These are declared synthetic Gaussian measurements, not audit evidence or a real client case.

```sh
.venv/bin/python lab.py select-information examples/information-selection/input.json
.venv/bin/python lab.py select-information examples/information-selection/input.json --output /tmp/new-aicc-result.json
```

Output files must be new. `input.json` supplies the state mean/covariance, affine action slopes/intercepts, channels, costs, named channel-error covariance, and actual observation sequence. Costs must use the same units as utility. Nothing is inferred from the names or equal observation values.

In finite joint mode, each channel represents **one** observation. The first two channels share all their error; the third is independent. After the first observation the variance is 0.5 and the copy's remaining value is zero. Replaying the copy leaves the mean and variance unchanged. Observing the third channel reduces variance to 1/3. An inconsistent copy is rejected. General partial positive/negative error correlations are also supported.

Without `channel_noise_covariance` and its exact ordered `covariance_channel_names`, the original fresh-independent-measurement mode remains: each call supplies a new noise draw. Equal values across two genuinely independent draws still add information. Do not represent a new draw by replaying a finite channel; create the correct finite observation model or use fresh mode.

Decision values now use analytic Gaussian upper-envelope integration, replacing the fixed 31-node approximation. For `max(0,Z)`, old value 0.38835954 versus the closed-form 0.39894228 reverses selection at a 0.393 cost. The existing QAIG composition has a corresponding cost-boundary regression test. This is a known mathematical method, not a novel acquisition algorithm. [Actual upstream code read and references](../../research/aicc-knowledge-gradient/OBSERVATIONS.md).

The model assumes initially independent latent state and channel error, a supplied Gaussian law, affine utilities, and a one-step decision objective. Square-root conditioning preserves singular duplicate/error-cancellation structure without adding independent noise. Tiny negative eigenvalues within numerical validation tolerance are clipped when constructing a factor; substantive indefiniteness is rejected. Extreme expected values may underflow in ordinary floating point. The EBC and AICC joint models require different meanings for their covariance inputs; they are not automatically interchangeable.
