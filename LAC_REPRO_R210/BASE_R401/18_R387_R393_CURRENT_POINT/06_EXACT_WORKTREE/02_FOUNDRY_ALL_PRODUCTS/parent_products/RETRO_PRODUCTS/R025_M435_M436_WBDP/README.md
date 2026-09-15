# WBDP v0.1 — Wasserstein Barycenter and Displacement Planner

WBDP computes exact one-dimensional W2 barycenters and displacement interpolations from discrete
quantile segments. It returns the transported distribution, moments, source Wasserstein distances,
and weighted transport objective. Unlike an ordinary mixture, interpolation moves mass through space.

WBDP is a standalone demand, inventory, geographic allocation, and risk-distribution planning product.
Current-product integration is not required.

Run `python -m unittest -v test_wbdp.py` and `python demo_distribution_plan.py`.
