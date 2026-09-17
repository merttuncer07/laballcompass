# Lab strategy — 17 September 2026

LabAllCompass explores mathematical mechanisms and their useful compositions.
Its scope includes dependence, decisions, representation, dynamics and proof;
the workbook product is one candidate, not the identity of the whole lab.

Current priority: **accepted progress per token and per unit of time**.
Optimize task completion subject to correctness and evidence quality. Test
count, number of products and generated reports are not the objective.

Keep the mechanism archive and working code. Rebuild the operating workflow
incrementally. Use one active objective in `lab-focus.json`; keep other lines
parked and searchable. This WIP limit is a local operating choice, not a
universal law. More agents or model routing need evidence of net benefit.

Each objective states the real task, strongest practical baseline, success
criterion, stop condition, next action and source/evidence pointers. A short
`lab.py focus` brief is the default context; retrieve detailed history only
when the task requires it. Preserve negative results to avoid repeated search.

Evaluation has four separate levels: software correctness; same-task advantage
over a baseline; independently assessed user benefit; defensible novelty.
A result cannot be promoted merely by passing unit tests or generating a demo.
Freeze test inputs, evaluator and source hashes for comparisons; separate
development from held-out source families. Report false positives, omissions,
cost and regressions. Changing the evaluator starts a new comparison.

Provisional active pilot: genuine published workbook-version review.
Measure changed-cell precision/recall, downstream impact agreement, latency
and reviewer effort against coordinate/value diff plus ordinary graph tracing.
Use independent labels. The existing synthetic benchmark found no R207
advantage over equally batched AND/OR; preserve that result. Do not force a
lab engine into a product when the baseline serves the task better.

Stop source acquisition after one focused session if a usable real pair cannot
be found, and reassess the candidate. Stop infrastructure work after the current
operating-layer validation. No market success is claimed yet.

Research comparison, current/target architecture and staged migration:
[ARCHITECTURE.md](ARCHITECTURE.md). Previous strategy and source observations:
[archived strategy](restoration/20260917-architecture/before/LAB_STRATEGY.md).
Measurements and next unresolved action:
[redesign record](restoration/20260917-architecture/README.md).
