# Selective salvage from laballcompass-fixes — 17 September 2026

Canonical checkout: `/Users/mertalituncer/Developer/lab`, main at 83a3a71.
Donor: `/Users/mertalituncer/Documents/Default Project/laballcompass-fixes`.
Both started at the same commit; their useful later work was uncommitted.
User authorized selective integration after a fresh read-only review. No commit
or push is part of this task. The donor remains untouched.

`before/` preserves the exact pre-integration versions, including earlier dirty
work. `before.json` records their hashes and donor hashes. The source-only donor
diff is retained in `donor-source.patch`; generated catalogs and old run results
were not imported. These backups begin after the earlier interrupted salvage,
which had already edited content.py and record_matches.py.

Accepted:
- BAMI evolves borrower classes separately in each scenario, preserving identity
  through delinquency/cure. A separate four-state matrix oracle covers 80 paths.
- ISTAICC measures continuation benefit relative to reachable no action from the
  same starting participation; a paid no-effect action now scores minus its cost.
- Record matching ranks candidates before spending the detail budget and includes
  formula/error-only coordinates in unmapped areas.
- Formula impact traversal starts at intermediate formula cells as well as roots.
- Explicit `--same-layout BEFORE.xlsx AFTER.xlsx` comparison. Completed the CLI
  and report, preserved supplied order (the old loader sorted alphabetically),
  and separated literal equality, unchanged formula text, changes, and unknowns.
  Identical formula text is not evaluated equality. Unknowns have separate impacts.
- Collection limits now agree at 100,000 populated cells. Existing compressed,
  expanded, worksheet, graph and search limits remain in force.
- Explicit catalog builds update both JSON and HTML with tested rollback on an
  index-replacement failure. Read-only discovery, selective lookup, historical
  result labels and the newer runner remain intact.

Retained canonical corrections: OPIA's zero-variance finite utility; workbook
snapshot hashes; SUMIF/AVERAGEIF effective ranges; compact root masks; contract
ownership; grouped ACSA/DREW, DTTC, package verifier and operating-layer work.
The donor's automatic catalog rebuild on discovery/check was not imported.
The optional PDF font-portability patch is preserved in donor-source.patch but
deferred: it needs its own font/glyph and visual validation and is not on the
engine/application execution path. No existing report was regenerated as evidence.

Validation results and run receipts are recorded in `validation.json` after
execution. Unit counterexamples are synthetic software checks, explicitly not
audit field evidence. Genuine published Apache POI workbooks are used separately
for unchanged-byte integration checks; they are engineering fixtures, not client
workpapers. No calibrated mortgage benefit, audit usefulness, novelty or product
superiority is established by this salvage.

Next product action remains acquiring two genuine published workbook versions
and independently labeling their real changes against the practical baseline.
