# ACSA v0.1 — Adaptive Candidate Selection Auditor

ACSA audits a model, policy, prompt, design, or process variant chosen after comparing many
candidates on the same data. It keeps the entire candidate family visible and measures what happens
on an untouched evaluation sample:

- which candidate selection data chose;
- which candidate actually performs best on holdout;
- selected-candidate optimism and regret;
- the worst selection-to-holdout gap anywhere in the family;
- holdout uncertainty; and
- how often bootstrap resamples would select each candidate.

This is not an academic accept/reject gate. It is a practical firewall against shipping a winner
created by the search procedure itself, while preserving the losing ideas and their measured behavior.

Run `python -m unittest -v test_acsa.py` and `python demo_selection.py`.
