# Unbalanced Movement-Creation Accountant

UMCA is the first standalone product of the retroactive reopening phase. It rescues held candidate
**M-437 (unbalanced transport)** without requiring any connection to the completed 20-composition
queue.

Given source mass, target mass, pairwise movement costs, and explicit creation/destruction costs, it
solves one linear program and reports separately:

- how much mass actually moved and along which routes;
- how much disappeared at each source;
- how much appeared at each target;
- movement, destruction, creation, and total cost;
- exact source and target accounting residuals.

The included comparator rescales source mass until totals match and then runs balanced transport.
That familiar shortcut can make nonexistent source mass look like movement and erase the operational
distinction between relocation and local creation/destruction.

## Run

```powershell
python -m unittest -v test_umca.py
python demo_stock_reconciliation.py
```

## Boundary

v0.1 uses divisible mass and linear costs. Next layers are partial observation, uncertain location,
capacity, time, nonlinear creation/destruction penalties, and integer objects.
