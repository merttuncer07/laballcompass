# Consequence-Aware Inspection Planner

This is a usable product shell for the Lab's `IM406_IM037_ACRA` mechanism. It chooses one
inspection or measurement mode per asset under a shared budget. The objective is not generic
accuracy: it minimizes error where delay, diagnostic ambiguity and failure consequence matter.

It produces:

- an inspection mode for every target;
- spend and consequence-weighted loss;
- comparisons with the cheapest plan and the best affordable uniform policy;
- the next budget breakpoint that changes the optimum;
- a budget curve;
- re-planning under user-declared consequence stresses;
- JSON output plus a short operational Markdown report.

The optimizer is dependency-free and exact for the declared discrete choices. It retains the
non-dominated multiple-choice frontier rather than rounding costs into integer buckets.

## Run the included example

Use any Python 3.10+ interpreter:

```powershell
python planner.py example_maintenance.json --output example_output.json --report example_report.md
```

Run the tests:

```powershell
python -m unittest -v test_planner.py
```

## Input meanings

Each target supplies:

- `urgency_weight`: how costly delayed detection is;
- `diagnostic_weight`: how costly ambiguity about the failure type is;
- `consequence`: relative operational consequence;
- optional `cost_multiplier`, error scale multipliers, and `allowed_modes`.

Each mode supplies:

- `cost`;
- `delay_error`;
- `diagnostic_error`.

Only ratios matter. The loss is a relative planning score, not money. Field deployment requires
cost and error estimates from actual inspections; the tool does not manufacture those estimates.

## Provenance and change from the parent

The native ACRA parent uses a mixed-integer optimizer to minimize:

`consequence × (time_importance × time_error² + frequency_importance × frequency_error²)`.

This product preserves that operator, renames the axes for inspection work, adds per-target
feasibility/cost/error modifiers, removes the SciPy runtime dependency, and adds operational
comparators, stress cases and reports. It does not alter the canonical Lab parent or product set.
