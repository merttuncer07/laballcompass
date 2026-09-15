# Product Result — MFPA v0.1

**Composition:** IM-401 → IM-030  
**Product:** Multi-Route Failure-Path Architect  
**Status:** working surrogate product

MFPA allocates a fixed mass budget across sacrificial failure, crack deflection, pull-out, and phase
transformation. It explicitly models activation order: if the resistance accumulated by earlier
routes does not reach a later route's threshold, the advancing crack outruns that mechanism and its
nominal capacity contributes nothing. The chain is replayed under non-common-mode degradation
scenarios.

At equal total mass 1.0:

- the best single route placed all mass in the sacrificial layer and achieved worst-case failure
  energy **1.9237**;
- the robust composition allocated **0.55 / 0.20 / 0.10 / 0.15** across sacrificial, deflection,
  pull-out, and transformation routes;
- all four routes activated in every modeled scenario;
- worst-case failure energy rose to **4.2863**, an absolute gain **2.3626** and relative gain
  **122.82%**;
- failure-family concentration fell from **1.0** to **0.375**.

Three unit tests pass. Construction also caught and fixed a comparison bug that had accidentally
given a supposed single-route design four times the allowed mass.

v0.1 is a transparent architecture surrogate, not specimen or finite-element validation. The live
extension path is calibrated traction/separation laws, geometry/manufacturing constraints, coupled
mechanism interference, uncertainty, and physical coupon data.
