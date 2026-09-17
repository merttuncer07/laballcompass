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

Run all current tests with `python -m pytest -q` in this folder, or
`./.venv/bin/python lab.py check R014` at the lab root. The older unittest-only
command does not collect module-level regression functions. The lab runner now
selects pytest for this mixed suite.

Without group IDs, bootstrap intervals and frequencies resample the supplied
rows independently. Observed selection-rule repair records are preserved at
`restoration/20260915-selection-identity/` at the lab root.

## Whole-source groups (2026-09-15)

Supply both `selection_groups` and `holdout_groups` to use whole-group pairs
bootstrap. Each ID must be a nonblank string or integer (not a boolean or float),
one per row. IDs use a shared namespace across partitions, with at least five
groups in each partition and no overlap. Integer `1` differs from string `"1"`;
NumPy integer IDs compare equal to Python integers. Unknown or missing IDs must
be resolved by the caller, not replaced by invented independent groups.

Every draw samples G groups with replacement and retains every row of each drawn
group, including duplicates. Candidate losses and tiebreak scores stay paired.
The pooled row mean is preserved; unequal group sizes are not given equal weight.
The selected holdout candidate stays fixed during resampling.

For N holdout rows in G groups, centered group loss totals T_g give the
intercept-only CR1 standard error `sqrt(G/(G-1) * sum(T_g**2)) / N`.
`pointwise_95_radius` remains `1.96*SE`, an approximate normal radius; the bootstrap
interval is the percentile interval. Output reports the sampling/SE methods,
unit counts, largest holdout unit share and the pooled-case estimand.

Five groups is a fail-closed engineering floor, not a claim that five clusters
guarantee nominal coverage. Few-group limitations still require judgment.

This implements established methods: [cluster pairs bootstrap, Cameron & Miller,
section II.F](https://cameron.econ.ucdavis.edu/research/Cameron_Miller_JHR_2015_February.pdf)
and the intercept-only specialization of [Statsmodels' cluster sandwich
implementation](https://www.statsmodels.org/stable/_modules/statsmodels/stats/sandwich_covariance.html#cov_cluster).
It does not prove independence, recover unknown provenance, replay sequential
policies, retrain models or account for adaptive candidate generation. Few groups,
one dominant group and cross-group dependence limit inference. Neither interval
has guaranteed coverage; existing status labels are descriptive diagnostics, not
significance tests or evidence-quality scores.

The real repeated-subject evaluation, original-source hashes and repeatable command
are at `examples/grouped-selection/README.md` in the lab. This is mechanism
validation, not a clinical or banking case.
