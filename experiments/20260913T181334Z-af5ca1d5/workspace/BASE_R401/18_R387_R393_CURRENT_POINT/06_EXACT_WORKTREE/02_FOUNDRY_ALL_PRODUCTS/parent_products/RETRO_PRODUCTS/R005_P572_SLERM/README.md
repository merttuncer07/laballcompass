# SLERM v0.1 — Synchronization Lock-in and Energy-transfer Risk Monitor

SLERM reconstructs the vortex-induced-vibration shell from time-series measurements. In each window
it measures forcing/response frequencies, relative detuning, phase locking, response amplitude, and
actual force-times-velocity energy transfer.

Frequency agreement alone is not labeled dangerous. A window becomes dangerous only when locking,
large response, and positive normalized energy transfer occur together. This makes the historical
synchronization idea an executable structural, rotating-machine, bridge, cable, and fluid-system
monitor rather than an academic classification.

Run `python -m unittest -v test_slerm.py` and `python demo_lock_in.py`.
