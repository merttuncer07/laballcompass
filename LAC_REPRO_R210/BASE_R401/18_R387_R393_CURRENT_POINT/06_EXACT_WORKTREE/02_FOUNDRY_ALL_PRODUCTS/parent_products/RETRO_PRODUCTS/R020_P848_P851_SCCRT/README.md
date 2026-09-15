# SCCRT v0.1 — State-bearing Catalyst Cycle and Regeneration Tracker

SCCRT models a catalyst lattice species as a finite state-bearing reactant. Reaction consumes active
lattice capacity, oxidant restores vacancies, and the material balance is carried through every feed
step. A passive-catalyst counterfactual shows how much output would be invented by assuming the
catalyst never changes state.

The capacity designer evaluates declared oxidant scales and selects the smallest one that respects
minimum and final active-state requirements. This turns the Mars–van Krevelen/vacancy-cycle shell into
a regeneration sizing and feed-schedule product.

Run `python -m unittest -v test_sccrt.py` and `python demo_catalyst.py`.
