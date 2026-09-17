# LabAllCompass working notes

Only active checkout: `/Users/mertalituncer/Developer/lab`.
Before editing verify cwd, branch `main`, and origin
`https://github.com/merttuncer07/laballcompass.git`.
Preserve the existing dirty tree. No new worktree unless explicitly requested.
Historical Documents/Downloads/experiments copies are not working checkouts.
Commit/push requires a separate user request.

Start with `CONTINUE_HERE.md`, `LAB_STRATEGY.md`, then
`.venv/bin/python lab.py focus`. Read the relevant linked evidence and source
before editing. Do not load the whole archive, catalog, or repair history by
default. A handoff is not an instruction to repeat completed experiments.

Find mechanisms with `lab.py components --query NAME` (20 results/page;
`--offset N`), then `lab.py show ID`. These are read-only.
Use `.venv/bin/python` for all lab commands. Only explicitly rebuild the
catalog when the saved artifact is needed.

`workbench/`: file-review application. `maintenance/`: discovery/evaluation.
`LAC_REPRO_R210/`: preserved mechanisms. `lab-focus.json`: one active objective,
baseline, success/stop criteria, source/evidence pointers.
`ARCHITECTURE.md`: design and comparison; retrieve only for architecture work.

Complete a useful capability and its affected consumers. Run focused tests;
expand for shared changes or failures. `lab.py run --profile lab --quiet`
checks the application/maintenance tests; `--profile all` includes these and
the legacy targets. Quiet mode keeps failures visible and full logs in runs/.
Receipt hashes cover Python sources, not all data: no automatic cache reuse.

Real cases use genuine sources; synthetic counterexamples remain labeled.
Software correctness, comparative advantage, novelty and user value are
separate claims. Source fidelity cannot be inherited from missing old code.

At a task boundary update the active brief and the relevant evidence record:
result, limitation, next action. Keep startup documents concise; history stays
in restoration/. No mandatory model routing, agents, or extra framework.
