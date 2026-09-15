# R401 — Retroactive Lab blueprint and material-product evaluation

## Bottom line

The Lab is not empty. It contains a substantial mechanism library and many executable research
prototypes. But it has repeatedly counted *scientific construction* as if it were *delivered user
value*. Those are not the same thing.

The useful core is:

- a large memory of mechanisms, failed combinations and boundary cases;
- reusable mathematical/software kernels;
- standalone parent products that implement a complete operator;
- higher-order compositions with unusually good removal controls and failure-region tests.

The missing layer is mostly mundane and product-shaped: real input adapters, user terminology,
out-of-sample evaluation, actionable reports, saved scenarios and contact with a real workflow.
Another controller, gate or registry will not supply that layer.

R401 therefore leaves the Lab authority untouched and starts a separate material-products surface.
The first delivered tool is the `CONSEQUENCE_AWARE_INSPECTION_PLANNER`.

## What was actually inspected

The supplied R398 retirement ZIP was read entry by entry, not sampled. Every file was decompressed,
hashed and CRC-checked.

| Archive fact | Observed value |
|---|---:|
| Files read | 10,320 |
| Uncompressed bytes read | 889,427,476 |
| Text files | 10,178 |
| Binary files | 142 |
| Unique content hashes | 5,061 |
| Duplicate-content groups | 1,976 |
| Python files | 4,175 |
| Markdown files | 2,820 |
| JSON files | 1,760 |

The SHA-256 was independently checked against the supplied manifest:
`ed3644144583921ac916c803511c08ba8caff72d030f5b1406580b2ff8f85abd`.

The archive is R392-era physical state plus later recovery material. The clean R399 rehydration is
the current authority. Counts from different layers must not be added together.

## The architecture that exists

```text
research rounds, results and negative cases
                 │
                 ▼
Registry455 mechanism-family ontology
                 │
        ┌────────┴────────┐
        ▼                 ▼
  4,000 primitives    96 LCB kernels
        │                 │
        └────────┬────────┘
                 ▼
       69 standalone parent products
       (19 current + 50 retro-built)
                 │
                 ▼
       145 Foundry compositions
                 │
                 ▼
     current V2 authority: 57 executable suites
                 44 distinct families
                 516 tests
```

Important qualifications:

- The latest consolidated LCB source exposes 91 parseable class definitions. Architecture records
  96 kernels. R401 records both facts; it does not invent five classes to make the numbers agree.
- The R398 ZIP contains 53 physical V2 directories. R399's separately recovered late products bring
  the current clean authority to 57 suites / 44 families.
- The 69 parent products are executable standalone mechanisms, not automatically V2 products.
- The 145 Foundry compositions are an inventory of potential/implemented interactions, not 145
  market-ready products. At the R12 accounting point: 22 were promoted through a V2 edge, 35 were
  active inferred constructions, 9 were parent-lineage-only and 79 were dormant. Dormant does not
  mean disproven.
- `POST_R178_SALVAGE_ARCHIVE` is excluded from normal Lab retrieval by the project contract and was
  not used as active scientific history in this evaluation.

## What the methodology really did

The Lab's productive loop, stripped of historical ceremony, is:

1. Find a concrete weakness, frontier or mechanism worth testing.
2. Retrieve relevant mechanisms and prior failures.
3. Specify an interaction at code/operator level, not by theme.
4. Test the composition against the parent or a mechanism-removing comparator.
5. Identify where it works, collapses and fails.
6. Keep it only if the mechanism contributes non-additive value.
7. Regression-test the executable result and record the evidence.

This is a strong experimental method. In particular, removal comparators, collapse regions and
transfer tests prevent attractive but inert compositions from being called inventions. R400's JARB
rejection is a good example: 3/21 candidate wins and 18/21 wins after removing the proposed
mechanism. The correct result was rejection, not promotion.

The method became counterproductive when record-keeping and route enforcement started choosing
what work could happen. Receipts, hashes, stage files and metadata are useful for recovery; they are
not product progress. Bridge, Regime Router and the retired control scaffolding are not part of this
blueprint.

## Re-evaluation from smallest unit to composition

### Mechanism families and primitives

Their highest value is as a search space and a vocabulary for causal/operational ideas. They are not
usable products by themselves. Registry IDs should answer “have we seen this mechanism?” rather
than “are we allowed to work on this problem?”

### LCB kernels

These are the most underused software assets. Examples include shared-capacity allocation,
deep-tail diagnostics, coverage feedback, active threshold sensing, decision-weighted calibration,
multi-fidelity budgeting, solver-certificate audit, decision-sufficient compression,
observability planning and reach-avoid viability. They can shorten new products substantially.

Current limitation: the consolidated source is a library surface, not a packaged SDK. Inputs,
exceptions, dependency expectations and real-data examples are inconsistent. Packaging all kernels
would be another large internal project; package only a kernel when a real product needs it.

### Parent products

The 69 parents are the best immediate product mine because each already owns a coherent operator.
They contain 271 test methods. Their most valuable categories are:

- allocation and planning: ACRA, LCM, CSID, MFPA, CAPL, ENPC;
- decision evaluation: DLEW, MDDC, SCE, DRE, DTTC;
- measurement and causal reliability: OWS, OTE, ACSA, CBAC, SACPS;
- system reduction and resilience: TWMR, TSRC, BRED, HMRM, DTRM;
- domain engines: OFLS, MCRIS, MBPF, MLHPE and market clearing.

Most parents are working algorithmic prototypes. Their tests establish software/mechanism behavior,
not field usefulness. The strongest next move is to wrap individual parents around real inputs,
comparators and decisions—not to combine them immediately.

### Foundry compositions

