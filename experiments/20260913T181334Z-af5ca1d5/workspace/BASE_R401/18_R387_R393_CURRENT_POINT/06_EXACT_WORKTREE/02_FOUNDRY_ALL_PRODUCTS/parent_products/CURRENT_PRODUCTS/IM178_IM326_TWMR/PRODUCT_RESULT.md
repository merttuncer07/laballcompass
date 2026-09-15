# IM-178 → IM-326 product result: Target-Weighted Model Reducer v0.1

TWMR reduces a linear dynamical model according to the full past-input to protected-future-output
bridge rather than state magnitude or input energy alone.

## Construction result

A five-state system had one highly excited state with almost no protected-output loading, two true
target drivers, and two minor states. With a two-state retention budget:

| Method | Retained states | Relative target error |
|---|---|---:|
| State-energy baseline | large hidden energy + target driver A | 28.56% |
| TWMR | target driver A + target driver B | **3.31%** |

Target-weighted subset selection reduced relative target error by **88.41%**. The high-energy state
was removed because it did not carry comparable consequence to the protected output.

## Working software

- finite-horizon Markov/impulse-response target sequence;
- exact coordinate-subset search under a retained-state budget;
- protected-output error and relative error;
- controllability/state-energy comparison baseline;
- explicit retained and removed state lists;
- three automated tests, all passing.

## Next construction layer

Move from coordinate deletion to continuous projection bases, add stability/error certificates, and
support several protected outputs with independently declared consequence weights.
