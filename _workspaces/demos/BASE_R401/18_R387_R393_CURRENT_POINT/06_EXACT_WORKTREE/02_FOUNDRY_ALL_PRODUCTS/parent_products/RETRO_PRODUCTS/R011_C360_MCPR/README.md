# MCPR v0.1 — Marginal Clearing Price and Rent Calculator

MCPR clears divisible supply offers against fixed demand under merit order and a uniform marginal
price. It reports dispatch, utilization, marginal tied blocks, common payment, offered variable cost,
inframarginal rent, and unserved demand. Equal-price marginal offers are prorated; shortage can invoke
an explicit scarcity price.

MCPR is a standalone auction/dispatch scenario product. It does not need integration with the current
composition products.

Run:

```powershell
python -m unittest -v test_mcpr.py
python demo_market_clear.py
```