The 145 compositions are valuable as a hypothesis shelf. Their hidden value is the 79 dormant
interactions: they are unexploited, not negative results. But promotion should remain demand-led. A
composition becomes interesting only when a real workflow needs both operators and their
interaction changes a decision.

### V2 products

The current 57 executable suites / 44 families are the most heavily tested layer (516 tests). They
demonstrate non-additive interactions better than the parent layer. They are nevertheless mostly
synthetic scientific products: the R401 executable/evidence scan found no V2 suite explicitly
claiming real-data evidence in its current product files. This is not a criticism of the mechanisms;
it is the exact boundary of what has been demonstrated.

## Materiality scale

R401 uses four plain labels. They are an evaluation lens, not a new Lab gate.

| Level | Meaning | Lab state |
|---|---|---|
| Kernel | Reusable operator with code/tests | Many |
| Research product | End-to-end mechanism demo on declared examples | Many parents and V2 suites |
| Workflow product | Accepts a user's data and returns an actionable artifact | Rare before R401 |
| Field-validated product | Demonstrated on actual decisions with held-out/operational outcomes | Not established by the inspected evidence |

This is why “57 products” felt like very little in hand: most are at the second level while the user
needs the third and eventually the fourth.

## Highest-leverage product routes

These are grounded in existing operators. Proposed combinations are explicitly proposals, not
claims that the Lab has already validated them.

| Priority | Product route | Existing assets | Concrete output | Present evidence boundary |
|---:|---|---|---|---|
| 1 | Consequence-aware inspection planner | ACRA | Asset-by-asset inspection plan, budget curve, stress changes | Workflow product built in R401; needs field estimates/outcomes |
| 2 | Trigger policy designer | DTTC, optionally SRCD | Threshold, holdout error/cost, candidate ranking, trigger policy | Workflow product built in R401; needs longer prospective evaluation |
| 3 | Decision model evaluation workbench | DLEW + MDDC + SCE | Which model to deploy, regret table, specification curve | Strong standalone pieces; no unified real-data shell yet |
| 4 | Receivables-to-liquidity planner | LCM + OWNM | Financeable claims, channel allocation, verification ROI | LP engine exists; needs actual eligibility/channel adapters |
| 5 | Safeguard portfolio designer | CSID + REL | Minimal controls and tampering-localization plan | Operators exist; control libraries must be domain-specific |
| 6 | Robust model shipper | TWMR + TSRC + BRED | Smaller deployable model with decision-loss/error certificate | Good synthetic reduction results; needs real model adapters |
| 7 | Resilience action planner | MFPA + HMRM + DTRM | Failure routes, transient risk and funded mitigations | Pieces exist; integration must be tested on one system |
| 8 | Experiment assignment/audit kit | ACSA + CBAC + discrepancy randomizer | Assignment, balance certificate, selection audit | Statistically useful pieces; needs data-frame/CSV surface |
| 9 | Portfolio decision kit | ENPC + SACPS + DLEW | Constraints-aware weights and decision-regret report | Finance code exists; requires realistic costs and walk-forward data |
| 10 | Mortgage intervention simulator | MCRIS + MBPF | Treatment scenarios with burnout/prepayment effects | Domain-specific parents exist; needs calibrated portfolio data |

## Latent power that was not fully used

1. **The parents are often more product-ready than the V2s.** A clean operator with an obvious user
   input can produce value faster than a scientifically novel composition.
2. **Negative results are a design asset.** The Lab knows which attractive combinations become
   inert when a mechanism is removed. That can prevent wasted product integration work.
3. **Decision loss is a unifying commercial surface.** DLEW, MDDC, DTTC, ACRA, DRE and several V2s
   can all answer “what changes the action?” This can become a family of workflow tools without
   merging their internals.
4. **Dormant Foundry compositions are best used on demand.** When a workflow exposes a failure in a
   parent product, the dormant shelf can suggest a targeted second mechanism.
5. **The real multiplier is data contact.** One actual inspection table, claims file, model-selection
   dataset or intervention history will teach more about product value than another registry pass.

## Operating blueprint from here

For each material product:

1. Pick one decision a real user already makes.
2. Wrap the smallest existing parent that can improve it.
3. Accept ordinary input (CSV/JSON/API), produce a saved actionable result.
4. Include one naive/current-policy comparator and one honest boundary statement.
5. Run on actual or realistically sourced data.
6. Add another Lab mechanism only when a measured failure calls for it.

Keep: tests, provenance, removal comparisons when composing, failure cases, deterministic examples.

Do not make prerequisites: round ceremonies, route approval, evidence receipts, hash production,
catalog completeness, capability counts or a new autonomous research controller.

## R401 output

`material_products/CONSEQUENCE_AWARE_INSPECTION_PLANNER` is the first direct conversion:

- dependency-free exact discrete optimizer;
- JSON scenario input;
- per-target feasibility and cost/error modifiers;
- cheapest and uniform-policy comparators;
- next useful budget breakpoint and budget curve;
- consequence stress cases;
- JSON and Markdown output;
- eight automated tests plus an executable maintenance example.

It does not modify the canonical R399 product authority. Promotion is unnecessary until actual use
shows whether it deserves a permanent Lab identity.

`material_products/TRIGGER_POLICY_DESIGNER` is the second conversion:

- ordinary CSV history input;
- high-side and low-side trigger candidates;
- missed-event, false-alarm, verification and manipulation-exposure costs;
- chronological calibration/evaluation separation;
- always-trigger and never-trigger comparisons;
- JSON and Markdown policy artifacts;
- six automated tests plus an executable machine-history example.

Its example selects temperature at `>= 76`, commits zero false positives and zero false negatives on
the ten-row holdout, and reduces the declared cost by 80% versus the best always/never baseline.
That is an executable demonstration on constructed data, not a field-performance claim.
