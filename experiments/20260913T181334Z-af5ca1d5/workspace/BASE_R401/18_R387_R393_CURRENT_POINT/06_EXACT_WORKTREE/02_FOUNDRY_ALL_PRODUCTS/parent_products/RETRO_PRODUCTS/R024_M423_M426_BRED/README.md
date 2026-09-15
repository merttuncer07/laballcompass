# BRED v0.1 — Balanced Reduction Error-budget Designer

BRED balances a stable discrete-time linear model, ranks its observable-controllable directions by
Hankel singular value, and selects the smallest truncation order whose standard `2 × discarded HSV`
error upper bound meets a user budget. It returns the reduced A/B/C/D matrices, every order option,
retained Hankel share, stability, and actual finite-horizon impulse-response errors.

BRED is a standalone model compression and deployment-sizing product. It does not require integration
with current products.

Run:

```powershell
python -m unittest -v test_bred.py
python demo_balanced_reduction.py
```
