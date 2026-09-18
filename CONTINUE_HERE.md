# Current checkpoint — 17 September 2026

User priority: **faster progress with less token use**, with better product
quality. Continue in Developer/lab on main; preserve uncommitted repairs.
No commit, push, deletion or fresh checkout was performed for the redesign.

Run `.venv/bin/python lab.py focus`. It returns the active objective, baseline,
stop criteria, verification command and pointers to relevant source/evidence.
Use `focus --list` for parked work. Do not reload all previous experiments.

The architecture is now problem-first with one active product pilot:
compare genuine published workbook versions and show potential formula impacts.
This is provisional, based on existing work; customer demand is unvalidated.
The genuine Ofgem pair is now preserved and has been run end to end. The next
action is reviewer-focused interpretation and a stronger independent impact
check, not another broad limit increase.

The real-file result is in [examples/published-version-review/ofgem-ed2-pcfm/README.md](examples/published-version-review/ofgem-ed2-pcfm/README.md): 125,169 populated cells were accepted across two official versions, array formulas were normalized, and 416 unique static downstream targets were traced. The interactive source checklist remains bounded at 4,000 roots; large reports retain the content diff and bounded impact lists.
Existing SONI parsing and R207 comparisons are completed evidence, not tasks.

17 September selective salvage: BAMI/ISTAICC repairs, matching and formula-impact
fixes, explicit same-layout comparison and catalog publication were integrated
without replacing newer canonical work. Before versions, decisions and validation:
[salvage record](restoration/20260917-salvage-fixes/README.md).

17 September operating-layer changes: bounded briefs, selective component
lookup, paginated search, quiet durable verification, explicit historical-result
labels, and application tests included in the all profile. Implementation,
measurements and limits: [record](restoration/20260917-architecture/README.md).
The full design/comparison is in [ARCHITECTURE.md](ARCHITECTURE.md).

Previous OPIA/ACSA/DTTC/package repairs and all earlier work are retained.
The earlier 1,682-test result predates this redesign and does not certify
current code. New validation is in the architecture record. No passing suite
establishes market value or statistical coverage; ACSA's five-group floor
remains an engineering policy, not a confidence-coverage proof.

For a historical question only: the complete previous handoff is preserved in
[before/CONTINUE_HERE.md](restoration/20260917-architecture/before/CONTINUE_HERE.md).
Older network, permissions and visibility statements are historical; check
live state when relevant. No need to repeat inventory on chat resume.
