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

## 2026-09-15 selection rule repair

The optional `selection_tiebreak_scores` matrix now represents the selector's
secondary score. Selection minimizes mean loss, then maximizes mean tiebreak
score on an exact tie, then retains column order. Both matrices must describe
the same selection cases and candidates. Bootstrap resamples their rows
together and repeats that complete rule; no holdout values enter selection.
Omitting scores preserves the previous first-column tie behavior.

`material_regret` must be finite and nonnegative. NaN or infinite thresholds
previously suppressed the regret-detected status; they now raise ValueError.
The reported instability status is a diagnostic at the existing 0.5 frequency
threshold, not a calibrated false-discovery test.

Run all 17 current tests with `python -m pytest -q` in this folder, or
`./.venv/bin/python lab.py check R014` at the lab root. The older unittest-only
command does not collect module-level regression functions. The lab runner now
selects pytest for this mixed suite.

Bootstrap intervals and frequencies resample the supplied rows. They do not
replay a sequential policy or account for unknown clusters, shared data sources,
or writer dependence. Those uses need an appropriate sampling model. Observed
repair records: `restoration/20260915-selection-identity/` at the lab root.
