# LabAllCompass working notes

## New-chat startup contract

The only active checkout is `/Users/mertalituncer/Developer/lab`. Start every
new Codex chat from this folder and make it the local project's **primary
folder**. Do not use `/Users/mertalituncer/Documents/Codex/2026-09-13/do-x20`,
`/Users/mertalituncer/Documents/Codex/2026-09-16`, or any `experiments/` copy as
the working checkout. Those locations are historical or isolated records.

Before editing, verify that the current directory is the path above, the branch
is `main`, and the remote is
`https://github.com/merttuncer07/laballcompass.git`. Use the existing checkout
for this project; do not create a new worktree unless the user explicitly asks
for isolated parallel work. Keep the existing working tree when continuing,
because it contains the current uncommitted repairs.

Read `CONTINUE_HERE.md`, `LAB_STRATEGY.md`, and the relevant restoration record
before choosing a new task. `CONTINUE_HERE.md` is a handoff, not a request to
repeat completed experiments.

This checkout is the active lab. Original Downloads archives and earlier releases are historical inputs; use them when origin questions require them. Do not restart inventory work from those copies.

Find a mechanism with `.venv/bin/python lab.py components --query NAME`, then `.venv/bin/python lab.py show ID`. These read current source without saving the catalog. Read the returned source and relevant callers. Use `python -m maintenance.catalog` only when an updated on-disk catalog is needed.

Main code areas: `workbench/` for evidence/file dependency analysis; `maintenance/` for discovery, execution and comparisons; `LAC_REPRO_R210/` for mechanisms and composed products. `LAB_STRATEGY.md` records the active direction, `PRODUCT_REPAIRS.md` the repairs, and `runs/` / `restoration/` the evidence. Retrieve the relevant entry, not every record.

Complete a useful capability with its affected consumers. Use component checks and focused tests, expanding when shared code or failures justify it. Preserve verbose results in existing record locations and report the result and failures briefly. Do not rerun unchanged successful experiments merely because a conversation resumed.

Public audit cases must use genuine source files. Keep mechanism counterexamples distinct from field evidence. A runnable demo or passing test is not a measured product advantage.

At a natural task boundary, update the relevant existing record with the next unresolved action. No mandatory model routing, extra orchestration framework or deployment platform is needed.
