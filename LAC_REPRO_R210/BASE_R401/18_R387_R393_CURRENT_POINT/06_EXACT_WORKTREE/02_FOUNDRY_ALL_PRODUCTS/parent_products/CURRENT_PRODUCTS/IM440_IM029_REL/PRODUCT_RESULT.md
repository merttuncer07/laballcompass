# IM-440 → IM-029 product result: Relational Evidence Localizer v0.1

REL converts counterparty-generated records into a consistency graph and uses its violation pattern
to locate one altered record or a coherent altered pair.

## Construction result

The scenario contained buyer order 100, seller invoice 120, warehouse receipt 100, carrier manifest
100, and bank payment 120. The actual altered pair was seller invoice plus bank payment.

With only two conventional relations, the graph was ambiguous. Its top explanation was the buyer
order with posterior 47.49%; the true pair received only 22.56%.

Adding independently generated receipt, carrier, and cross-party relations changed the result:

| Evidence graph | Relations | Top explanation | Posterior |
|---|---:|---|---:|
| Sparse | 2 | buyer order | 47.49% |
| Counterparty-redundant | 7 | seller invoice + bank payment | **97.57%** |

The tool also exposed a structural ambiguity: a pure XOR violation pattern can confuse a culprit set
with its graph complement. REL resolved this by representing justified producer-specific alteration
priors, making independently controlled anchor records explicit rather than silently trusted.

## Working software

- numeric equality/tolerance evidence relations;
- violation-pattern extraction;
- single-record and coherent-pair localization;
- producer-specific alteration priors;
- posterior ranking with predicted violation explanation;
- three automated tests, all passing.

## Next construction layer

Add a graph-design operator that proposes the cheapest new independently generated record or
relation capable of reducing current localization ambiguity. This will turn IM-440's incentive to
create evidence into an explicit mechanism-design output.
