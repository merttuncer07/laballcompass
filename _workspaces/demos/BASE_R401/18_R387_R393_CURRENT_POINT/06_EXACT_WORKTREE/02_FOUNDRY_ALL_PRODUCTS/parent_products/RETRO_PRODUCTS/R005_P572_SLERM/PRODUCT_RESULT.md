# R-005 product result — SLERM v0.1

**Product route:** reconstructed standalone synchronization/energy-transfer monitor  
**Result:** working product; 4/4 tests pass

SLERM reconstructs the fluid–structure lock-in shell from force and displacement time series. It
requires frequency proximity, phase locking, large response, and positive force-times-velocity work
before declaring dangerous energy-transferring lock-in.

In the first 80-second construction, early windows separated 1.5 Hz forcing from a 1.0 Hz response
and remained safe. The later response locked at 1.5 Hz with phase-locking value approximately 1,
response RMS 0.91924, and normalized energy transfer approximately 1. SLERM identified a 30-second
consecutive dangerous episode; a transition window was retained but not overcalled.

The reconstructed shell is independently deployable for structures, cables, rotating equipment,
and coupled fluid systems.
