# SALC v0.1 — State Aggregation and Lumpability Certificate

SALC tests whether every micro-state in a proposed block sends the same total transition probability
to every target block. Exact compatibility produces a certified smaller Markov chain. When exact
lumpability fails, SALC preserves the approximate model and reports the worst block/state violation,
one-step total-variation error, and maximum multi-step block-distribution error over a chosen horizon.

SALC is a standalone regime, customer-state, reliability, and credit-state aggregation product. It
does not require integration with current products.

Run:

```powershell
python -m unittest -v test_salc.py
python demo_lumpability.py
```
