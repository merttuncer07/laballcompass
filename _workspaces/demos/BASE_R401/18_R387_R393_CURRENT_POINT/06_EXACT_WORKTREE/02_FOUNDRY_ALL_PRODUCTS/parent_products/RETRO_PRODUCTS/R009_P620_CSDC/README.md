# CSDC v0.1 — Curvature-driven Size-Distribution Controller

CSDC reconstructs the LSW critical-radius mechanism for a measured particle/domain population. At
each step, radii below the instantaneous critical radius shrink, larger radii grow, dissolved
material is returned to the surviving population, and total material volume is conserved.

The controller can run to a time limit or stop when a requested mean radius is reached. It reports
the full size distribution, critical radius, dispersity, dissolved count, material error, and stop
time. This makes the historical mechanism usable for heat-treatment, precipitation, emulsion, and
microstructure process planning.

Run `python -m unittest -v test_csdc.py` and `python demo_coarsening.py`.
