# R-041 product result — CAPL v0.1

**Product route:** standalone constraint-aware portfolio policy learner  
**Result:** working product; 4/4 focused tests pass

CAPL turns observable signals directly into auditable portfolio actions. Feasibility is enforced in
the action path itself, and the entire untouched action sequence is retained for inspection.

Historical overlap with direct/end-to-end portfolio learning remains provenance rather than a veto.

In the first untouched 500-period construction, CAPL produced mean net return 0.004922 and
certainty-equivalent return 0.004885 versus 0.001531 for equal weight. The learned policy evaluated
2,401 candidates, respected the 0.70 asset cap and 0.40 turnover limit to floating-point precision,
and recorded zero sum, lower-bound, upper-bound, or turnover violations across all 500 actions.
