# PRIU v0.1 — Priority-Reset Investment Unlocker

PRIU inserts a proposed new-money claim at every possible position in an existing absolute-priority
waterfall. Across explicit scenarios it reports:

- whether expected recovery meets the new lender's funding hurdle;
- the least senior position that still unlocks financing;
- each old claimant's recovery before and after funding;
- whether every old claimant is protected relative to no funding;
- incremental enterprise value net of the new capital.

It is a scenario and contract-design calculator, not a prediction of legal approval. It stands alone
and does not require integration with the completed current products.

Run:

```powershell
python -m unittest -v test_priu.py
python demo_priority_reset.py
```
