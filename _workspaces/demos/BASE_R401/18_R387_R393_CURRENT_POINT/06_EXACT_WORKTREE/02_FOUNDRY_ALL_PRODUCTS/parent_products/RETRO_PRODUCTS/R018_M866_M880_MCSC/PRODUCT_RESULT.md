# R-018 product result — MCSC v0.1

**Product route:** standalone structural decision certificate  
**Result:** working product; 4/4 tests pass

MCSC accepts an ordered action-by-parameter payoff table and checks every pairwise
increasing/decreasing-differences rectangle. It returns the complete argmax correspondence, least
and greatest selections, a certified response direction when one exists, and an exact worst
counterexample when it does not.

In the first construction, the payoff `theta*x - 0.5*x^2` certified a nondecreasing optimal action
path `0,1,2,3,4,5`. A deliberately damaged cell still left the observed optimum path monotone, but
MCSC correctly refused the stronger structural claim and localized a 19-unit increasing-differences
violation at actions 5/6 and parameters 4/5. This distinction is the product: it prevents a clean
sample path from being mistaken for a reusable policy-response law.

This product stands independently. Integration with an existing LABALLCOMPASS product is optional.
