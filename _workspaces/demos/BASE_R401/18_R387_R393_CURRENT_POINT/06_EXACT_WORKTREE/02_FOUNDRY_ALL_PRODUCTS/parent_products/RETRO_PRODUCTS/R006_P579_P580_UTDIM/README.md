# UTDIM v0.1 — Unequal-Transport Double-diffusive Instability Monitor

UTDIM reconstructs the two-scalar transport shell as an explicit linear dynamical system. It scans
spatial wavenumbers, measures the fastest eigenvalue and mode composition, and reruns the identical
system after equalizing diffusivities.

An instability is attributed to transport-rate mismatch only when the combined static gradient is
stable, the measured unequal-rate system grows, and the equal-transport counterfactual does not.
This distinguishes salt-finger/double-diffusive failure from ordinary static instability and turns
the historical idea into a deployable stratification, battery, reactor, geophysical, or process
monitor.

Run `python -m unittest -v test_utdim.py` and `python demo_double_diffusion.py`.
