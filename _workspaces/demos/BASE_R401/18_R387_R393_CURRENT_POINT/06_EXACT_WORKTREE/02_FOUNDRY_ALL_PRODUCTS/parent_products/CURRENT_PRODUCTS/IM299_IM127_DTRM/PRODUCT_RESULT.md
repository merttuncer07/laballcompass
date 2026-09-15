# IM-299 → IM-127 + IM-317 product result: Decision Transient Risk Monitor v0.2

DTRM turns the existing finite-horizon operator into an executable monitor. Given a linearized
system, bounded uncertainty map, action contrast, nominal action gap, and horizon, it returns:

- the maximum decision-direction gain;
- the time of maximum action risk;
- the Transient Action-Flip Index;
- a certified lower action gap or an explicit flip-capable direction;
- the corresponding admissible initial perturbation;
- common-flow or action-branch propagation provenance.

## Reproduced working cases

For `A=[[-1,20],[0,-2]]`, horizon 4, uncertainty radius 0.1, and gap 0.2:

| Decision direction | Peak gain | Peak time | TAFI | Result |
|---|---:|---:|---:|---|
| `[1,0]` | 5.025063 | 0.688 | 2.512531 | flip-capable direction returned |
| `[0,1]` | 1.000000 | 0.000 | 0.500000 | certified in linear shell |

For action-specific systems `A_a=diag(-1,-2)` and `A_b=[[-1,20],[0,-2]]`, DTRM used the branch
difference rather than a common flow and returned peak gain 5.0, peak time 0.693, TAFI 2.5, and the
admissible perturbation `(0, 0.1)`.

## Working software

- reusable Python monitor using NumPy/SciPy matrix exponentials;
- common-flow and action-specific-flow modes;
- JSON configuration and CLI;
- dimension and shell validation;
- IM-317 Grönwall-style finite-horizon decision envelope when only a local growth inequality is known;
- seven automated tests, all passing.

## Next construction layer

Add repeated process disturbances by accumulating the decision-direction stochastic convolution,
then include state constraints through reachable-set clipping. This will make the monitor useful for
systems driven throughout the horizon rather than only by uncertain initial conditions.
