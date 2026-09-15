# Product Result — UMCA v0.1

**Retro candidate:** R-032 / M-437  
**Historical decision:** held without new IM ID  
**Product:** Unbalanced Movement-Creation Accountant  
**Status:** independent working product

M-437 was previously held because its movement-versus-creation distinction did not yet justify a
new ontology family beyond IM-025/IM-139. That ontology decision did not prevent an independent
product. UMCA now solves the relaxed-conservation accounting problem directly.

In the reproducible two-source/two-target construction:

- source total was **100** and target total was **130**;
- UMCA identified **50 moved**, **50 destroyed**, and **80 created** units;
- movement, destruction, and creation costs were **50**, **60**, and **144**, for total **254**;
- exact source and target accounting residuals were zero;
- a balanced-transport workaround rescaled source mass by **1.3**, silently invented **30** source
  units, labeled all **130** target units as moved, and incurred movement cost **500**.

Four automated tests pass. This is a direct standalone product result; no integration with the
completed 20-composition queue was required.

v0.1 uses divisible mass and linear costs. The next independent construction layer is capacity,
time, nonlinear mass-change penalties, partial observation, and integer objects.

